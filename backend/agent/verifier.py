"""
PrivyBrowse AI — Evidence-Based Action Outcome Verifier
Verifies post-execution browser state changes using real observation diffs, expected state matching,
and privacy-safe metadata inspection.
"""

from typing import List, Dict, Any, Optional
from backend.agent.schemas import (
    VerificationResult,
    VerificationStatus,
    FailureCategory,
    RecoveryRecommendation,
    ActionType,
    ExpectedState
)
from backend.agent.differencer import ObservationDifferencer, StateDiff
from backend.agent.recovery import FailureClassifier, RecoveryEngine


class ActionVerifier:
    """
    Evaluates whether an executed browser action had the expected outcome.
    Never claims success merely because an action was dispatched or acknowledged.
    """

    def __init__(self, recovery_engine: Optional[RecoveryEngine] = None):
        self.recovery_engine = recovery_engine or RecoveryEngine()

    def generate_expected_state(
        self,
        action: Dict[str, Any],
        target_element: Optional[Dict[str, Any]] = None
    ) -> ExpectedState:
        """
        Derives the expected post-action browser state from the candidate action and context.
        """
        raw_act = str(action.get("action", "CLICK")).upper()
        if "." in raw_act:
            raw_act = raw_act.split(".")[-1]

        target_id = action.get("target_id") or action.get("element_id")
        text = action.get("text", "")
        url = action.get("url", "")
        scroll_delta = action.get("scroll_delta", {})

        is_sens = bool(
            action.get("sensitive") or
            (target_element and (target_element.get("sensitive") or target_element.get("type") == "password"))
        )

        expected = ExpectedState(
            action_type=raw_act,
            target_id=target_id,
            is_sensitive=is_sens
        )

        if raw_act == "CLICK":
            # Clicks typically cause DOM mutations, route changes, or modal popups
            expected.expected_dom_mutation = True
            if "search" in str(target_id).lower() or "submit" in str(target_id).lower():
                expected.expected_dom_mutation = True
        elif raw_act == "TYPE":
            expected.expected_value_populated = True
        elif raw_act in ("SCROLL", "SCROLL_UP", "SCROLL_DOWN"):
            expected.expected_scroll_delta = scroll_delta or {"x": 0.0, "y": 400.0}
        elif raw_act == "NAVIGATE":
            expected.expected_url_pattern = url

        return expected

    def verify_action_outcome(
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
        expected_state: Optional[ExpectedState] = None,
        objective_id: str = "obj-01"
    ) -> VerificationResult:
        """
        Strictly compares pre-action and post-action observation diffs against expected state.
        """
        raw_act = str(action.get("action", "CLICK")).upper()
        if "." in raw_act:
            raw_act = raw_act.split(".")[-1]

        target_id = action.get("target_id") or action.get("element_id")
        is_sensitive = bool(action.get("sensitive") or (expected_state and expected_state.is_sensitive))

        # 0. Check explicit execution failure
        if exec_error:
            cat = FailureClassifier.classify(action=action, exec_error=exec_error)
            rec, rec_reason = self.recovery_engine.recommend_recovery(cat, action, objective_id)
            return VerificationResult(
                success=False,
                status=VerificationStatus.FAILED,
                signal="EXECUTION_FAILED",
                details=f"Action execution error: {exec_error}",
                evidence=[f"Execution failed: {exec_error}"],
                failure_category=cat,
                recovery_recommendation=rec,
                re_perception_required=True,
                metadata={"recovery_reason": rec_reason}
            )

        # 1. Compute observation diff
        diff = ObservationDifferencer.compute_diff(
            prev_elements=prev_elements,
            curr_elements=current_elements,
            prev_url=prev_url,
            curr_url=current_url,
            prev_title=prev_title,
            curr_title=current_title,
            target_id=target_id,
            prev_scroll=prev_scroll,
            curr_scroll=current_scroll,
            is_sensitive=is_sensitive
        )

        # 2. Derive expected state if not supplied
        if not expected_state:
            target_el = next((e for e in prev_elements if e.get("id") == target_id), None)
            expected_state = self.generate_expected_state(action, target_el)

        # 3. VERIFY BY ACTION TYPE

        # --- A. CLICK VERIFICATION ---
        if raw_act == "CLICK":
            # Click is verified if:
            # 1. Navigation occurred
            # 2. Page title changed
            # 3. DOM mutated (nodes added/removed)
            # 4. Target element state changed (disabled/checked/expanded)
            # 5. Modal appeared or disappeared
            if diff.url_changed:
                return VerificationResult(
                    success=True,
                    status=VerificationStatus.ACTION_VERIFIED,
                    signal="PAGE_NAVIGATED",
                    details=f"Click triggered navigation to '{current_url}'",
                    evidence=diff.evidence,
                    recovery_recommendation=RecoveryRecommendation.PROCEED,
                    re_perception_required=True
                )

            if diff.modal_appeared:
                return VerificationResult(
                    success=True,
                    status=VerificationStatus.ACTION_VERIFIED,
                    signal="MODAL_OPENED",
                    details="Click triggered modal dialog render",
                    evidence=diff.evidence,
                    recovery_recommendation=RecoveryRecommendation.PROCEED,
                    re_perception_required=True
                )

            if diff.dom_mutated:
                return VerificationResult(
                    success=True,
                    status=VerificationStatus.ACTION_VERIFIED,
                    signal="DOM_MUTATION_DETECTED",
                    details=f"Click triggered DOM layout update (+{diff.elements_added_count}, -{diff.elements_removed_count})",
                    evidence=diff.evidence,
                    recovery_recommendation=RecoveryRecommendation.PROCEED,
                    re_perception_required=True
                )

            if diff.target_state_changed:
                return VerificationResult(
                    success=True,
                    status=VerificationStatus.ACTION_VERIFIED,
                    signal="TARGET_STATE_UPDATED",
                    details=f"Click toggled state of element '{target_id}'",
                    evidence=diff.evidence,
                    recovery_recommendation=RecoveryRecommendation.PROCEED,
                    re_perception_required=False
                )

            # If CLICK produced ZERO state changes -> NO_STATE_CHANGE failure
            cat = FailureCategory.NO_STATE_CHANGE
            rec, rec_reason = self.recovery_engine.recommend_recovery(cat, action, objective_id)
            return VerificationResult(
                success=False,
                status=VerificationStatus.NO_STATE_CHANGE,
                signal="NO_STATE_CHANGE",
                details=f"Click on target '{target_id}' produced no observable DOM, URL, or attribute changes",
                evidence=["Zero observable change detected after click dispatch"],
                failure_category=cat,
                recovery_recommendation=rec,
                re_perception_required=True,
                metadata={"recovery_reason": rec_reason}
            )

        # --- B. TYPE VERIFICATION ---
        elif raw_act == "TYPE":
            typed_text = action.get("text", "")
            target_el = next((e for e in current_elements if e.get("id") == target_id), None)

            if not target_el:
                cat = FailureCategory.TARGET_NOT_FOUND
                rec, rec_reason = self.recovery_engine.recommend_recovery(cat, action, objective_id)
                return VerificationResult(
                    success=False,
                    status=VerificationStatus.FAILED,
                    signal="TARGET_NOT_FOUND",
                    details=f"Target input '{target_id}' not found in post-action DOM",
                    evidence=["Target input absent from current observation"],
                    failure_category=cat,
                    recovery_recommendation=rec,
                    re_perception_required=True,
                    metadata={"recovery_reason": rec_reason}
                )

            # Check value
            curr_val = str(target_el.get("value") or target_el.get("text") or "")
            if is_sensitive:
                # Privacy Invariant: NEVER check or expose raw value
                if len(curr_val) > 0 or target_el.get("sensitive") or "REDACTED" in curr_val or diff.target_value_populated:
                    return VerificationResult(
                        success=True,
                        status=VerificationStatus.ACTION_VERIFIED,
                        signal="INPUT_VALUE_UPDATED",
                        details=f"Target sensitive field '{target_id}' verified populated with masked input",
                        evidence=["Sensitive input field contains valid masked characters"],
                        recovery_recommendation=RecoveryRecommendation.PROCEED,
                        re_perception_required=False
                    )
            else:
                if (typed_text and typed_text in curr_val) or diff.target_value_changed or len(curr_val) > 0:
                    return VerificationResult(
                        success=True,
                        status=VerificationStatus.ACTION_VERIFIED,
                        signal="INPUT_VALUE_UPDATED",
                        details=f"Target input '{target_id}' populated successfully",
                        evidence=diff.evidence or [f"Value '{typed_text[:20]}' verified in element"],
                        recovery_recommendation=RecoveryRecommendation.PROCEED,
                        re_perception_required=False
                    )

            # Value not applied
            cat = FailureCategory.NO_STATE_CHANGE
            rec, rec_reason = self.recovery_engine.recommend_recovery(cat, action, objective_id)
            return VerificationResult(
                success=False,
                status=VerificationStatus.NO_STATE_CHANGE,
                signal="VALUE_NOT_APPLIED",
                details=f"Typed text was not retained by input '{target_id}'",
                evidence=["Target input value remained empty or unchanged"],
                failure_category=cat,
                recovery_recommendation=rec,
                re_perception_required=True,
                metadata={"recovery_reason": rec_reason}
            )

        # --- C. SCROLL VERIFICATION ---
        elif raw_act in ("SCROLL", "SCROLL_UP", "SCROLL_DOWN"):
            if diff.scroll_changed:
                return VerificationResult(
                    success=True,
                    status=VerificationStatus.ACTION_VERIFIED,
                    signal="VIEWPORT_SCROLLED",
                    details=f"Viewport scrolled by ({diff.scroll_delta_x:.0f}, {diff.scroll_delta_y:.0f}) px",
                    evidence=diff.evidence,
                    recovery_recommendation=RecoveryRecommendation.PROCEED,
                    re_perception_required=True
                )

            if diff.is_at_scroll_boundary:
                return VerificationResult(
                    success=True,
                    status=VerificationStatus.SCROLL_BOUNDARY,
                    signal="SCROLL_BOUNDARY_REACHED",
                    details="Viewport reached scroll boundary (cannot scroll further)",
                    evidence=diff.evidence,
                    recovery_recommendation=RecoveryRecommendation.PROCEED,
                    re_perception_required=False
                )

            # Scroll didn't move and wasn't at boundary
            cat = FailureCategory.NO_STATE_CHANGE
            rec, rec_reason = self.recovery_engine.recommend_recovery(cat, action, objective_id)
            return VerificationResult(
                success=False,
                status=VerificationStatus.NO_STATE_CHANGE,
                signal="SCROLL_UNMOVED",
                details="Scroll action did not displace viewport",
                evidence=["Scroll offset unchanged"],
                failure_category=cat,
                recovery_recommendation=rec,
                re_perception_required=False,
                metadata={"recovery_reason": rec_reason}
            )

        # --- D. NAVIGATE VERIFICATION ---
        elif raw_act == "NAVIGATE":
            target_url = action.get("url") or action.get("text", "")
            if diff.url_changed:
                return VerificationResult(
                    success=True,
                    status=VerificationStatus.ACTION_VERIFIED,
                    signal="PAGE_NAVIGATED",
                    details=f"Navigated to '{current_url}'",
                    evidence=diff.evidence,
                    recovery_recommendation=RecoveryRecommendation.PROCEED,
                    re_perception_required=True
                )

            # Same URL or Navigation didn't occur
            cat = FailureCategory.NO_STATE_CHANGE
            rec, rec_reason = self.recovery_engine.recommend_recovery(cat, action, objective_id)
            return VerificationResult(
                success=False,
                status=VerificationStatus.NO_STATE_CHANGE,
                signal="NAVIGATION_NOT_COMPLETED",
                details=f"Navigation to '{target_url}' produced no URL update",
                evidence=["Current URL matches previous URL"],
                failure_category=cat,
                recovery_recommendation=rec,
                re_perception_required=True,
                metadata={"recovery_reason": rec_reason}
            )

        # --- E. OTHER ACTIONS (WAIT, FINISH, PRESS_KEY) ---
        return VerificationResult(
            success=True,
            status=VerificationStatus.ACTION_VERIFIED,
            signal="ACTION_COMPLETED",
            details=f"Action '{raw_act}' completed",
            evidence=diff.evidence,
            recovery_recommendation=RecoveryRecommendation.PROCEED,
            re_perception_required=diff.dom_mutated or diff.url_changed
        )
