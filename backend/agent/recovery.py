"""
PrivyBrowse AI — Failure Classification, Recovery Engine & Progress Tracker
Classifies execution/verification failures, enforces bounded retries, detects action loops/stalls,
and executes self-healing recovery strategies or clean safe stops.
"""

from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from backend.agent.schemas import (
    FailureCategory,
    RecoveryRecommendation,
    ActionType,
    AgentTask,
    CandidateAction
)
from backend.agent.differencer import StateDiff


class ProgressTracker:
    """
    Tracks state transitions across turns to detect:
      1. Repetitive identical actions with zero progress.
      2. State oscillations (State A <-> State B).
      3. Stagnant execution loops.
    """

    def __init__(self, max_history: int = 15):
        self.state_history: deque[Tuple[str, str, str]] = deque(maxlen=max_history)  # (url, dom_fp, action_signature)
        self.action_counts: Dict[str, int] = {}
        self.no_progress_turns: int = 0
        self.max_identical_actions = 3
        self.max_stagnant_turns = 4

    def record_turn(
        self,
        url: str,
        dom_fingerprint: str,
        action_signature: str,
        has_progress: bool
    ):
        """Records state and action after each turn."""
        self.state_history.append((url, dom_fingerprint, action_signature))
        self.action_counts[action_signature] = self.action_counts.get(action_signature, 0) + 1

        if has_progress:
            self.no_progress_turns = 0
        else:
            self.no_progress_turns += 1

    def detect_loop_or_stall(self) -> Tuple[bool, Optional[FailureCategory], Optional[str]]:
        """
        Evaluates history for loops or stagnant progress.
        Returns (is_stalled, failure_category, diagnostic_reason).
        """
        # 1. Check for stagnant turns with zero state progress
        if self.no_progress_turns >= self.max_stagnant_turns:
            return True, FailureCategory.LOOP_DETECTED, f"Execution stalled: {self.no_progress_turns} consecutive turns produced no state change"

        # 2. Check for identical consecutive actions
        if len(self.state_history) >= self.max_identical_actions:
            recent = list(self.state_history)[-self.max_identical_actions:]
            first_action = recent[0][2]
            if all(item[2] == first_action for item in recent) and not first_action.startswith("WAIT"):
                return True, FailureCategory.LOOP_DETECTED, f"Action loop detected: action '{first_action}' repeated {self.max_identical_actions} times consecutively"

        # 3. Check for 2-state oscillation (A -> B -> A -> B)
        if len(self.state_history) >= 4:
            h = list(self.state_history)
            if h[-1][0] == h[-3][0] and h[-2][0] == h[-4][0] and h[-1][0] != h[-2][0]:
                return True, FailureCategory.LOOP_DETECTED, "Navigation oscillation detected between two alternating URLs"
            if h[-1][1] == h[-3][1] and h[-2][1] == h[-4][1] and h[-1][1] != h[-2][1]:
                return True, FailureCategory.LOOP_DETECTED, "DOM layout oscillation detected between two alternating states"

        return False, None, None

    def reset(self):
        self.state_history.clear()
        self.action_counts.clear()
        self.no_progress_turns = 0


class FailureClassifier:
    """
    Maps action results, state differences, and validator outputs to strongly typed failure categories.
    """

    @classmethod
    def classify(
        cls,
        action: Dict[str, Any],
        exec_error: Optional[str] = None,
        diff: Optional[StateDiff] = None,
        target_found: bool = True,
        is_timeout: bool = False,
        is_blocked: bool = False,
        is_privacy_blocked: bool = False
    ) -> FailureCategory:
        """
        Categorizes the exact root cause of an action failure.
        """
        err_str = (exec_error or "").upper()

        if is_privacy_blocked or "PRIVACY" in err_str or "PII" in err_str:
            return FailureCategory.PRIVACY_BLOCK

        if is_blocked or "VALIDATION" in err_str or "CONFIRMATION" in err_str:
            return FailureCategory.VALIDATION_FAILURE

        if is_timeout or "TIMEOUT" in err_str:
            return FailureCategory.ACTION_TIMEOUT

        if "EXTENSION" in err_str or "DISCONNECTED" in err_str:
            return FailureCategory.EXTENSION_DISCONNECTED

        if not target_found or "TARGET_NOT_FOUND" in err_str or "ELEMENT_NOT_FOUND" in err_str:
            return FailureCategory.TARGET_NOT_FOUND

        if "UNEXPECTED_NAVIGATION" in err_str or "STALE_NAVIGATION" in err_str:
            return FailureCategory.UNEXPECTED_NAVIGATION

        if "STALE" in err_str or "TAB_MISMATCH" in err_str or "DOM_MUTATION_MISMATCH" in err_str or "STALE_TARGET" in err_str:
            return FailureCategory.TARGET_STALE

        if diff and not (diff.url_changed or diff.dom_mutated or diff.target_value_changed or diff.scroll_changed or diff.modal_appeared or diff.is_at_scroll_boundary):
            return FailureCategory.NO_STATE_CHANGE

        return FailureCategory.UNKNOWN_FAILURE


class RecoveryEngine:
    """
    Determines actionable recovery recommendations and bounded retry policies.
    Guarantees the agent never performs infinite blind retries.
    """

    def __init__(self, max_retries_per_objective: int = 2, max_total_retries: int = 6):
        self.max_retries_per_objective = max_retries_per_objective
        self.max_total_retries = max_total_retries
        self.retry_counts: Dict[str, int] = {}  # objective_id -> retry count
        self.total_retries: int = 0

    def recommend_recovery(
        self,
        failure_category: FailureCategory,
        action: Dict[str, Any],
        objective_id: str = "obj-01"
    ) -> Tuple[RecoveryRecommendation, str]:
        """
        Calculates recovery plan and determines whether safe stop is required.
        """
        self.total_retries += 1
        curr_obj_retries = self.retry_counts.get(objective_id, 0) + 1
        self.retry_counts[objective_id] = curr_obj_retries

        # Check budget limits
        if self.total_retries > self.max_total_retries:
            return RecoveryRecommendation.SAFE_STOP, f"Exhausted total retry budget ({self.total_retries}/{self.max_total_retries}). Halting safely."

        if curr_obj_retries > self.max_retries_per_objective:
            return RecoveryRecommendation.SAFE_STOP, f"Exhausted retry attempts ({curr_obj_retries}/{self.max_retries_per_objective}) for objective '{objective_id}'."

        # 1. Target Stale
        if failure_category == FailureCategory.TARGET_STALE:
            return RecoveryRecommendation.REPERCEIVE, f"Target element became stale. Triggering re-perception (attempt {curr_obj_retries}/{self.max_retries_per_objective})."

        # 2. Target Not Found
        if failure_category == FailureCategory.TARGET_NOT_FOUND:
            act_type = action.get("action", "CLICK")
            if curr_obj_retries == 1:
                return RecoveryRecommendation.REPERCEIVE, "Target not found in current viewport. Refreshing perception."
            elif curr_obj_retries == 2 and act_type != "SCROLL":
                return RecoveryRecommendation.RETRY_ALTERNATIVE, "Target still unresolved. Attempting alternative scroll/search strategy."
            return RecoveryRecommendation.SAFE_STOP, f"Unable to locate target '{action.get('target_id')}' after {curr_obj_retries} attempts."

        # 3. No State Change
        if failure_category == FailureCategory.NO_STATE_CHANGE:
            act_type = action.get("action", "CLICK")
            if act_type == "CLICK":
                return RecoveryRecommendation.RETRY_ALTERNATIVE, "Click produced no observable state change. Attempting alternative submission (e.g. Enter key or parent element)."
            return RecoveryRecommendation.REPERCEIVE, "Action produced no observable change. Re-perceiving browser state."

        # 4. Unexpected Navigation
        if failure_category == FailureCategory.UNEXPECTED_NAVIGATION:
            return RecoveryRecommendation.REBUILD_CONTEXT, "Unexpected browser navigation. Rebuilding context state and replanning."

        # 5. Validation Failure / Privacy Block
        if failure_category in (FailureCategory.VALIDATION_FAILURE, FailureCategory.PRIVACY_BLOCK):
            return RecoveryRecommendation.SAFE_STOP, f"Action blocked by safety policy ({failure_category.value}). Safe stop enforced."

        # 6. Loop Detected
        if failure_category == FailureCategory.LOOP_DETECTED:
            return RecoveryRecommendation.SAFE_STOP, "Action loop / stall detected. Halting execution safely."

        # Default fallback
        return RecoveryRecommendation.REPERCEIVE, f"Recovering from {failure_category.value} via re-perception."

    def reset(self):
        self.retry_counts.clear()
        self.total_retries = 0
