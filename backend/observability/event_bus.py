"""
In-Memory Thread-Safe Event Bus for PrivyBrowse-AI Observability.
Provides bounded event storage (ring buffer), monotonic sequence ordering,
strict PII/credential sanitization, and pub/sub queues for SSE streaming.
"""

import re
import time
import asyncio
import threading
from typing import List, Dict, Any, Optional, Set
from collections import deque
from datetime import datetime, timezone

from backend.observability.schemas import (
    ObservabilityEvent, EventType, EventSeverity, EventComponent
)

# Sensitive patterns that must never appear in event metadata or messages
SENSITIVE_KEY_PATTERNS = {
    "password", "passwd", "pwd", "secret", "token", "auth", "credential",
    "api_key", "apikey", "card_number", "cvv", "pan_number", "aadhaar", "ssn"
}

SECRET_VALUE_REGEXES = [
    (re.compile(r"sk-(?:proj-)?[a-zA-Z0-9_\-]{12,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"ghp_[a-zA-Z0-9_\-]{16,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"), "[REDACTED_PAN]"),
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[REDACTED_CARD]"),
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[REDACTED_AADHAAR]"),
]


def sanitize_value(val: Any) -> Any:
    """Recursively sanitizes values, masking potential credentials and PII."""
    if isinstance(val, str):
        masked = val
        for regex, tag in SECRET_VALUE_REGEXES:
            masked = regex.sub(tag, masked)
        return masked
    elif isinstance(val, dict):
        sanitized = {}
        for k, v in val.items():
            k_lower = str(k).lower()
            if any(p in k_lower for p in SENSITIVE_KEY_PATTERNS):
                sanitized[k] = "[REDACTED_CREDENTIAL]"
            else:
                sanitized[k] = sanitize_value(v)
        return sanitized
    elif isinstance(val, (list, tuple, set)):
        return [sanitize_value(item) for item in val]
    return val


class ObservabilityEventBus:
    """
    High-performance, offline-first, in-memory event bus.
    Guarantees bounded memory consumption, sequence preservation, and thread safety.
    """

    def __init__(self, max_retention: int = 500):
        self._max_retention = max_retention
        self._events: deque = deque(maxlen=max_retention)
        self._seq_counter = 0
        self._lock = threading.Lock()
        self._async_subscribers: Set[asyncio.Queue] = set()

    def publish(
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
        """
        Publishes a new telemetry event into the ring buffer and notifies active SSE subscribers.
        """
        with self._lock:
            self._seq_counter += 1
            seq = self._seq_counter
            evt_id = f"evt-{seq:06d}"

            # Strictly sanitize message and metadata
            clean_msg = sanitize_value(message)
            clean_meta = sanitize_value(metadata or {})

            event = ObservabilityEvent(
                seq_id=seq,
                event_id=evt_id,
                event_type=event_type,
                severity=severity,
                component=component,
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_id=task_id,
                step_id=step_id,
                tab_id=tab_id,
                message=clean_msg,
                duration_ms=round(duration_ms, 2) if duration_ms is not None else None,
                status=status,
                metadata=clean_meta
            )

            self._events.append(event)

        # Notify active SSE subscribers asynchronously
        if self._async_subscribers:
            for q in list(self._async_subscribers):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass
                except Exception:
                    self._async_subscribers.discard(q)

        return event

    def get_events(
        self,
        limit: int = 100,
        since_seq: Optional[int] = None,
        component: Optional[EventComponent] = None,
        severity: Optional[EventSeverity] = None,
        task_id: Optional[str] = None
    ) -> List[ObservabilityEvent]:
        """
        Queries events from the ring buffer with optional filtering and sequence pagination.
        """
        with self._lock:
            items = list(self._events)

        # Filter by since_seq
        if since_seq is not None:
            items = [e for e in items if e.seq_id > since_seq]

        # Filter by component
        if component is not None:
            items = [e for e in items if e.component == component]

        # Filter by severity
        if severity is not None:
            items = [e for e in items if e.severity == severity]

        # Filter by task_id
        if task_id is not None:
            items = [e for e in items if e.task_id == task_id]

        # Return latest up to limit
        return items[-limit:]

    def get_latest_event(self) -> Optional[ObservabilityEvent]:
        """Returns the most recent event or None."""
        with self._lock:
            return self._events[-1] if self._events else None

    def get_total_events_count(self) -> int:
        """Returns total historical published count."""
        with self._lock:
            return self._seq_counter

    def subscribe_async(self, queue: asyncio.Queue):
        """Registers an asyncio queue for live SSE event streaming."""
        self._async_subscribers.add(queue)

    def unsubscribe_async(self, queue: asyncio.Queue):
        """Unregisters an asyncio queue."""
        self._async_subscribers.discard(queue)

    def clear(self):
        """Resets the event bus (primarily for test isolation)."""
        with self._lock:
            self._events.clear()
            self._seq_counter = 0


# Global singleton event bus instance
global_event_bus = ObservabilityEventBus()
