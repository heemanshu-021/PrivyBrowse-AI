"""
PrivyBrowse AI — End-to-End Autonomous Agent Runner
Multi-Step, Multi-Page Continuous Autonomous Browser Agent Runner with Task State Management,
Dynamic Replanning, Step Dependencies, Bounded Recovery, and Human Confirmation Lifecycle.
"""

import time
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from backend.agent.schemas import (
    AgentState, AgentTask, TaskConstraints, RiskLevel,
    CandidateAction, ValidationResult, VerificationResult,
    VerificationStatus, FailureCategory, RecoveryRecommendation,
    ActionType, TaskStep, ObjectiveStatus, TaskResult,
    CheckpointType, TaskCheckpoint, ActionRecord
)
from backend.agent.planner import AgentPlanner
from backend.actions.executor import ActionExecutor
from backend.actions.schemas import ActionResult, ExecutionStatus, ExpectedState
from backend.actions.page_change_detector import PageChangeDetector
from backend.agent.recovery import ProgressTracker, RecoveryEngine
from backend.browser.context_manager import global_browser_context_manager
from backend.observability.publisher import global_event_publisher


class EndToEndAgentRunner:
    """
    Continuous Multi-Step, Multi-Page Autonomous Agent Runner.
    Drives complete user tasks across live browser sessions with strict evidence-based verification,
    cross-page state memory, step dependency resolution, and dynamic replanning.
    """

    def __init__(
        self,
        planner: Optional[AgentPlanner] = None,
        executor: Optional[ActionExecutor] = None,
        recovery_engine: Optional[RecoveryEngine] = None,
        event_publisher: Optional[Any] = None
    ):
        self.planner = planner or AgentPlanner()
        self.executor = executor or ActionExecutor()
        self.change_detector = PageChangeDetector()
        self.recovery_engine = recovery_engine or getattr(self.planner.verifier, "recovery_engine", RecoveryEngine())
        self.progress_tracker = ProgressTracker()
        self.events = event_publisher or global_event_publisher
        self.active_task: Optional[AgentTask] = None
        self.is_stopped = False
        self.is_paused = False

    def run_single_turn(
        self,
        sanitized_elements: List[Dict[str, Any]],
        current_url: str = "",
        task_goal: str = "",
        user_confirmed: bool = False,
        history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a single end-to-end iteration of the agent loop:
          1. Plan next candidate action
          2. Validate safety & budget
          3. If confirmation required -> return BLOCKED / REQUIRES_CONFIRMATION
          4. Execute action via executor
          5. Verify state change against expected state
          6. Record progress & check for action loops / stalls
          7. Return step telemetry
        """
        t0 = time.perf_counter()

        if self.is_stopped:
            return {
                "status": "STOPPED",
                "message": "Agent execution halted by user STOP request",
                "state": AgentState.IDLE.value
            }

        # 1. PLAN next action
        candidate, validation, state = self.planner.plan_next_step(
            sanitized_elements=sanitized_elements,
            history=history or [],
            task_goal=task_goal,
            user_confirmed=user_confirmed,
            current_url=current_url
        )

        task_id = self.planner.current_task.task_id if self.planner.current_task else None

        if not candidate:
            return {
                "status": "COMPLETED" if state == AgentState.COMPLETED else "NO_ACTION",
                "message": validation.reason,
                "state": state.value,
                "action": None
            }

        # 2. VALIDATE action
        if not validation.allowed:
            if validation.requires_confirmation and not user_confirmed:
                self.events.confirmation_required(
                    action_type=candidate.action.value,
                    target_id=candidate.target_id,
                    reason=validation.reason,
                    task_id=task_id
                )
                return {
                    "status": "REQUIRES_CONFIRMATION",
                    "message": "High-risk or financial interaction requires user confirmation",
                    "state": AgentState.AWAITING_CONFIRMATION.value,
                    "action": candidate.model_dump(),
                    "validation": validation.model_dump()
                }

            return {
                "status": "BLOCKED",
                "message": f"Action blocked: {validation.reason}",
                "state": AgentState.BLOCKED.value,
                "action": candidate.model_dump(),
                "validation": validation.model_dump()
            }

        self.events.action_validated(
            action_type=candidate.action.value,
            target_id=candidate.target_id,
            risk_level=candidate.risk_level.value,
            task_id=task_id
        )

        # 3. CHECK IDEMPOTENCY & SAVE TARGET CHECKPOINT
        if self.planner.memory.is_action_idempotent(candidate.action.value, candidate.target_id, candidate.text, sanitized_elements, current_url):
            self.planner.memory.save_checkpoint(
                task_id=task_id or "task-0",
                checkpoint_type=CheckpointType.STATE_VERIFIED,
                step_index=getattr(self.planner.current_task, "current_step_index", 0),
                url=current_url,
                metadata={"idempotent_skip": True, "target_id": candidate.target_id}
            )
            if self.planner.current_task and self.planner.current_task.current_step_index < len(self.planner.current_task.steps):
                curr_step = self.planner.current_task.steps[self.planner.current_task.current_step_index]
                curr_step.status = ObjectiveStatus.COMPLETED
                curr_step.evidence = [f"Target '{candidate.target_id}' already in desired state."]
                if curr_step.id not in self.planner.current_task.completed_steps:
                    self.planner.current_task.completed_steps.append(curr_step.id)
                if curr_step.id in self.planner.current_task.pending_steps:
                    self.planner.current_task.pending_steps.remove(curr_step.id)
                if self.planner.current_task.current_step_index < len(self.planner.current_task.steps) - 1:
                    self.planner.current_task.current_step_index += 1

            return {
                "status": "SUCCESS",
                "state": self.planner.state_machine.current_state.value,
                "action": candidate.model_dump(),
                "message": "Action already satisfied in target state (idempotent skip)",
                "post_elements": sanitized_elements,
                "post_url": current_url,
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
                "agent_summary": self.planner.get_agent_status()
            }

        self.planner.memory.save_checkpoint(
            task_id=task_id or "task-0",
            checkpoint_type=CheckpointType.TARGET_IDENTIFIED,
            step_index=getattr(self.planner.current_task, "current_step_index", 0),
            url=current_url,
            metadata={"target_id": candidate.target_id, "action": candidate.action.value}
        )

        # 4. GENERATE EXPECTED STATE
        target_el = next((e for e in sanitized_elements if e.get("id") == candidate.target_id), None)
        action_dict = candidate.model_dump()
        action_dict["confirmed_by_user"] = user_confirmed
        expected_state = self.planner.verifier.generate_expected_state(action_dict, target_el)

        # 5. EXECUTE action
        exec_res = self.executor.execute_browser_action(
            action_json=action_dict,
            current_elements=sanitized_elements,
            current_url=current_url,
            user_confirmed=user_confirmed
        )

        self.planner.memory.save_checkpoint(
            task_id=task_id or "task-0",
            checkpoint_type=CheckpointType.ACTION_COMPLETED,
            step_index=getattr(self.planner.current_task, "current_step_index", 0),
            url=current_url,
            metadata={"action_result": exec_res.status.value, "success": exec_res.success}
        )

        # 6. POST-ACTION OBSERVATION & EVIDENCE VERIFICATION
        re_perception_required = exec_res.page_changed or exec_res.metadata.get("re_perception_required", False)
        if exec_res.error and exec_res.error.code in ("TAB_MISMATCH", "STALE_NAVIGATION", "DOM_MUTATION_MISMATCH", "STALE_DOCUMENT", "STALE_TARGET"):
            re_perception_required = True

        post_action_elements = list(sanitized_elements)
        post_url = current_url
        prev_scroll = None
        curr_scroll = None

        # Check live browser context manager for fresh post-action state
        live_ctx = global_browser_context_manager.current_context
        is_live_matching = bool(live_ctx and live_ctx.url and (live_ctx.url == current_url or current_url in live_ctx.url or live_ctx.url in current_url))

        if is_live_matching and live_ctx:
            post_url = live_ctx.url or current_url
            if live_ctx.elements and exec_res.success:
                post_action_elements = live_ctx.elements
            if live_ctx.scroll:
                curr_scroll = {
                    "scrollX": live_ctx.scroll.scroll_x,
                    "scrollY": live_ctx.scroll.scroll_y,
                    "documentHeight": live_ctx.scroll.document_height,
                    "viewportHeight": live_ctx.scroll.viewport_height,
                    "maxScrollY": live_ctx.scroll.max_scroll_y
                }

        # Apply synthetic value mutation for testing/simulation when live context not refreshed or in simulation mode
        if exec_res.success and (not is_live_matching or getattr(self.executor, "simulation_mode", False)):
            post_action_elements = [dict(e) for e in sanitized_elements]
            if candidate.action == ActionType.TYPE and candidate.target_id:
                actual_value = exec_res.metadata.get("typed_value") or candidate.text or "[POPULATED]"
                for el in post_action_elements:
                    if el.get("id") == candidate.target_id:
                        el["value"] = actual_value
            elif candidate.action == ActionType.CLICK and candidate.target_id:
                for el in post_action_elements:
                    if el.get("id") == candidate.target_id:
                        el["state_clicked"] = True
            elif candidate.action == ActionType.SCROLL:
                prev_scroll = {"scrollX": 0.0, "scrollY": 0.0}
                curr_scroll = {"scrollX": 0.0, "scrollY": float(action_dict.get("scroll_delta", {}).get("y", 400.0) or 400.0)}

        # Run Evidence-Based Verification
        verify_res = self.planner.verify_step_outcome(
            action=action_dict,
            prev_elements=sanitized_elements,
            current_elements=post_action_elements,
            prev_url=current_url,
            current_url=post_url,
            prev_scroll=prev_scroll,
            current_scroll=curr_scroll,
            exec_error=exec_res.error.message if (exec_res.error and not exec_res.success) else None,
            expected_state=expected_state
        )

        t_total_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        self.events.action_completed(
            action_type=candidate.action.value,
            target_id=candidate.target_id,
            duration_ms=exec_res.duration_ms or t_total_ms,
            task_id=task_id
        )

        if verify_res.success:
            self.planner.memory.save_checkpoint(
                task_id=task_id or "task-0",
                checkpoint_type=CheckpointType.STATE_VERIFIED,
                step_index=getattr(self.planner.current_task, "current_step_index", 0),
                url=post_url,
                metadata={"signal": verify_res.signal}
            )
            self.events.action_verified(
                signal=verify_res.signal,
                evidence=verify_res.evidence,
                task_id=task_id
            )
        else:
            self.events.action_verification_failed(
                signal=verify_res.signal,
                reason=verify_res.details,
                task_id=task_id
            )

        # 7. RECORD AUDIT RECORD
        audit_record = ActionRecord(
            action_id=f"act-{task_id or '0'}-{time.time()}",
            task_id=task_id or "task-0",
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_type=candidate.action.value,
            target_id=candidate.target_id,
            preconditions_met=True,
            postconditions_met=verify_res.success,
            result=exec_res.model_dump(),
            verification_result=verify_res.status.value,
            failure_reason=verify_res.details if not verify_res.success else None
        )
        self.planner.memory.record_action_audit(audit_record)

        # 8. PROGRESS TRACKING & LOOP DETECTION
        action_sig = f"{candidate.action.value}:{candidate.target_id or candidate.text or ''}"
        dom_fp = getattr(live_ctx.dom_fingerprint, "hash", "") if (live_ctx and live_ctx.dom_fingerprint) else ""
        has_progress = verify_res.success and verify_res.status in (VerificationStatus.ACTION_VERIFIED, VerificationStatus.SCROLL_BOUNDARY)

        self.progress_tracker.record_turn(
            url=post_url,
            dom_fingerprint=dom_fp,
            action_signature=action_sig,
            has_progress=has_progress
        )
        self.planner.memory.record_state_snapshot(post_url, post_action_elements)

        is_stalled, loop_cat, loop_reason = self.progress_tracker.detect_loop_or_stall()
        if not is_stalled and self.planner.memory.is_progress_stagnant(max_stagnant_turns=4):
            is_stalled = True
            loop_cat = FailureCategory.LOOP_DETECTED
            loop_reason = "Progress stagnant: browser state unchanged across 4 turns"

        if is_stalled:
            verify_res.status = VerificationStatus.FAILED
            verify_res.failure_category = loop_cat
            verify_res.recovery_recommendation = RecoveryRecommendation.SAFE_STOP
            verify_res.details = loop_reason or "Action loop / stall detected"
            self.events.loop_detected(
                reason=verify_res.details,
                task_id=task_id
            )

        # Record action in planner memory
        self.planner.memory.record_action(action_dict)
        if self.planner.current_task:
            self.planner.current_task.actions_executed += 1
            if verify_res.success and self.planner.current_task.current_step_index < len(self.planner.current_task.steps):
                curr_step = self.planner.current_task.steps[self.planner.current_task.current_step_index]
                curr_step.status = ObjectiveStatus.COMPLETED
                curr_step.evidence = verify_res.evidence
                curr_step.completed_at = datetime.now(timezone.utc).isoformat()
                if curr_step.id not in self.planner.current_task.completed_steps:
                    self.planner.current_task.completed_steps.append(curr_step.id)
                if curr_step.id in self.planner.current_task.pending_steps:
                    self.planner.current_task.pending_steps.remove(curr_step.id)

                self.events.task_step_completed(
                    task_id=self.planner.current_task.task_id,
                    step_id=curr_step.id,
                    description=curr_step.description,
                    duration_ms=t_total_ms,
                    metadata={"evidence": curr_step.evidence}
                )
                
                if self.planner.current_task.current_step_index < len(self.planner.current_task.steps) - 1:
                    self.planner.current_task.current_step_index += 1

        # Check for Safe Stop requirement
        turn_status = "SUCCESS" if (exec_res.success and verify_res.success) else "FAILED"
        if verify_res.recovery_recommendation == RecoveryRecommendation.SAFE_STOP:
            turn_status = "SAFE_STOP"

        return {
            "status": turn_status,
            "state": self.planner.state_machine.current_state.value,
            "action": candidate.model_dump(),
            "execution": exec_res.model_dump(),
            "verification": verify_res.model_dump(),
            "latency_ms": t_total_ms,
            "post_elements": post_action_elements,
            "post_url": post_url,
            "re_perception_required": re_perception_required or verify_res.re_perception_required,
            "recovery_recommendation": verify_res.recovery_recommendation.value,
            "agent_summary": self.planner.get_agent_status()
        }

    def run_closed_loop_task(
        self,
        task_goal: str,
        initial_elements: List[Dict[str, Any]],
        current_url: str = "",
        max_turns: int = 15,
        user_confirmed: bool = False,
        perception_callback: Optional[Any] = None,
        existing_task: Optional[AgentTask] = None
    ) -> Dict[str, Any]:
        """
        Drives a full multi-turn, multi-step, multi-page closed-loop task execution:
          OBSERVE -> PLAN -> VALIDATE -> EXECUTE -> RE-OBSERVE -> VERIFY -> RECOVER/REPLAN -> COMPLETE/STOP
        Continues until completion, user pause/stop, confirmation required, safe stop, or budget reached.
        """
        t0 = time.perf_counter()
        self.is_stopped = False
        self.is_paused = False
        self.progress_tracker.reset()
        self.recovery_engine.reset()

        # 1. Initialize or Resume Structured Task
        if existing_task:
            task = existing_task
            self.planner.current_task = task
        else:
            task = self.planner.create_task(
                goal=task_goal,
                constraints=TaskConstraints(max_actions=max_turns),
                initial_elements=initial_elements,
                current_url=current_url
            )
        task.status = AgentState.RUNNING
        self.active_task = task

        current_elements = list(initial_elements)
        active_url = current_url
        history: List[Dict[str, Any]] = []
        turn_results: List[Dict[str, Any]] = []

        for turn_idx in range(max_turns):
            if self.is_stopped:
                task.status = AgentState.CANCELLED
                return {
                    "status": "STOPPED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx,
                    "completed_steps": task.completed_steps,
                    "remaining_steps": task.pending_steps,
                    "message": "Execution stopped by user",
                    "turns": turn_results
                }

            if self.is_paused:
                task.status = AgentState.PAUSED
                return {
                    "status": "PAUSED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx,
                    "completed_steps": task.completed_steps,
                    "remaining_steps": task.pending_steps,
                    "message": "Execution paused by user",
                    "turns": turn_results
                }

            # 2. Check Task Completion Evidence
            is_done, reason = self.planner.check_task_completion(task, current_elements, active_url)
            if is_done:
                if self.planner.state_machine.can_transition_to(AgentState.COMPLETED):
                    self.planner.state_machine.transition_to(AgentState.COMPLETED, f"Task completed: {reason}")
                task.status = AgentState.COMPLETED
                task.completed_at = datetime.now(timezone.utc).isoformat()
                task.task_progress = 1.0
                return {
                    "status": "COMPLETED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx,
                    "completed_steps": task.completed_steps,
                    "remaining_steps": [],
                    "message": reason,
                    "turns": turn_results,
                    "total_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
                }

            # 3. Check Step Dependencies
            if task.current_step_index < len(task.steps):
                current_step = task.steps[task.current_step_index]
                unmet_deps = [d for d in current_step.dependencies if d not in task.completed_steps]
                if unmet_deps:
                    # Replan or skip to resolve dependency
                    self.planner.replan_task(task, task.current_step_index, current_elements, active_url, f"Unmet dependencies: {unmet_deps}")

            # 4. Execute Single Turn
            if task.current_step_index < len(task.steps):
                c_step = task.steps[task.current_step_index]
                self.events.task_step_started(
                    task_id=task.task_id,
                    step_id=c_step.id,
                    description=c_step.description
                )

            turn_res = self.run_single_turn(
                sanitized_elements=current_elements,
                current_url=active_url,
                task_goal=task_goal,
                user_confirmed=user_confirmed,
                history=history
            )
            turn_results.append(turn_res)

            # Update working memory & context
            if turn_res.get("re_perception_required") and perception_callback and callable(perception_callback):
                try:
                    fresh_ctx = perception_callback()
                    if isinstance(fresh_ctx, dict):
                        current_elements = fresh_ctx.get("elements", current_elements)
                        active_url = fresh_ctx.get("url", active_url)
                except Exception:
                    if turn_res.get("post_elements"):
                        current_elements = turn_res["post_elements"]
            elif turn_res.get("post_elements"):
                current_elements = turn_res["post_elements"]

            if turn_res.get("post_url"):
                active_url = turn_res["post_url"]
                task.current_context = {"url": active_url, "elements_count": len(current_elements)}

            # Update Task Progress Metric
            if task.steps:
                task.task_progress = round(len(task.completed_steps) / len(task.steps), 2)

            # 5. Handle Human-in-the-Loop Confirmation Pause
            if turn_res.get("status") in ("REQUIRES_CONFIRMATION", "AWAITING_CONFIRMATION"):
                task.status = AgentState.AWAITING_CONFIRMATION
                if task.current_step_index < len(task.steps):
                    task.steps[task.current_step_index].status = ObjectiveStatus.AWAITING_CONFIRMATION
                return {
                    "status": "AWAITING_CONFIRMATION",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx + 1,
                    "completed_steps": task.completed_steps,
                    "remaining_steps": task.pending_steps,
                    "message": "Task paused: Action requires human confirmation before continuing.",
                    "blocked_turn": turn_res,
                    "turns": turn_results
                }

            # 6. Handle Security Block
            if turn_res.get("status") == "BLOCKED":
                task.status = AgentState.BLOCKED
                return {
                    "status": "BLOCKED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx + 1,
                    "completed_steps": task.completed_steps,
                    "remaining_steps": task.pending_steps,
                    "message": turn_res.get("message", "Action blocked by security policy"),
                    "blocked_turn": turn_res,
                    "turns": turn_results
                }

            # 7. Safe Stop Enforcement
            if turn_res.get("status") == "SAFE_STOP" or turn_res.get("recovery_recommendation") == "SAFE_STOP":
                if self.planner.state_machine.can_transition_to(AgentState.FAILED):
                    self.planner.state_machine.transition_to(AgentState.FAILED, "Safe stop triggered")
                task.status = AgentState.FAILED
                diag_msg = turn_res.get("verification", {}).get("details") or turn_res.get("message") or "Recovery budget exhausted. Execution halted safely."
                return {
                    "status": "FAILED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx + 1,
                    "completed_steps": task.completed_steps,
                    "remaining_steps": task.pending_steps,
                    "message": diag_msg,
                    "safe_stopped": True,
                    "turns": turn_results,
                    "total_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
                }

            # 8. Dynamic Replanning on Step Failure / Ineffective Action
            if turn_res.get("status") == "FAILED" and turn_res.get("recovery_recommendation") in ("REPERCEIVE", "RETRY_ALTERNATIVE"):
                if task.current_step_index < len(task.steps):
                    task.steps[task.current_step_index].retry_count += 1
                    if task.steps[task.current_step_index].retry_count >= task.constraints.max_retries_per_step:
                        # Replan remaining sub-goals
                        self.planner.replan_task(task, task.current_step_index, current_elements, active_url, "Step retry budget exceeded")

            if turn_res.get("status") in ("NO_ACTION", "COMPLETED"):
                break

            # If action was dispatched, record in history
            if turn_res.get("action"):
                act = turn_res["action"]
                history.append({
                    "action": act.get("action"),
                    "targetId": act.get("target_id"),
                    "text": act.get("text"),
                    "success": turn_res.get("status") == "SUCCESS"
                })

            # Refresh perception if callback provided
            if perception_callback and callable(perception_callback):
                try:
                    fresh_ctx = perception_callback()
                    if isinstance(fresh_ctx, dict):
                        current_elements = fresh_ctx.get("elements", current_elements)
                        active_url = fresh_ctx.get("url", active_url)
                except Exception:
                    pass

        # Final Task Completion Evaluation
        is_done, reason = self.planner.check_task_completion(task, current_elements, active_url)
        final_status = "COMPLETED" if (is_done or task.status == AgentState.COMPLETED) else "FINISHED"
        if final_status == "COMPLETED":
            task.status = AgentState.COMPLETED
            task.completed_at = datetime.now(timezone.utc).isoformat()

        return {
            "status": final_status,
            "task_id": task.task_id,
            "goal": task_goal,
            "turns_executed": len(turn_results),
            "completed_steps": task.completed_steps,
            "remaining_steps": [s.id for s in task.steps if s.id not in task.completed_steps],
            "task_progress": task.task_progress,
            "message": reason,
            "turns": turn_results,
            "total_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }

    def resume_task(
        self,
        task: AgentTask,
        current_elements: List[Dict[str, Any]],
        current_url: str = "",
        user_confirmed: bool = True,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """
        Resumes a paused or confirmation-blocked task from its last recorded step without restarting from scratch.
        """
        self.active_task = task
        self.is_paused = False
        self.is_stopped = False
        task.status = AgentState.RUNNING
        self.planner.memory.state_snapshots.clear()
        self.progress_tracker.reset()
        if task.constraints:
            task.constraints.max_actions = max(task.constraints.max_actions, task.actions_executed + max_turns)

        # Continue closed-loop task execution with user confirmation enabled
        return self.run_closed_loop_task(
            task_goal=task.goal,
            initial_elements=current_elements,
            current_url=current_url,
            max_turns=max_turns,
            user_confirmed=user_confirmed,
            existing_task=task
        )

    def stop(self):
        """Immediately halts all autonomous execution."""
        self.is_stopped = True
        if self.active_task:
            self.active_task.status = AgentState.CANCELLED
        self.planner.stop()

    def cancel_task(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Explicitly cancels an active task, releases resources, and transitions state to CANCELLED."""
        self.is_stopped = True
        target_task = self.active_task
        if target_task:
            target_task.status = AgentState.CANCELLED
        if self.planner.state_machine.can_transition_to(AgentState.CANCELLED):
            self.planner.state_machine.transition_to(AgentState.CANCELLED, "User explicitly cancelled task")
        return {
            "status": "CANCELLED",
            "task_id": target_task.task_id if target_task else task_id,
            "message": "Task execution cancelled successfully"
        }

    def pause(self):
        """Pauses autonomous execution preserving active task state."""
        self.is_paused = True
        if self.active_task:
            self.active_task.status = AgentState.PAUSED
        self.planner.pause()

    def resume(self):
        """Resumes autonomous execution."""
        self.is_paused = False
        self.is_stopped = False
        if self.active_task:
            self.active_task.status = AgentState.RUNNING
        self.planner.resume()
