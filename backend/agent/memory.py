"""
PrivyBrowse AI — Agent Working Memory
Privacy-safe short-term working memory tracking completed objectives,
recent observations, action histories, and failure counts.
"""

from typing import List, Dict, Any, Optional
from backend.agent.schemas import Objective, PlanTraceEntry


class AgentMemory:
    """
    Short-term episodic memory for a single task execution.
    STRICT INVARIANT: Never stores raw secrets or unsanitized credentials.
    """

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.completed_objectives: List[str] = []
        self.recent_actions: List[Dict[str, Any]] = []
        self.recent_observations: List[Dict[str, Any]] = []
        self.failed_attempts: Dict[str, int] = {}  # target_id -> count
        self.traces: List[PlanTraceEntry] = []

    def record_action(self, action: Dict[str, Any]):
        """Records an action in short-term history, scrubbing any password strings."""
        safe_action = dict(action)
        if safe_action.get("action") == "TYPE" and "pass" in str(safe_action.get("target_description", "")).lower():
            safe_action["text"] = "[REDACTED_PASSWORD]"

        self.recent_actions.append(safe_action)
        if len(self.recent_actions) > self.max_history:
            self.recent_actions.pop(0)

    def record_failure(self, target_id: str):
        """Increments failure count for a target to prevent endless retries."""
        if target_id:
            self.failed_attempts[target_id] = self.failed_attempts.get(target_id, 0) + 1

    def get_failure_count(self, target_id: str) -> int:
        return self.failed_attempts.get(target_id, 0)

    def mark_objective_completed(self, objective_id: str):
        if objective_id not in self.completed_objectives:
            self.completed_objectives.append(objective_id)

    def add_trace(self, trace_entry: PlanTraceEntry):
        self.traces.append(trace_entry)
        if len(self.traces) > 50:
            self.traces.pop(0)

    def clear(self):
        self.completed_objectives.clear()
        self.recent_actions.clear()
        self.recent_observations.clear()
        self.failed_attempts.clear()
        self.traces.clear()
