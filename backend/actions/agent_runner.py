"""
PrivyBrowse AI — End-to-End Autonomous Agent Runner
Orchestrates the continuous multi-turn autonomous perception-action loop:
  OBSERVE → PERCEIVE → SANITIZE → PLAN → VALIDATE → EXECUTE → VERIFY → RE-PERCEIVE
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from backend.agent.schemas import (
    AgentState, AgentTask, TaskConstraints, RiskLevel,
    CandidateAction, ValidationResult, VerificationResult
)
from backend.agent.planner import AgentPlanner
from backend.actions.executor import ActionExecutor
from backend.actions.schemas import ActionResult, ExecutionStatus
from backend.actions.page_change_detector import PageChangeDetector


class EndToEndAgentRunner:
    """
    Continuous Multi-Turn Autonomous Agent Runner.
    Drives complete user tasks across live browser sessions.
    """

    def __init__(
        self,
        planner: Optional[AgentPlanner] = None,
        executor: Optional[ActionExecutor] = None
    ):
        self.planner = planner or AgentPlanner()
        self.executor = executor or ActionExecutor()
        self.change_detector = PageChangeDetector()
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
          5. Verify state change
          6. Return step telemetry
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
            user_confirmed=user_confirmed
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

        # 3. EXECUTE action
        action_dict = candidate.model_dump()
        action_dict["confirmed_by_user"] = user_confirmed
        exec_res = self.executor.execute_browser_action(
            action_json=action_dict,
            current_elements=sanitized_elements,
            current_url=current_url,
            user_confirmed=user_confirmed
        )

        # 4. VERIFY outcome using real execution result
        re_perception_required = exec_res.page_changed or exec_res.metadata.get("re_perception_required", False)
        if exec_res.error and exec_res.error.code in ("TAB_MISMATCH", "STALE_NAVIGATION", "DOM_MUTATION_MISMATCH", "STALE_DOCUMENT", "STALE_TARGET"):
            re_perception_required = True

        post_action_elements = list(sanitized_elements)
        if exec_res.success and candidate.action == "TYPE" and candidate.target_id:
            # Reflect the typed value from the real execution result for verification
            post_action_elements = [dict(e) for e in sanitized_elements]
            actual_value = exec_res.metadata.get("typed_value") or candidate.text or "[POPULATED]"
            for el in post_action_elements:
                if el.get("id") == candidate.target_id:
                    el["value"] = actual_value

        verify_res = self.planner.verify_step_outcome(
            action=action_dict,
            prev_elements=sanitized_elements,
            current_elements=post_action_elements,
            prev_url=current_url,
            current_url=current_url
        )

        t_total_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        # Record action in planner memory
        self.planner.memory.record_action(action_dict)
        if self.planner.current_task:
            self.planner.current_task.actions_executed += 1
            if self.planner.current_task.current_objective_index < len(self.planner.current_task.objectives) - 1:
                self.planner.current_task.current_objective_index += 1

        return {
            "status": "SUCCESS" if exec_res.success else "FAILED",
            "state": self.planner.state_machine.current_state.value,
            "action": candidate.model_dump(),
            "execution": exec_res.model_dump(),
            "verification": verify_res.model_dump(),
            "latency_ms": t_total_ms,
            "re_perception_required": re_perception_required,
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
          OBSERVE -> PLAN -> VALIDATE -> EXECUTE -> RE-OBSERVE -> VERIFY -> REPLAN
        Continues until completion, user pause/stop, confirmation required, or budget reached.
        """
        t0 = time.perf_counter()
        self.is_stopped = False
        self.is_paused = False

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
        return {
            "status": "COMPLETED" if (is_done or task.status == AgentState.COMPLETED) else "FINISHED",
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

