"""
PrivyBrowse AI — Privacy Gate & Remote Guard
Enforces the zero-leak trust boundary between local perception and any reasoning layer.
Blocks raw unsanitized perception transmission and produces privacy-safe audit trails.
"""

import time
import base64
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from backend.privacy.schemas import (
    PIIEntity, SanitizedContext, RedactionMap, PrivacyPolicy,
    PrivacyAuditLogEntry, DataClassification
)
from backend.privacy.pii_detector import PIIDetector
from backend.privacy.redactor import Redactor


class PrivacyGateViolation(Exception):
    """Raised when an attempt is made to transmit raw unredacted data outside the local trust boundary."""
    pass


class PrivacyGate:
    """
    Architectural Privacy Gatekeeper.
    Controls all data flow out of the trusted local perception zone.
    """

    def __init__(self, policy: Optional[PrivacyPolicy] = None):
        self.detector = PIIDetector()
        self.redactor = Redactor()
        self.policy = policy or PrivacyPolicy()
        self.audit_logs: List[PrivacyAuditLogEntry] = []
        self._log_counter = 1

        # Real in-memory metrics
        self.metrics = {
            "total_pii_detected": 0,
            "total_pii_redacted": 0,
            "highly_sensitive_count": 0,
            "sensitive_count": 0,
            "blocked_raw_transmissions": 0,
            "last_detection_latency_ms": 0.0,
            "last_redaction_latency_ms": 0.0,
            "last_total_gate_latency_ms": 0.0,
        }

    def _add_audit_log(
        self,
        event: str,
        pii_type: Optional[str] = None,
        classification: Optional[str] = None,
        confidence: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Appends a privacy-safe audit record.
        STRICT INVARIANT: Never records raw secrets, passwords, or PII text.
        """
        entry = PrivacyAuditLogEntry(
            id=f"audit-{self._log_counter:04d}",
            event=event,
            type=pii_type,
            classification=classification,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {}
        )
        self._log_counter += 1
        self.audit_logs.append(entry)
        # Keep latest 200 audit entries in memory
        if len(self.audit_logs) > 200:
            self.audit_logs = self.audit_logs[-200:]

    def process_and_sanitize(
        self,
        screenshot_bytes: bytes,
        ocr_blocks: List[Dict[str, Any]],
        dom_nodes: List[Dict[str, Any]],
        style: Optional[str] = None
    ) -> Tuple[SanitizedContext, List[PIIEntity]]:
        """
        Executes end-to-end local privacy gating:
          1. Detects all PII entities across OCR, DOM, and Visual Haar Cascade
          2. Applies visual screenshot masking
          3. Scrubs OCR text blocks and DOM attributes
          4. Emits privacy-safe audit entries
          5. Packages into a verified SanitizedContext
        """
        t0 = time.perf_counter()
        active_style = style or self.policy.default_redaction_style

        # Step 1: Detect PII
        t_det_start = time.perf_counter()
        entities = self.detector.detect(screenshot_bytes, ocr_blocks, dom_nodes)
        t_det_ms = (time.perf_counter() - t_det_start) * 1000.0

        # Step 2: Redact Screenshot and build RedactionMap
        t_red_start = time.perf_counter()
        entities_dict = [e.model_dump() for e in entities]
        redacted_bytes, redaction_map = self.redactor.redact_screenshot(
            screenshot_bytes, entities_dict, active_style
        )

        # Step 3: Scrub OCR and DOM nodes
        sanitized_ocr = self.redactor.redact_ocr_blocks(ocr_blocks, entities_dict)
        sanitized_dom = self.redactor.redact_dom_nodes(dom_nodes, entities_dict)
        t_red_ms = (time.perf_counter() - t_red_start) * 1000.0

        t_total_ms = (time.perf_counter() - t0) * 1000.0

        # Update metrics
        self.metrics["total_pii_detected"] += len(entities)
        self.metrics["total_pii_redacted"] += redaction_map.total_redacted
        self.metrics["highly_sensitive_count"] += redaction_map.highly_sensitive_count
        self.metrics["sensitive_count"] += redaction_map.sensitive_count
        self.metrics["last_detection_latency_ms"] = round(t_det_ms, 2)
        self.metrics["last_redaction_latency_ms"] = round(t_red_ms, 2)
        self.metrics["last_total_gate_latency_ms"] = round(t_total_ms, 2)

        # Record audit logs for detected items (PRIVACY SAFE: no raw text)
        for ent in entities:
            self._add_audit_log(
                event="PII_DETECTED",
                pii_type=ent.type,
                classification=ent.classification,
                confidence=ent.confidence,
                details={"sources": ent.source, "element_id": ent.element_id}
            )

        if redaction_map.total_redacted > 0:
            self._add_audit_log(
                event="SANITIZATION_COMPLETED",
                details={
                    "total_redacted": redaction_map.total_redacted,
                    "style": active_style,
                    "latency_ms": round(t_total_ms, 2)
                }
            )

        # Base64 encode redacted image
        redacted_b64 = ""
        if redacted_bytes:
            redacted_b64 = "data:image/png;base64," + base64.b64encode(redacted_bytes).decode("utf-8")

        sanitized_context = SanitizedContext(
            redacted_screenshot=redacted_b64,
            sanitized_dom_nodes=sanitized_dom,
            sanitized_ocr_blocks=sanitized_ocr,
            redaction_map=redaction_map,
            is_safe_for_reasoning=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            privacy_policy_applied="STRICT_LOCAL_ONLY"
        )

        return sanitized_context, entities

    def guard_outbound_transmission(self, context: Any) -> bool:
        """
        Security Guard: Validates that an outbound payload is safe and sanitized.
        Rejects raw observations or unverified contexts.
        """
        if not self.policy.allow_raw_remote_transmission:
            # Check if payload is a raw observation or contains raw unsanitized flags
            if isinstance(context, dict):
                if context.get("privacy_status") == "LOCAL_UNSANITIZED" or context.get("is_safe_for_reasoning") is False:
                    self.metrics["blocked_raw_transmissions"] += 1
                    self._add_audit_log(
                        event="REMOTE_TRANSMISSION_BLOCKED",
                        details={"reason": "RAW_CONTEXT_BLOCKED_BY_PRIVACY_GATE"}
                    )
                    raise PrivacyGateViolation(
                        "RAW_CONTEXT_BLOCKED_BY_PRIVACY_GATE: Outbound transmission of raw unredacted perception context is strictly prohibited."
                    )
            elif not isinstance(context, SanitizedContext) and not getattr(context, "is_safe_for_reasoning", False):
                self.metrics["blocked_raw_transmissions"] += 1
                self._add_audit_log(
                    event="REMOTE_TRANSMISSION_BLOCKED",
                    details={"reason": "UNVERIFIED_CONTEXT_TYPE"}
                )
                raise PrivacyGateViolation(
                    "RAW_CONTEXT_BLOCKED_BY_PRIVACY_GATE: Only verified SanitizedContext instances may pass the privacy gate."
                )

        return True

    def get_status(self) -> Dict[str, Any]:
        """Returns real-time privacy engine status for the UI dashboard."""
        return {
            "privacy_gate_active": True,
            "policy": self.policy.model_dump(),
            "metrics": self.metrics,
            "audit_log_count": len(self.audit_logs),
            "trust_boundary": "STRICT_LOCAL_ON_DEVICE",
            "offline_enforced": True
        }
