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

        # 4. VERIFY outcome
        # Simulate / evaluate post-action elements
        simulated_next_elements = [dict(e) for e in sanitized_elements]
        if candidate.action == "TYPE" and candidate.target_id:
            for el in simulated_next_elements:
                if el.get("id") == candidate.target_id:
                    el["value"] = candidate.text or "[POPULATED]"

        verify_res = self.planner.verify_step_outcome(
            action=action_dict,
            prev_elements=sanitized_elements,
            current_elements=simulated_next_elements,
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
            "agent_summary": self.planner.get_agent_status()
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
