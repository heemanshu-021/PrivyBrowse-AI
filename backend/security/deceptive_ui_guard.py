"""
PrivyBrowse AI — Deceptive UI & Exfiltration Guard
Detects deceptive UI mismatches (e.g. 'Cancel' buttons that execute deletions)
and untrusted external form credential/API key exfiltration endpoints.
"""

from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from backend.security.schemas import ThreatLevel, DeceptiveUIResult, SecurityEventType


class DeceptiveUIGuard:
    """
    Analyzes visual DOM element representations and interaction payloads
    to detect deceptive UI patterns, hidden element traps, and credential exfiltration.
    """

    BENIGN_LABELS = {"cancel", "close", "back", "dismiss", "no", "abort", "skip", "view", "details"}
    DESTRUCTIVE_KEYWORDS = {"delete", "destroy", "remove", "drop", "terminate", "wipe", "purge", "clear_all", "revoke", "format"}
    SENSITIVE_FIELD_NAMES = {"password", "pwd", "secret", "api_key", "apikey", "access_token", "token", "card_number", "cvv", "otp", "aadhaar", "pan"}

    @classmethod
    def analyze_element(
        cls,
        element: Dict[str, Any],
        current_url: str = ""
    ) -> DeceptiveUIResult:
        """
        Analyzes a single element for deceptive UI patterns or exfiltration risk.
        """
        if not element:
            return DeceptiveUIResult(is_deceptive=False, risk_level=ThreatLevel.NORMAL)

        el_id = element.get("id", "")
        visible_text = (element.get("text", "") or element.get("label", "") or "").lower().strip()
        attrs = element.get("attributes", {}) or {}

        # 1. Check Deceptive Button Mismatch (Benign text with destructive backend handler)
        # E.g. Text "Cancel" or "Close", but attributes indicate account deletion
        attr_blob = " ".join([
            str(attrs.get("class", "")),
            str(attrs.get("id", "")),
            str(attrs.get("name", "")),
            str(attrs.get("action", "")),
            str(attrs.get("formaction", "")),
            str(attrs.get("onclick", "")),
            str(attrs.get("data-action", ""))
        ]).lower()

        is_benign_label = any(b == visible_text or visible_text.startswith(b + " ") for b in cls.BENIGN_LABELS)
        has_destructive_handler = any(d in attr_blob for d in cls.DESTRUCTIVE_KEYWORDS)

        if is_benign_label and has_destructive_handler:
            return DeceptiveUIResult(
                is_deceptive=True,
                risk_level=ThreatLevel.CRITICAL,
                mismatch_type="LABEL_ACTION_MISMATCH",
                reason=f"Deceptive UI: Visible text is '{visible_text}', but element attributes indicate destructive action ({attr_blob[:60]})",
                action_type="DESTRUCTIVE_MISMATCH",
                target_id=el_id
            )

        # 2. Check Hidden / Zero-Sized / Obfuscated Element Trap
        is_hidden = False
        hidden_reason = ""

        if element.get("visibility") == "HIDDEN":
            is_hidden = True
            hidden_reason = "Element explicitly marked HIDDEN"
        elif attrs.get("hidden") is True or attrs.get("aria-hidden") == "true":
            is_hidden = True
            hidden_reason = "Element has hidden/aria-hidden attribute"
        elif "display:none" in str(attrs.get("style", "")).replace(" ", "").lower():
            is_hidden = True
            hidden_reason = "Element style display:none"
        elif "opacity:0" in str(attrs.get("style", "")).replace(" ", "").lower():
            is_hidden = True
            hidden_reason = "Element style opacity:0"

        bbox = element.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            if (x2 - x1) <= 0 or (y2 - y1) <= 0:
                is_hidden = True
                hidden_reason = f"Zero-sized element bounding box [{x1},{y1},{x2},{y2}]"

        if is_hidden:
            return DeceptiveUIResult(
                is_deceptive=True,
                risk_level=ThreatLevel.HIGH_RISK,
                mismatch_type="HIDDEN_ELEMENT_TRAP",
                reason=f"Hidden Element: {hidden_reason}",
                action_type="HIDDEN_INTERACTION",
                target_id=el_id
            )

        # 3. Check Sensitive Form Exfiltration to External Endpoint
        # E.g. Form contains password/api_key input, and submits to a third-party domain
        form_action = str(attrs.get("formaction", attrs.get("action", "")))
        el_type = str(element.get("type", "")).lower()
        el_name = str(attrs.get("name", attrs.get("id", ""))).lower()

        if form_action and current_url:
            curr_host = urlparse(current_url).netloc.lower()
            action_host = urlparse(form_action).netloc.lower()
            if action_host and action_host != curr_host:
                if any(s in el_name for s in cls.SENSITIVE_FIELD_NAMES) or el_type == "password":
                    return DeceptiveUIResult(
                        is_deceptive=True,
                        risk_level=ThreatLevel.CRITICAL,
                        mismatch_type="EXFILTRATION_FORM",
                        reason=f"Exfiltration Risk: Sensitive credential field '{el_name}' submits to external host '{action_host}'",
                        action_type="DATA_EXFILTRATION",
                        target_id=el_id
                    )

        return DeceptiveUIResult(is_deceptive=False, risk_level=ThreatLevel.NORMAL)
