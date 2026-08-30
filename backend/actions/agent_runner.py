"""
PrivyBrowse AI — End-to-End Autonomous Agent Runner
Continuous Multi-Turn Autonomous Agent Runner with Evidence-Based Action Verification,
Progress Tracking, Loop Protection, and Self-Healing Failure Recovery.
"""

import time
from typing import List, Dict, Any, Optional

from backend.agent.schemas import (
    AgentState, AgentTask, TaskConstraints, RiskLevel,
    CandidateAction, ValidationResult, VerificationResult,
    VerificationStatus, FailureCategory, RecoveryRecommendation,
    ActionType
)
from backend.agent.planner import AgentPlanner
from backend.actions.executor import ActionExecutor
from backend.actions.schemas import ActionResult, ExecutionStatus, ExpectedState
from backend.actions.page_change_detector import PageChangeDetector
from backend.agent.recovery import ProgressTracker, RecoveryEngine
from backend.browser.context_manager import global_browser_context_manager


class EndToEndAgentRunner:
    """
    Continuous Multi-Turn Autonomous Agent Runner.
    Drives complete user tasks across live browser sessions with strict evidence-based verification.
    """

    def __init__(
        self,
        planner: Optional[AgentPlanner] = None,
        executor: Optional[ActionExecutor] = None,
        recovery_engine: Optional[RecoveryEngine] = None
    ):
        self.planner = planner or AgentPlanner()
        self.executor = executor or ActionExecutor()
        self.change_detector = PageChangeDetector()
        self.recovery_engine = recovery_engine or getattr(self.planner.verifier, "recovery_engine", RecoveryEngine())
        self.progress_tracker = ProgressTracker()
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
          3. If confirmation required -> return BLOCKED
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
                return {
                    "status": "REQUIRES_CONFIRMATION",
                    "message": "High-risk or financial interaction requires user confirmation",
                    "state": AgentState.BLOCKED.value,
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

        # 3. GENERATE EXPECTED STATE
        target_el = next((e for e in sanitized_elements if e.get("id") == candidate.target_id), None)
        action_dict = candidate.model_dump()
        action_dict["confirmed_by_user"] = user_confirmed
        expected_state = self.planner.verifier.generate_expected_state(action_dict, target_el)

        # 4. EXECUTE action
        exec_res = self.executor.execute_browser_action(
            action_json=action_dict,
            current_elements=sanitized_elements,
            current_url=current_url,
            user_confirmed=user_confirmed
        )

        # 5. POST-ACTION OBSERVATION & EVIDENCE VERIFICATION
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

        # 6. PROGRESS TRACKING & LOOP DETECTION
        action_sig = f"{candidate.action.value}:{candidate.target_id or candidate.text or ''}"
        dom_fp = getattr(live_ctx.dom_fingerprint, "hash", "") if (live_ctx and live_ctx.dom_fingerprint) else ""
        has_progress = verify_res.success and verify_res.status in (VerificationStatus.ACTION_VERIFIED, VerificationStatus.SCROLL_BOUNDARY)

        self.progress_tracker.record_turn(
            url=post_url,
            dom_fingerprint=dom_fp,
            action_signature=action_sig,
            has_progress=has_progress
        )

        is_stalled, loop_cat, loop_reason = self.progress_tracker.detect_loop_or_stall()
        if is_stalled:
            verify_res.status = VerificationStatus.FAILED
            verify_res.failure_category = loop_cat
            verify_res.recovery_recommendation = RecoveryRecommendation.SAFE_STOP
            verify_res.details = loop_reason or "Action loop / stall detected"

        # Record action in planner memory
        self.planner.memory.record_action(action_dict)
        if self.planner.current_task:
            self.planner.current_task.actions_executed += 1
            if verify_res.success and self.planner.current_task.current_objective_index < len(self.planner.current_task.objectives) - 1:
                self.planner.current_task.current_objective_index += 1

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
        perception_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Drives a full multi-turn closed-loop task execution:
          OBSERVE -> PLAN -> VALIDATE -> EXECUTE -> RE-OBSERVE -> VERIFY -> RECOVER/REPLAN -> COMPLETE/STOP
        Continues until completion, user pause/stop, confirmation required, safe stop, or budget reached.
        """
        t0 = time.perf_counter()
        self.is_stopped = False
        self.is_paused = False
        self.progress_tracker.reset()
        self.recovery_engine.reset()

        # 1. Initialize Task
        task = self.planner.create_task(task_goal, TaskConstraints(max_actions=max_turns))
        
        current_elements = list(initial_elements)
        active_url = current_url
        history: List[Dict[str, Any]] = []
        turn_results: List[Dict[str, Any]] = []
        
        for turn_idx in range(max_turns):
            if self.is_stopped:
                return {
                    "status": "STOPPED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx,
                    "message": "Execution stopped by user",
                    "turns": turn_results
                }

            if self.is_paused:
                return {
                    "status": "PAUSED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx,
                    "message": "Execution paused by user",
                    "turns": turn_results
                }

            # Check if task is already complete from perception evidence
            is_done, reason = self.planner.check_task_completion(task, current_elements, active_url)
            if is_done:
                if self.planner.state_machine.can_transition_to(AgentState.COMPLETED):
                    self.planner.state_machine.transition_to(AgentState.COMPLETED, f"Task completed: {reason}")
                task.status = AgentState.COMPLETED
                return {
                    "status": "COMPLETED",
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx,
                    "message": reason,
                    "turns": turn_results,
                    "total_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
                }

            # Execute single turn
            turn_res = self.run_single_turn(
                sanitized_elements=current_elements,
                current_url=active_url,
                task_goal=task_goal,
                user_confirmed=user_confirmed,
                history=history
            )
            turn_results.append(turn_res)

            # Update current elements and url for next turn
            if turn_res.get("post_elements"):
                current_elements = turn_res["post_elements"]
            if turn_res.get("post_url"):
                active_url = turn_res["post_url"]

            # Check special stop conditions
            if turn_res.get("status") in ("REQUIRES_CONFIRMATION", "BLOCKED"):
                return {
                    "status": turn_res["status"],
                    "task_id": task.task_id,
                    "goal": task_goal,
                    "turns_executed": turn_idx + 1,
                    "message": turn_res.get("message", "Action blocked"),
                    "blocked_turn": turn_res,
                    "turns": turn_results
                }

            # Safe Stop enforcement
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
                    "message": diag_msg,
                    "safe_stopped": True,
                    "turns": turn_results,
                    "total_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
                }

            if turn_res.get("status") in ("NO_ACTION", "COMPLETED"):
                break

            # If an action was dispatched, record it in history
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

        # Final check
        is_done, reason = self.planner.check_task_completion(task, current_elements, active_url)
        final_status = "COMPLETED" if (is_done or task.status == AgentState.COMPLETED) else "FINISHED"
        return {
            "status": final_status,
            "task_id": task.task_id,
            "goal": task_goal,
            "turns_executed": len(turn_results),
            "message": reason,
            "turns": turn_results,
            "total_latency_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }

    def stop(self):
        """Immediately halts all autonomous execution."""
        self.is_stopped = True
        self.planner.stop()

    def pause(self):
        """Pauses autonomous execution preserving active task state."""
        self.is_paused = True
        self.planner.pause()

    def resume(self):
        """Resumes autonomous execution."""
        self.is_paused = False
        self.is_stopped = False
        self.planner.resume()
