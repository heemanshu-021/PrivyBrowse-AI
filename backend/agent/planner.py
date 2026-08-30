"""
PrivyBrowse AI — Agent Planning & Decision Engine Orchestrator
Master orchestrator executing the PERCEIVE → UNDERSTAND → PLAN → VALIDATE → ACT → VERIFY loop.
Operates on-device with zero-leak privacy enforcement and transparent action scoring.
"""

import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from backend.agent.schemas import (
    AgentState, ActionType, Objective, ObjectiveStatus,
    CandidateAction, ValidationResult, VerificationResult,
    PlanTraceEntry, AgentTask, TaskConstraints, RiskLevel
)
from backend.agent.state_machine import AgentStateMachine
from backend.agent.decomposer import GoalDecomposer
from backend.agent.engine import LocalRuleBasedEngine
from backend.agent.validator import ActionValidator
from backend.agent.verifier import ActionVerifier
from backend.agent.memory import AgentMemory


class AgentPlanner:
    """
    Main Browser Agent Planner.
    Coordinates State Machine, Goal Decomposition, Candidate Generation, Scoring, and Validation.
    """

    def __init__(self, min_confidence: float = 0.50):
        self.state_machine = AgentStateMachine()
        self.decomposer = GoalDecomposer()
        self.engine = LocalRuleBasedEngine()
        self.validator = ActionValidator(min_confidence=min_confidence)
        self.verifier = ActionVerifier()
        self.memory = AgentMemory()

        self.current_task: Optional[AgentTask] = None
        self.metrics = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "actions_planned": 0,
            "actions_validated": 0,
            "actions_blocked": 0,
            "last_planning_latency_ms": 0.0,
            "last_validation_latency_ms": 0.0,
            "total_agent_cycle_ms": 0.0
        }

    def create_task(
        self,
        goal: str,
        constraints: Optional[TaskConstraints] = None
    ) -> AgentTask:
        """Creates a new structured AgentTask and decomposes it into sub-objectives."""
        self.state_machine.reset()
        self.memory.clear()

        objectives = self.decomposer.decompose(goal)
        task_id = f"task-{int(time.time()*1000)%10000:04d}"

        task = AgentTask(
            task_id=task_id,
            goal=goal,
            status=AgentState.IDLE,
            created_at=datetime.now(timezone.utc).isoformat(),
            constraints=constraints or TaskConstraints(),
            objectives=objectives,
            current_objective_index=0
        )

        self.current_task = task
        self.metrics["tasks_created"] += 1
        return task

    def check_task_completion(
        self,
        task: Optional[AgentTask] = None,
        sanitized_elements: List[Dict[str, Any]] = None,
        current_url: str = ""
    ) -> Tuple[bool, str]:
        """
        Evaluates whether the active task has reached its completion criteria.
        Checks objective progression, semantic evidence in perception, and URL destination.
        """
        active_task = task or self.current_task
        if not active_task:
            return False, "NO_ACTIVE_TASK"

        # 1. Check if all objectives were completed
        if active_task.current_objective_index >= len(active_task.objectives):
            return True, "ALL_OBJECTIVES_COMPLETED"

        # 2. Check semantic evidence in perception
        elements = sanitized_elements or []
        page_text = " ".join(
            f"{e.get('text', '')} {e.get('label', '')} {e.get('attributes', {}).get('placeholder', '')}"
            for e in elements
        ).lower()

        goal_lower = active_task.goal.lower()

        # Check search results presence
        if any(k in goal_lower for k in ["search", "find", "lookup"]):
            query_m = self.decomposer._extract_search_query(active_task.goal).lower()
            if query_m and query_m in page_text:
                if any(w in page_text for w in ["result", "search results", "found", "articles", "showing"]):
                    return True, f"Search results for '{query_m}' verified on page"

        # Check authentication / login completion
        if any(k in goal_lower for k in ["login", "sign in", "auth"]):
            if any(w in page_text for w in ["welcome", "dashboard", "logout", "sign out", "profile"]):
                return True, "Authenticated session confirmed"

        # Check checkout completion
        if any(k in goal_lower for k in ["checkout", "payment", "order"]):
            if any(w in page_text for w in ["order confirmed", "receipt", "thank you", "payment successful"]):
                return True, "Payment and order confirmed"

        return False, "IN_PROGRESS"

    def plan_next_step(
        self,
        sanitized_elements: List[Dict[str, Any]],
        history: List[Dict[str, Any]] = None,
        task_goal: Optional[str] = None,
        user_confirmed: bool = False,
        current_url: str = ""
    ) -> Tuple[Optional[CandidateAction], ValidationResult, AgentState]:
        """
        Executes a single reasoning iteration of the agent planning loop:
          1. Transitions state: IDLE -> PLANNING
          2. Evaluates task completion
          3. Selects active objective
          4. Generates and ranks candidate actions
          5. Validates top candidate
          6. Records explainable trace
        """
        t0 = time.perf_counter()

        # Initialize task if not existing
        if not self.current_task or (task_goal and self.current_task.goal != task_goal):
            self.create_task(task_goal or "Complete browser task")

        task = self.current_task
        hist = history or []

        # Check pause
        if task.is_paused:
            return None, ValidationResult(allowed=False, reason="AGENT_PAUSED"), AgentState.PAUSED

        # Check objective bounds & dynamic task completion
        is_completed, comp_reason = self.check_task_completion(task, sanitized_elements, current_url)
        if is_completed or task.current_objective_index >= len(task.objectives):
            self.state_machine.transition_to(AgentState.COMPLETED, f"Task completed: {comp_reason}")
            task.status = AgentState.COMPLETED
            self.metrics["tasks_completed"] += 1
            return None, ValidationResult(allowed=False, reason=comp_reason), AgentState.COMPLETED

        active_objective = task.objectives[task.current_objective_index]
        active_objective.status = ObjectiveStatus.IN_PROGRESS

        # Transition to PLANNING
        if self.state_machine.can_transition_to(AgentState.PLANNING):
            self.state_machine.transition_to(AgentState.PLANNING, f"Planning objective: {active_objective.id}")
            task.status = AgentState.PLANNING

        # Plan next candidate action
        t_plan_start = time.perf_counter()
        selected_candidate = self.engine.plan_next_action(
            task=task,
            objective=active_objective,
            sanitized_elements=sanitized_elements,
            history=hist
        )
        t_plan_ms = (time.perf_counter() - t_plan_start) * 1000.0
        self.metrics["last_planning_latency_ms"] = round(t_plan_ms, 2)
        self.metrics["actions_planned"] += 1

        if not selected_candidate:
            # Mark objective skipped or move next
            task.current_objective_index += 1
            return None, ValidationResult(allowed=False, reason="NO_CANDIDATES_FOUND"), self.state_machine.current_state

        # Validate candidate
        t_val_start = time.perf_counter()
        if self.state_machine.can_transition_to(AgentState.VALIDATING):
            self.state_machine.transition_to(AgentState.VALIDATING, "Validating action constraints")
            task.status = AgentState.VALIDATING

        cand_dict = selected_candidate.model_dump()
        cand_dict["confirmed_by_user"] = user_confirmed

        validation = self.validator.validate_candidate(
            action_json=cand_dict,
            fused_elements=sanitized_elements,
            constraints=task.constraints,
            actions_executed_so_far=task.actions_executed,
            history=hist
        )

        t_val_ms = (time.perf_counter() - t_val_start) * 1000.0
        self.metrics["last_validation_latency_ms"] = round(t_val_ms, 2)

        if validation.allowed:
            self.metrics["actions_validated"] += 1
        else:
            self.metrics["actions_blocked"] += 1
            if validation.requires_confirmation:
                if self.state_machine.can_transition_to(AgentState.BLOCKED):
                    self.state_machine.transition_to(AgentState.BLOCKED, "Confirmation required")
                    task.status = AgentState.BLOCKED

        t_cycle_ms = (time.perf_counter() - t0) * 1000.0
        self.metrics["total_agent_cycle_ms"] = round(t_cycle_ms, 2)

        # Record explainable trace
        trace_entry = PlanTraceEntry(
            step=len(task.trace) + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            goal=task.goal,
            current_objective=active_objective.description,
            observation_summary=f"{len(sanitized_elements)} sanitized layout elements present",
            candidate_actions_count=1,
            selected_action=selected_candidate.model_dump(),
            validation=validation,
            state=self.state_machine.current_state
        )
        task.trace.append(trace_entry)
        self.memory.add_trace(trace_entry)

        return selected_candidate, validation, self.state_machine.current_state

    def plan_action(
        self,
        task: str,
        fused_elements: List[Dict[str, Any]],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Legacy-compatible planning endpoint wrapper.
        """
        candidate, validation, state = self.plan_next_step(
            sanitized_elements=fused_elements,
            history=history,
            task_goal=task
        )

        if candidate and validation.allowed:
            # Advance objective index on action planned
            if self.current_task:
                self.current_task.actions_executed += 1
                if self.current_task.current_objective_index < len(self.current_task.objectives) - 1:
                    self.current_task.current_objective_index += 1

            act_dict = {
                "action": candidate.action.value,
                "target": candidate.target or {"x": 0, "y": 0},
                "target_description": candidate.target_description,
                "confidence": candidate.confidence,
                "element_id": candidate.target_id,
                "score": candidate.score,
                "score_breakdown": candidate.score_breakdown,
                "requires_confirmation": candidate.requires_confirmation or validation.requires_confirmation
            }
            if candidate.text:
                act_dict["text"] = candidate.text
            return act_dict

        # Fallback default action
        return {
            "action": "WAIT",
            "target": {"x": 0, "y": 0},
            "target_description": validation.reason if not validation.allowed else "Wait for state update",
            "confidence": 0.90,
            "requires_confirmation": validation.requires_confirmation
        }

    def verify_step_outcome(
        self,
        action: Dict[str, Any],
        prev_elements: List[Dict[str, Any]],
        current_elements: List[Dict[str, Any]],
        prev_url: str = "",
        current_url: str = "",
        prev_title: str = "",
        current_title: str = "",
        prev_scroll: Optional[Dict[str, float]] = None,
        current_scroll: Optional[Dict[str, float]] = None,
        exec_error: Optional[str] = None,
        expected_state: Optional[Any] = None
    ) -> VerificationResult:
        """Verifies action execution outcome and updates state machine."""
        if self.state_machine.can_transition_to(AgentState.VERIFYING):
            self.state_machine.transition_to(AgentState.VERIFYING, "Verifying action outcome")
            if self.current_task:
                self.current_task.status = AgentState.VERIFYING

        active_obj_id = (
            self.current_task.objectives[self.current_task.current_objective_index].id
            if self.current_task and self.current_task.current_objective_index < len(self.current_task.objectives)
            else "obj-01"
        )

        res = self.verifier.verify_action_outcome(
            action=action,
            prev_elements=prev_elements,
            current_elements=current_elements,
            prev_url=prev_url,
            current_url=current_url,
            prev_title=prev_title,
            current_title=current_title,
            prev_scroll=prev_scroll,
            current_scroll=current_scroll,
            exec_error=exec_error,
            expected_state=expected_state,
            objective_id=active_obj_id
        )

        # Update trace if task active
        if self.current_task and self.current_task.trace:
            self.current_task.trace[-1].verification = res

        return res

    def pause(self) -> AgentState:
        if self.current_task:
            self.current_task.is_paused = True
            self.current_task.status = AgentState.PAUSED
        if self.state_machine.can_transition_to(AgentState.PAUSED):
            self.state_machine.transition_to(AgentState.PAUSED, "User requested pause")
        return self.state_machine.current_state

    def resume(self) -> AgentState:
        if self.current_task:
            self.current_task.is_paused = False
            self.current_task.status = AgentState.PLANNING
        if self.state_machine.can_transition_to(AgentState.PLANNING):
            self.state_machine.transition_to(AgentState.PLANNING, "User requested resume")
        return self.state_machine.current_state

    def stop(self) -> AgentState:
        if self.current_task:
            self.current_task.status = AgentState.IDLE
        self.state_machine.reset()
        return self.state_machine.current_state

    def get_agent_status(self) -> Dict[str, Any]:
        """Returns comprehensive agent status for UI workspace."""
        task_data = self.current_task.model_dump() if self.current_task else None
        return {
            "state": self.state_machine.current_state.value,
            "task": task_data,
            "metrics": self.metrics,
            "active_objective": (
                self.current_task.objectives[self.current_task.current_objective_index].model_dump()
                if self.current_task and self.current_task.current_objective_index < len(self.current_task.objectives)
                else None
            ),
            "trace_count": len(self.current_task.trace) if self.current_task else 0
        }
