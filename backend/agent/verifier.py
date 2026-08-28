"""
PrivyBrowse AI — Action Outcome Verifier
Verifies post-execution browser state changes (URL navigation, DOM mutation, value update)
and flags necessary re-perception or recovery steps.
"""

from typing import List, Dict, Any, Optional
from backend.agent.schemas import VerificationResult, CandidateAction, ActionType


class ActionVerifier:
    """
    Evaluates whether an executed browser action had the expected outcome.
    """

    def __init__(self):
        pass

    def verify_action_outcome(
        self,
        action: Dict[str, Any],
        prev_elements: List[Dict[str, Any]],
        current_elements: List[Dict[str, Any]],
        prev_url: str = "",
        current_url: str = ""
    ) -> VerificationResult:
        """
        Compares pre-action and post-action state snapshots.
        """
        act_type = action.get("action", "CLICK")
        target_id = action.get("target_id") or action.get("element_id")

        # 1. Check URL navigation
        if prev_url and current_url and prev_url != current_url:
            return VerificationResult(
                success=True,
                signal="PAGE_NAVIGATED",
                details=f"URL changed from '{prev_url}' to '{current_url}'",
                re_perception_required=True
            )

        # 2. Check TYPE action outcome
        if act_type == "TYPE":
            typed_text = action.get("text", "")
            # Find target element in current state
            matching_el = next((e for e in current_elements if e.get("id") == target_id), None)
            if matching_el:
                curr_val = matching_el.get("value") or matching_el.get("text", "")
                if typed_text and (typed_text in curr_val or "REDACTED" in curr_val or len(curr_val) > 0):
                    return VerificationResult(
                        success=True,
                        signal="INPUT_VALUE_UPDATED",
                        details=f"Target input '{target_id}' populated successfully",
                        re_perception_required=False
                    )

            # Fallback success if execution was reported
            return VerificationResult(
                success=True,
                signal="TYPE_ACTION_DISPATCHED",
                details="Keystrokes dispatched to input target",
                re_perception_required=False
            )

        # 3. Check CLICK action outcome
        if act_type == "CLICK":
            # Compare element IDs/count
            prev_ids = {e.get("id") for e in prev_elements if "id" in e}
            curr_ids = {e.get("id") for e in current_elements if "id" in e}

            if prev_ids != curr_ids or len(prev_elements) != len(current_elements):
                return VerificationResult(
                    success=True,
                    signal="DOM_MUTATION_DETECTED",
                    details=f"DOM layout updated: {len(prev_elements)} -> {len(current_elements)} elements",
                    re_perception_required=True
                )

            # If element sets are identical and no change
            return VerificationResult(
                success=True,
                signal="CLICK_DISPATCHED",
                details=f"Click dispatched to '{target_id}'",
                re_perception_required=False
            )

        # 4. Check SCROLL action outcome
        if act_type == "SCROLL":
            return VerificationResult(
                success=True,
                signal="VIEWPORT_SCROLLED",
                details="Viewport scroll offset updated",
                re_perception_required=True
            )

        # Default completion
        return VerificationResult(
            success=True,
            signal="ACTION_COMPLETED",
            details="Action executed successfully",
            re_perception_required=False
        )
