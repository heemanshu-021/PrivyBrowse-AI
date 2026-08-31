"""
PrivyBrowse AI — Agent Working Memory & Checkpoint Store
Privacy-safe working memory tracking completed objectives,
checkpoints, action histories, idempotency states, and progress snapshots.
"""

from datetime import datetime, timezone
import hashlib
from typing import List, Dict, Any, Optional
from backend.agent.schemas import (
    Objective, PlanTraceEntry, TaskCheckpoint, CheckpointType, ActionRecord
)


class AgentMemory:
    """
    Working memory and milestone checkpoint engine for task execution.
    STRICT INVARIANT: Never stores raw secrets or unsanitized credentials.
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.completed_objectives: List[str] = []
        self.recent_actions: List[Dict[str, Any]] = []
        self.action_records: List[ActionRecord] = []
        self.checkpoints: List[TaskCheckpoint] = []
        self.recent_observations: List[Dict[str, Any]] = []
        self.state_snapshots: List[str] = []  # URL + element hash history
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

    def _scrub_pii_recursive(self, val: Any) -> Any:
        import re
        if isinstance(val, str):
            val = re.sub(r"\b(?:\d{4}\s?){2}\d{4}\b", "[REDACTED_AADHAAR]", val)
            val = re.sub(r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[REDACTED_CARD]", val)
            val = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", "[REDACTED_PAN]", val)
            val = re.sub(r"sk-(?:proj-)?[a-zA-Z0-9_\-]{12,}", "[REDACTED_API_KEY]", val)
            return val
        elif isinstance(val, dict):
            return {k: self._scrub_pii_recursive(v) for k, v in val.items()}
        elif isinstance(val, (list, tuple)):
            return [self._scrub_pii_recursive(item) for item in val]
        return val

    def record_action_audit(self, record: ActionRecord):
        """Stores structured immutable action audit record with PII scrubbing."""
        if record.result:
            record.result = self._scrub_pii_recursive(record.result)
        self.action_records.append(record)
        if len(self.action_records) > self.max_history:
            self.action_records.pop(0)

    def save_checkpoint(
        self,
        task_id: str,
        checkpoint_type: CheckpointType,
        step_index: int,
        url: str,
        dom_fingerprint: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskCheckpoint:
        """Creates and stores a milestone checkpoint."""
        now_iso = datetime.now(timezone.utc).isoformat()
        chk_id = f"chk-{task_id}-{step_index}-{checkpoint_type.value}"
        checkpoint = TaskCheckpoint(
            id=chk_id,
            task_id=task_id,
            checkpoint_type=checkpoint_type,
            step_index=step_index,
            url=url,
            dom_fingerprint=dom_fingerprint,
            timestamp=now_iso,
            metadata=metadata or {}
        )
        self.checkpoints.append(checkpoint)
        if len(self.checkpoints) > 50:
            self.checkpoints.pop(0)
        return checkpoint

    def get_latest_checkpoint(self, task_id: Optional[str] = None) -> Optional[TaskCheckpoint]:
        """Returns the most recent valid checkpoint for a task."""
        if not self.checkpoints:
            return None
        if task_id:
            task_chks = [c for c in self.checkpoints if c.task_id == task_id]
            return task_chks[-1] if task_chks else None
        return self.checkpoints[-1]

    def rollback_to_checkpoint(self, checkpoint_id: str) -> Optional[TaskCheckpoint]:
        """Rolls back checkpoint stack to the specified checkpoint."""
        for idx, chk in enumerate(self.checkpoints):
            if chk.id == checkpoint_id:
                self.checkpoints = self.checkpoints[:idx + 1]
                return chk
        return None

    def record_state_snapshot(self, url: str, elements: List[Dict[str, Any]]):
        """Computes and records page state hash for stagnant progress detection."""
        element_states = sorted(
            f"{e.get('id', '')}:{e.get('value', '')}:{e.get('checked', '')}:{e.get('selected', '')}:{e.get('state_clicked', '')}"
            for e in elements if e.get("id")
        )
        raw_repr = f"{url}|{','.join(element_states)}"
        state_hash = hashlib.md5(raw_repr.encode("utf-8")).hexdigest()
        self.state_snapshots.append(state_hash)
        if len(self.state_snapshots) > 20:
            self.state_snapshots.pop(0)

    def is_progress_stagnant(self, max_stagnant_turns: int = 3) -> bool:
        """Returns True if the browser state has not changed across consecutive turns."""
        if len(self.state_snapshots) < max_stagnant_turns:
            return False
        recent = self.state_snapshots[-max_stagnant_turns:]
        return len(set(recent)) == 1

    def is_action_idempotent(
        self,
        action_type: str,
        target_id: str,
        expected_value: Any,
        current_elements: List[Dict[str, Any]],
        current_url: str = ""
    ) -> bool:
        """
        Determines whether the target element is already in the expected postcondition state,
        preventing duplicate or accidental redundant actions.
        """
        if action_type in ("NAVIGATE", "OPEN_URL"):
            if current_url and expected_value:
                return current_url.rstrip("/").lower() == str(expected_value).rstrip("/").lower()
            return False

        if not current_elements or not target_id:
            return False

        target = next((e for e in current_elements if e.get("id") == target_id), None)
        if not target:
            return False

        elif action_type == "CHECK":
            # If element is already checked, redundant action
            return bool(target.get("checked") or target.get("aria_checked"))

        elif action_type == "UNCHECK":
            # If element is already unchecked, redundant action
            return not bool(target.get("checked") or target.get("aria_checked"))

        elif action_type == "TYPE":
            curr_val = str(target.get("value", "") or target.get("text", ""))
            return curr_val == str(expected_value)

        elif action_type == "SELECT":
            curr_selected = target.get("selected_option") or target.get("value")
            return str(curr_selected) == str(expected_value)

        return False

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
        self.action_records.clear()
        self.checkpoints.clear()
        self.recent_observations.clear()
        self.state_snapshots.clear()
        self.failed_attempts.clear()
        self.traces.clear()
