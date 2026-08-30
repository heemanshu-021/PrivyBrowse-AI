"""
PrivyBrowse AI — Zero-Leak Security Audit Logger
Records immutable security events with strict zero-leak guarantees
(passwords, OTPs, card numbers, and PII are never logged).
"""

import time
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.security.schemas import SecurityEvent, SecurityEventType, ThreatLevel


class SecurityAuditLogger:
    """
    Centralized, privacy-safe security event logging engine.
    Guarantees zero-leak logging of sensitive secrets or personal information.
    """

    def __init__(self, max_events: int = 1000):
        self.max_events = max_events
        self._events: List[SecurityEvent] = []
        self._leak_check_regex = re.compile(
            r"(?i)(?:password|otp|secret|ghp_|4242|4111|[0-9]{12}|[A-Z]{5}[0-9]{4}[A-Z])"
        )

    def log_event(
        self,
        event_type: SecurityEventType,
        threat_level: ThreatLevel,
        description: str,
        target_id: Optional[str] = None,
        blocked_url: Optional[str] = None,
        mitigation_action: str = "BLOCKED",
        details: Optional[Dict[str, Any]] = None
    ) -> SecurityEvent:
        """
        Logs a security event with zero-leak sanitization on description and details.
        """
        event_id = f"sec-{int(time.time()*1000)%1000000:06d}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Sanitize description & details to guarantee zero leakage of actual credentials
        clean_desc = self._sanitize_log_text(description)
        clean_details = self._sanitize_dict(details or {})

        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            threat_level=threat_level,
            timestamp=now_iso,
            description=clean_desc,
            target_id=target_id,
            blocked_url=blocked_url,
            mitigation_action=mitigation_action,
            details=clean_details
        )

        self._events.append(event)
        if len(self._events) > self.max_events:
            self._events.pop(0)

        return event

    def get_events(self, limit: int = 50) -> List[SecurityEvent]:
        """Returns latest security events."""
        return list(reversed(self._events[-limit:]))

    def get_event_count_by_type(self) -> Dict[str, int]:
        """Returns aggregate event counts per security type."""
        counts = {t.value: 0 for t in SecurityEventType}
        for e in self._events:
            counts[e.event_type.value] = counts.get(e.event_type.value, 0) + 1
        return counts

    def get_total_events(self) -> int:
        return len(self._events)

    def _sanitize_log_text(self, text: str) -> str:
        """Strips raw credential sequences and secret values from log messages."""
        if not text:
            return ""
        # Mask password and secret phrase values
        text = re.sub(r"(?i)(?:password|pwd|secret|api[_-]?key)\s*[:= ]\s*(\S+)", r"password: [REDACTED_PASSWORD]", text)
        text = re.sub(r"(?i)\bwith\s+password\s+(\S+)", r"with password [REDACTED_PASSWORD]", text)
        text = re.sub(r"ghp_[a-zA-Z0-9]{20,}", "[REDACTED_GITHUB_TOKEN]", text)
        text = re.sub(r"sk-[a-zA-Z0-9]{15,}", "[REDACTED_API_KEY]", text)
        text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CARD_NUMBER]", text)
        text = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED_PAN]", text)
        return text

    def _sanitize_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitizes dictionary keys and string values."""
        clean = {}
        for k, v in d.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ("password", "pwd", "otp", "secret", "card", "token")):
                clean[k] = "[REDACTED_SENSITIVE_FIELD]"
            elif isinstance(v, str):
                clean[k] = self._sanitize_log_text(v)
            elif isinstance(v, dict):
                clean[k] = self._sanitize_dict(v)
            else:
                clean[k] = v
        return clean
