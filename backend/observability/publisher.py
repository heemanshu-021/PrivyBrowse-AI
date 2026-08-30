"""
Global Observability Event Publisher for PrivyBrowse-AI.
Provides centralized emission helpers for all system modules.
"""

from typing import Dict, Any, Optional
from backend.observability.schemas import (
    EventType, EventSeverity, EventComponent, ObservabilityEvent
)
from backend.observability.event_bus import global_event_bus


class EventPublisher:
    """
    Convenience wrapper over global_event_bus with module-specific helper methods.
    """

    def __init__(self, bus=global_event_bus):
        self.bus = bus

    def emit(
        self,
        event_type: EventType,
        component: EventComponent,
        message: str,
        severity: EventSeverity = EventSeverity.INFO,
        task_id: Optional[str] = None,
        step_id: Optional[str] = None,
        tab_id: Optional[int] = None,
        duration_ms: Optional[float] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ObservabilityEvent:
        return self.bus.publish(
            event_type=event_type,
            component=component,
            message=message,
            severity=severity,
            task_id=task_id,
            step_id=step_id,
            tab_id=tab_id,
            duration_ms=duration_ms,
            status=status,
            metadata=metadata
        )

    # Task Helpers
    def task_created(self, task_id: str, goal: str, steps_count: int, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.TASK_CREATED,
            component=EventComponent.TASK_MANAGER,
            message=f"Task '{task_id}' created with {steps_count} planned steps: {goal}",
            severity=EventSeverity.INFO,
            task_id=task_id,
            status="PLANNED",
            metadata={"goal": goal, "steps_count": steps_count, **(metadata or {})}
        )

    def task_step_started(self, task_id: str, step_id: str, description: str, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.TASK_STEP_STARTED,
            component=EventComponent.PLANNER,
            message=f"Step '{step_id}' started: {description}",
            severity=EventSeverity.INFO,
            task_id=task_id,
            step_id=step_id,
            status="RUNNING",
            metadata={"description": description, **(metadata or {})}
        )

    def task_step_completed(self, task_id: str, step_id: str, description: str, duration_ms: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.TASK_STEP_COMPLETED,
            component=EventComponent.PLANNER,
            message=f"Step '{step_id}' completed successfully: {description}",
            severity=EventSeverity.SUCCESS,
            task_id=task_id,
            step_id=step_id,
            duration_ms=duration_ms,
            status="COMPLETED",
            metadata={"description": description, **(metadata or {})}
        )

    def task_step_failed(self, task_id: str, step_id: str, reason: str, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.TASK_STEP_FAILED,
            component=EventComponent.PLANNER,
            message=f"Step '{step_id}' failed: {reason}",
            severity=EventSeverity.WARNING,
            task_id=task_id,
            step_id=step_id,
            status="FAILED",
            metadata={"reason": reason, **(metadata or {})}
        )

    def task_replanned(self, task_id: str, reason: str, remaining_steps_count: int, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.TASK_REPLANNED,
            component=EventComponent.PLANNER,
            message=f"Task '{task_id}' dynamically replanned ({remaining_steps_count} remaining steps): {reason}",
            severity=EventSeverity.WARNING,
            task_id=task_id,
            status="REPLANNED",
            metadata={"reason": reason, "remaining_steps": remaining_steps_count, **(metadata or {})}
        )

    def task_completed(self, task_id: str, goal: str, duration_ms: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.TASK_COMPLETED,
            component=EventComponent.TASK_MANAGER,
            message=f"Task '{task_id}' fully completed: {goal}",
            severity=EventSeverity.SUCCESS,
            task_id=task_id,
            duration_ms=duration_ms,
            status="COMPLETED",
            metadata={"goal": goal, **(metadata or {})}
        )

    def task_failed(self, task_id: str, reason: str, duration_ms: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.TASK_FAILED,
            component=EventComponent.TASK_MANAGER,
            message=f"Task '{task_id}' failed: {reason}",
            severity=EventSeverity.ERROR,
            task_id=task_id,
            duration_ms=duration_ms,
            status="FAILED",
            metadata={"reason": reason, **(metadata or {})}
        )

    # Browser Context Helpers
    def browser_context_updated(self, tab_id: Optional[int], url: str, title: str, element_count: int):
        return self.emit(
            event_type=EventType.BROWSER_CONTEXT_UPDATED,
            component=EventComponent.BROWSER_CONTEXT,
            message=f"Browser context synced: '{title}' ({url}) with {element_count} elements",
            severity=EventSeverity.INFO,
            tab_id=tab_id,
            metadata={"url": url, "title": title, "element_count": element_count}
        )

    def navigation_detected(self, tab_id: Optional[int], from_url: str, to_url: str):
        return self.emit(
            event_type=EventType.NAVIGATION_DETECTED,
            component=EventComponent.BROWSER_CONTEXT,
            message=f"Navigation detected on tab {tab_id}: {from_url} -> {to_url}",
            severity=EventSeverity.INFO,
            tab_id=tab_id,
            metadata={"from_url": from_url, "to_url": to_url}
        )

    def tab_changed(self, from_tab_id: Optional[int], to_tab_id: Optional[int], url: str):
        return self.emit(
            event_type=EventType.TAB_CHANGED,
            component=EventComponent.BROWSER_CONTEXT,
            message=f"Active browser tab changed: {from_tab_id} -> {to_tab_id} ({url})",
            severity=EventSeverity.INFO,
            tab_id=to_tab_id,
            metadata={"from_tab_id": from_tab_id, "to_tab_id": to_tab_id, "url": url}
        )

    # Perception Helpers
    def perception_completed(self, element_count: int, duration_ms: float, ocr_count: int = 0, cv_count: int = 0):
        return self.emit(
            event_type=EventType.PERCEPTION_COMPLETED,
            component=EventComponent.PERCEPTION,
            message=f"Perception completed: {element_count} fused elements (OCR: {ocr_count}, CV: {cv_count}) in {duration_ms:.1f}ms",
            severity=EventSeverity.SUCCESS,
            duration_ms=duration_ms,
            metadata={"element_count": element_count, "ocr_count": ocr_count, "cv_count": cv_count}
        )

    # Privacy Helpers
    def pii_detected(self, count: int, pii_types: list, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.PII_DETECTED,
            component=EventComponent.PRIVACY,
            message=f"Local PII scan detected {count} sensitive item(s): {', '.join(pii_types)}",
            severity=EventSeverity.WARNING,
            metadata={"detected_count": count, "pii_types": pii_types, **(metadata or {})}
        )

    def pii_redacted(self, count: int, style: str = "opaque", metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.PII_REDACTED,
            component=EventComponent.PRIVACY,
            message=f"Privacy Gate applied on-device redaction to {count} field(s) (style: {style})",
            severity=EventSeverity.SUCCESS,
            metadata={"redacted_count": count, "style": style, **(metadata or {})}
        )

    def privacy_blocked(self, reason: str, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.PRIVACY_BLOCKED,
            component=EventComponent.PRIVACY,
            message=f"Privacy policy blocked transmission: {reason}",
            severity=EventSeverity.ERROR,
            metadata={"reason": reason, **(metadata or {})}
        )

    # Security Helpers
    def prompt_injection_detected(self, threat_level: str, matched_patterns: list, metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.PROMPT_INJECTION_DETECTED,
            component=EventComponent.SECURITY,
            message=f"Adversarial prompt injection detected ({threat_level}): {len(matched_patterns)} pattern(s) neutralized",
            severity=EventSeverity.CRITICAL if threat_level == "HIGH_RISK" else EventSeverity.WARNING,
            metadata={"threat_level": threat_level, "patterns_count": len(matched_patterns), **(metadata or {})}
        )

    def security_blocked(self, reason: str, category: str = "SECURITY_VIOLATION", metadata: Optional[Dict[str, Any]] = None):
        return self.emit(
            event_type=EventType.SECURITY_BLOCKED,
            component=EventComponent.SECURITY,
            message=f"Security guard intercepted action: {reason}",
            severity=EventSeverity.ERROR,
            metadata={"reason": reason, "category": category, **(metadata or {})}
        )

    # Action & Verification Helpers
    def action_validated(self, action_type: str, target_id: Optional[str], risk_level: str, task_id: Optional[str] = None):
        return self.emit(
            event_type=EventType.ACTION_VALIDATED,
            component=EventComponent.ACTION_VALIDATOR,
            message=f"ActionValidator passed '{action_type}' on target '{target_id}' (Risk: {risk_level})",
            severity=EventSeverity.INFO,
            task_id=task_id,
            status="PASSED",
            metadata={"action_type": action_type, "target_id": target_id, "risk_level": risk_level}
        )

    def action_completed(self, action_type: str, target_id: Optional[str], duration_ms: float, task_id: Optional[str] = None):
        return self.emit(
            event_type=EventType.ACTION_COMPLETED,
            component=EventComponent.ACTION_EXECUTOR,
            message=f"Action '{action_type}' dispatched and executed on target '{target_id}' in {duration_ms:.1f}ms",
            severity=EventSeverity.SUCCESS,
            task_id=task_id,
            duration_ms=duration_ms,
            status="SUCCESS",
            metadata={"action_type": action_type, "target_id": target_id}
        )

    def action_verified(self, signal: str, evidence: list, task_id: Optional[str] = None):
        return self.emit(
            event_type=EventType.ACTION_VERIFIED,
            component=EventComponent.ACTION_VERIFIER,
            message=f"Action verified via signal '{signal}': {len(evidence)} state evidence point(s)",
            severity=EventSeverity.SUCCESS,
            task_id=task_id,
            status="VERIFIED",
            metadata={"signal": signal, "evidence": evidence}
        )

    def action_verification_failed(self, signal: str, reason: str, task_id: Optional[str] = None):
        return self.emit(
            event_type=EventType.ACTION_VERIFICATION_FAILED,
            component=EventComponent.ACTION_VERIFIER,
            message=f"Action verification failed ({signal}): {reason}",
            severity=EventSeverity.WARNING,
            task_id=task_id,
            status="FAILED",
            metadata={"signal": signal, "reason": reason}
        )

    def loop_detected(self, reason: str, task_id: Optional[str] = None):
        return self.emit(
            event_type=EventType.LOOP_DETECTED,
            component=EventComponent.RECOVERY,
            message=f"Action oscillation / repetitive loop detected: {reason}",
            severity=EventSeverity.ERROR,
            task_id=task_id,
            status="LOOP_DETECTED",
            metadata={"reason": reason}
        )

    def confirmation_required(self, action_type: str, target_id: Optional[str], reason: str, task_id: Optional[str] = None):
        return self.emit(
            event_type=EventType.CONFIRMATION_REQUIRED,
            component=EventComponent.ACTION_VALIDATOR,
            message=f"Human confirmation required before executing '{action_type}' on '{target_id}': {reason}",
            severity=EventSeverity.WARNING,
            task_id=task_id,
            status="AWAITING_CONFIRMATION",
            metadata={"action_type": action_type, "target_id": target_id, "reason": reason}
        )

    def recovery_triggered(self, failure_category: str, recommendation: str, task_id: Optional[str] = None):
        return self.emit(
            event_type=EventType.RECOVERY_TRIGGERED,
            component=EventComponent.RECOVERY,
            message=f"Failure recovery triggered for '{failure_category}': {recommendation}",
            severity=EventSeverity.WARNING,
            task_id=task_id,
            status="RECOVERING",
            metadata={"failure_category": failure_category, "recommendation": recommendation}
        )

    def system_heartbeat(self):
        return self.emit(
            event_type=EventType.HEALTH_HEARTBEAT,
            component=EventComponent.SYSTEM,
            message="System heartbeat tick",
            severity=EventSeverity.INFO
        )


# Global singleton publisher instance
global_event_publisher = EventPublisher()
