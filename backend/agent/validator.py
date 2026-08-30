"""
PrivyBrowse AI — Action Validation & Safety Gatekeeper
Validates all candidate actions before dispatch. Guarantees that no invalid,
out-of-bounds, adversarial, deceptive, unverified, or high-risk unconfirmed action is executed.
"""

from typing import Dict, Any, List, Optional, Tuple
from backend.agent.schemas import (
    ValidationResult, RiskLevel, TaskConstraints, ActionType
)
from backend.security.navigation_guard import NavigationGuard
from backend.security.deceptive_ui_guard import DeceptiveUIGuard
from backend.security.schemas import ThreatLevel


class ActionValidator:
    """
    Pre-execution Safety Gatekeeper.
    Guarantees no invalid, unverified, out-of-budget, deceptive, or high-risk unconfirmed action is executed.
    """

    def __init__(self, min_confidence: float = 0.50):
        self.valid_actions = {
            "CLICK", "TYPE", "SCROLL", "SCROLL_UP", "SCROLL_DOWN",
            "PRESS_KEY", "NAVIGATE", "WAIT", "GO_BACK", "GO_FORWARD", "FINISH"
        }
        self.min_confidence = min_confidence

    def validate_action(
        self,
        action_json: Dict[str, Any],
        screen_width: int = 1920,
        screen_height: int = 1080
    ) -> Tuple[bool, str]:
        """
        Legacy-compatible validation method returning (is_valid, error_message).
        """
        res = self.validate_candidate(
            action_json=action_json,
            fused_elements=[],
            screen_width=screen_width,
            screen_height=screen_height
        )
        return res.allowed, res.reason

    def validate_candidate(
        self,
        action_json: Dict[str, Any],
        fused_elements: List[Dict[str, Any]] = None,
        constraints: Optional[TaskConstraints] = None,
        actions_executed_so_far: int = 0,
        history: List[Dict[str, Any]] = None,
        screen_width: int = 1920,
        screen_height: int = 1080,
        current_url: str = ""
    ) -> ValidationResult:
        """
        Comprehensive pre-execution validation with security, link safety,
        deceptive UI analysis, and budget checks.
        """
        if not isinstance(action_json, dict):
            return ValidationResult(allowed=False, reason="ACTION_MUST_BE_JSON_OBJECT")

        raw_act = action_json.get("action")
        if hasattr(raw_act, "value"):
            action_name = raw_act.value
        else:
            action_name = str(raw_act).split(".")[-1] if raw_act else None

        if not action_name or action_name not in self.valid_actions:
            return ValidationResult(
                allowed=False,
                reason=f"INVALID_ACTION_NAME: '{action_name}'. Must be one of {self.valid_actions}"
            )

        # 1. Action Budget Check
        task_limits = constraints or TaskConstraints()
        if actions_executed_so_far >= task_limits.max_actions:
            return ValidationResult(
                allowed=False,
                reason=f"ACTION_BUDGET_EXCEEDED: Max limit of {task_limits.max_actions} actions reached.",
                risk_level=RiskLevel.HIGH
            )

        # 2. Loop Detection Check
        hist = history or []
        if len(hist) >= 3:
            target_id = action_json.get("target_id") or action_json.get("element_id")
            recent_same = [
                h for h in hist[-3:]
                if h.get("action") == action_name and (h.get("target_id") == target_id or h.get("targetId") == target_id or h.get("element_id") == target_id)
            ]

            if len(recent_same) >= 3:
                return ValidationResult(
                    allowed=False,
                    reason="POSSIBLE_AGENT_LOOP: Same action repeated 3 times on same target without progress.",
                    risk_level=RiskLevel.HIGH
                )

        # 3. Coordinate & Boundary Checks for CLICK / TYPE
        if action_name in ("CLICK", "TYPE"):
            target = action_json.get("target")
            if not target or not isinstance(target, dict):
                return ValidationResult(
                    allowed=False,
                    reason=f"MISSING_TARGET_COORDINATES: Action {action_name} requires a target {{x, y}} object"
                )

            x = target.get("x")
            y = target.get("y")

            if x is None or y is None:
                return ValidationResult(allowed=False, reason="Target coordinates x and y are required")

            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                return ValidationResult(allowed=False, reason="Target coordinates must be numbers")

            if x < 0 or y < 0:
                return ValidationResult(allowed=False, reason="Coordinates cannot be negative")

            if x > screen_width or y > screen_height:
                return ValidationResult(
                    allowed=False,
                    reason=f"COORDINATES_OUT_OF_BOUNDS: ({x}, {y}) exceeds screen bounds ({screen_width}x{screen_height})"
                )

        # 4. Confidence Threshold Check
        conf = float(action_json.get("confidence", 0.90))
        if conf < self.min_confidence:
            return ValidationResult(
                allowed=False,
                reason=f"LOW_TARGET_CONFIDENCE: Confidence {conf:.2f} is below minimum threshold {self.min_confidence:.2f}",
                risk_level=RiskLevel.MEDIUM
            )

        # 5. Target Element Security, Deceptive UI & Visibility Checks
        target_id = action_json.get("target_id") or action_json.get("element_id")
        if target_id and fused_elements:
            matched_el = next((e for e in fused_elements if e.get("id") == target_id), None)
            if matched_el:
                # 5a. Deceptive UI Analysis
                deceptive_res = DeceptiveUIGuard.analyze_element(matched_el, current_url=current_url)
                if deceptive_res.is_deceptive:
                    if deceptive_res.risk_level == ThreatLevel.CRITICAL:
                        return ValidationResult(
                            allowed=False,
                            reason=f"DECEPTIVE_UI_BLOCKED: {deceptive_res.reason}",
                            risk_level=RiskLevel.CRITICAL,
                            requires_confirmation=True,
                            details={"mismatch_type": deceptive_res.mismatch_type}
                        )
                    elif deceptive_res.risk_level == ThreatLevel.HIGH_RISK:
                        return ValidationResult(
                            allowed=False,
                            reason=f"SECURITY_RISK_BLOCKED: {deceptive_res.reason}",
                            risk_level=RiskLevel.HIGH
                        )

                # 5b. Link Safety for LINK elements
                if matched_el.get("type") == "LINK" or matched_el.get("tag") == "a":
                    href = matched_el.get("attributes", {}).get("href", "")
                    link_text = matched_el.get("text", "")
                    if href:
                        link_res = NavigationGuard.validate_link_safety(link_text, href, current_url=current_url)
                        if not link_res.is_safe:
                            return ValidationResult(
                                allowed=False,
                                reason=f"UNSAFE_LINK_BLOCKED: {link_res.reason}",
                                risk_level=RiskLevel.HIGH,
                                details={"error_code": link_res.error_code, "target_url": link_res.target_url}
                            )

                # 5c. Visibility Checks
                vis = str(matched_el.get("visibility", "VISIBLE")).upper()
                if vis in ("HIDDEN", "INVISIBLE", "OCCLUDED") or matched_el.get("visible") is False:
                    return ValidationResult(
                        allowed=False,
                        reason=f"TARGET_IS_{vis}: Action cannot be performed on hidden/invisible element '{target_id}'",
                        risk_level=RiskLevel.HIGH
                    )

                # 5d. Check for destructive/critical keywords in matched element
                el_text = str(matched_el.get("text", "")).lower()
                if any(w in el_text for w in ("delete", "destroy", "wipe", "format", "transfer", "pay", "authorize", "wire")):
                    action_json["risk_level"] = RiskLevel.CRITICAL
                    action_json["requires_confirmation"] = True

        # 6. NAVIGATE Specific Security Checks
        if action_name == "NAVIGATE":
            url = action_json.get("url")
            if not url:
                return ValidationResult(allowed=False, reason="NAVIGATE action requires a 'url' parameter")

            is_safe, nav_code, nav_err = NavigationGuard.validate_url(url, current_url=current_url)
            if not is_safe:
                return ValidationResult(
                    allowed=False,
                    reason=f"NAVIGATION_GUARD_BLOCKED: {nav_err}",
                    risk_level=RiskLevel.HIGH,
                    details={"error_code": nav_code, "blocked_url": url}
                )

        # 7. Financial / High-Risk Confirmation Policy Check
        risk = action_json.get("risk_level", RiskLevel.LOW)
        if isinstance(risk, str):
            try:
                risk = RiskLevel(risk)
            except Exception:
                risk = RiskLevel.LOW

        requires_confirmation = bool(action_json.get("requires_confirmation", False))
        if risk == RiskLevel.CRITICAL or requires_confirmation:
            if task_limits.require_confirmation_for_sensitive and not action_json.get("confirmed_by_user", False):
                return ValidationResult(
                    allowed=False,
                    reason="REQUIRES_HUMAN_CONFIRMATION: High-impact or financial action detected.",
                    risk_level=RiskLevel.CRITICAL,
                    requires_confirmation=True
                )

        # 8. TYPE Specific Checks
        if action_name == "TYPE":
            text = action_json.get("text")
            if text is None:
                return ValidationResult(allowed=False, reason="TYPE action requires a 'text' parameter")

        return ValidationResult(
            allowed=True,
            reason="VALIDATION_PASSED",
            risk_level=risk,
            requires_confirmation=requires_confirmation
        )
