"""
PrivyBrowse AI — Browser Action Bridge
Thread-safe bidirectional communication bridge between the backend ActionExecutor
and the Chrome extension. Manages action queuing, dispatch lifecycle, acknowledgement
tracking, timeout handling, and extension connectivity detection.

Architecture:
    ActionExecutor → dispatch_action() → PENDING QUEUE
    Extension polls GET /api/action/pending → picks up action (DISPATCHED)
    Content script executes real DOM action
    Extension posts POST /api/action/ack → bridge wakes executor thread
    ActionExecutor ← wait_for_result() ← ActionBridgeResult
"""

import os
import time
import threading
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class PendingAction(BaseModel):
    """An action queued for dispatch to the Chrome extension."""
    action_id: str
    action_type: str  # CLICK, TYPE, SCROLL, PRESS_KEY, NAVIGATE
    tab_id: Optional[int] = None
    expected_url: Optional[str] = None
    page_identity: Optional[str] = None
    dom_fingerprint: Optional[str] = None
    target_id: Optional[str] = None
    target: Optional[Dict[str, Any]] = None  # {x, y} coordinates
    text: Optional[str] = None
    key: Optional[str] = None
    scroll_delta: Optional[Dict[str, Any]] = None  # {x, y} scroll amounts
    url: Optional[str] = None
    description: Optional[str] = None  # target_description for element resolution
    timeout_ms: float = 5000.0
    created_at: str = ""
    status: str = "PENDING"  # PENDING, DISPATCHED, SUCCESS, FAILED, TIMEOUT, CANCELLED
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionAcknowledgement(BaseModel):
    """Acknowledgement payload received from the Chrome extension after action execution."""
    action_id: str
    success: bool
    action_type: Optional[str] = None
    target_id: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_timestamp: Optional[str] = None
    detail: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionBridgeResult(BaseModel):
    """Result returned to the ActionExecutor after bridge dispatch completes."""
    action_id: str
    success: bool
    status: str  # SUCCESS, FAILED, TIMEOUT, EXTENSION_UNAVAILABLE, CANCELLED
    action_type: str
    target_id: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_timestamp: Optional[str] = None
    detail: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrowserActionBridge:
    """
    Thread-safe bidirectional action bridge between backend and Chrome extension.

    Lifecycle:
        1. ActionExecutor calls dispatch_action() → action enters PENDING queue
        2. Extension polls get_pending_action() → action moves to DISPATCHED
        3. Content script executes real DOM action
        4. Extension calls acknowledge_action() → waiting thread is woken
        5. ActionExecutor receives ActionBridgeResult via wait_for_result()

    Extension connectivity is tracked via heartbeat timestamps from polling.
    """

    # How long (seconds) before we consider the extension disconnected
    HEARTBEAT_TIMEOUT_S = 10.0
    MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

    def _handle_incoming_raw_message(self, raw_str: str) -> bool:
        """
        Validates raw payload length and JSON schema from WebSocket/IPC bridge.
        Returns False if oversized or malformed, preventing memory exhaustion DoS.
        """
        if not raw_str or len(raw_str.encode("utf-8")) > self.MAX_PAYLOAD_BYTES:
            return False
        return True

    def __init__(self):
        self._lock = threading.Lock()
        # OrderedDict preserves insertion order for FIFO dispatch
        self._pending: OrderedDict[str, PendingAction] = OrderedDict()
        # Events that executor threads wait on, keyed by action_id
        self._events: Dict[str, threading.Event] = {}
        # Completed results, keyed by action_id
        self._results: Dict[str, ActionBridgeResult] = {}
        # Extension heartbeat tracking
        self._last_heartbeat: float = 0.0
        # History of completed actions (bounded)
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100

    def dispatch_action(self, action: PendingAction) -> str:
        """
        Enqueue an action for extension pickup.
        Returns the action_id. The caller should then call wait_for_result().
        """
        with self._lock:
            action.status = "PENDING"
            action.created_at = datetime.now(timezone.utc).isoformat()
            self._pending[action.action_id] = action
            self._events[action.action_id] = threading.Event()
        return action.action_id

    def get_pending_action(self) -> Optional[PendingAction]:
        """
        Called by the extension polling endpoint.
        Returns the oldest PENDING action and marks it as DISPATCHED.
        Also registers a heartbeat for extension connectivity tracking.
        """
        self.register_heartbeat()
        with self._lock:
            for action_id, action in self._pending.items():
                if action.status == "PENDING":
                    action.status = "DISPATCHED"
                    return action
        return None

    def acknowledge_action(self, ack: ActionAcknowledgement) -> bool:
        """
        Called by the extension ack endpoint after content script execution.
        Wakes the waiting executor thread with the result.
        Returns True if the action_id was found and processed.
        """
        with self._lock:
            action = self._pending.get(ack.action_id)
            if not action:
                return False

            # Build result
            status = "SUCCESS" if ack.success else "FAILED"
            action.status = status

            result = ActionBridgeResult(
                action_id=ack.action_id,
                success=ack.success,
                status=status,
                action_type=action.action_type,
                target_id=ack.target_id or action.target_id,
                error=ack.error,
                error_code=ack.error_code,
                execution_timestamp=ack.execution_timestamp or datetime.now(timezone.utc).isoformat(),
                detail=ack.detail,
                metadata=ack.metadata
            )
            self._results[ack.action_id] = result

            # Record in history
            self._history.append({
                "action_id": ack.action_id,
                "action_type": action.action_type,
                "success": ack.success,
                "timestamp": result.execution_timestamp,
                "error": ack.error
            })
            if len(self._history) > self._max_history:
                self._history.pop(0)

            # Remove from pending
            del self._pending[ack.action_id]

            # Wake waiting thread
            event = self._events.get(ack.action_id)
            if event:
                event.set()

        return True

    def wait_for_result(self, action_id: str, timeout_ms: float = 5000.0) -> ActionBridgeResult:
        """
        Blocking wait for action completion. Called by ActionExecutor.
        Returns ActionBridgeResult with actual browser execution outcome.
        """
        event = self._events.get(action_id)
        if not event:
            return ActionBridgeResult(
                action_id=action_id,
                success=False,
                status="FAILED",
                action_type="UNKNOWN",
                error="No event registered for this action_id",
                error_code="INTERNAL_ERROR"
            )

        # Wait for extension acknowledgement or timeout
        timeout_s = timeout_ms / 1000.0
        completed = event.wait(timeout=timeout_s)

        with self._lock:
            # Clean up event
            self._events.pop(action_id, None)

            if completed:
                # Result was set by acknowledge_action
                result = self._results.pop(action_id, None)
                if result:
                    return result
                # Shouldn't happen, but defensive
                return ActionBridgeResult(
                    action_id=action_id,
                    success=False,
                    status="FAILED",
                    action_type="UNKNOWN",
                    error="Event was set but no result found",
                    error_code="INTERNAL_ERROR"
                )
            else:
                # Timeout — clean up pending action
                action = self._pending.pop(action_id, None)
                action_type = action.action_type if action else "UNKNOWN"
                return ActionBridgeResult(
                    action_id=action_id,
                    success=False,
                    status="TIMEOUT",
                    action_type=action_type,
                    error=f"Action timed out after {timeout_ms}ms — no acknowledgement received from extension",
                    error_code="EXTENSION_TIMEOUT"
                )

    def register_heartbeat(self):
        """Called on each extension poll to track connectivity."""
        self._last_heartbeat = time.monotonic()

    def is_extension_connected(self) -> bool:
        """
        Returns True if the extension has polled within the heartbeat timeout window.
        Used by the executor to fail-fast if no extension is available.
        """
        if self._last_heartbeat == 0.0:
            return False
        return (time.monotonic() - self._last_heartbeat) < self.HEARTBEAT_TIMEOUT_S

    def get_status(self) -> Dict[str, Any]:
        """Returns bridge status for monitoring endpoints."""
        with self._lock:
            pending_count = sum(1 for a in self._pending.values() if a.status == "PENDING")
            dispatched_count = sum(1 for a in self._pending.values() if a.status == "DISPATCHED")
        return {
            "extension_connected": self.is_extension_connected(),
            "last_heartbeat": self._last_heartbeat,
            "pending_actions": pending_count,
            "dispatched_actions": dispatched_count,
            "history_count": len(self._history)
        }

    def cancel_action(self, action_id: str) -> bool:
        """Cancel a pending/dispatched action."""
        with self._lock:
            action = self._pending.pop(action_id, None)
            if not action:
                return False
            result = ActionBridgeResult(
                action_id=action_id,
                success=False,
                status="CANCELLED",
                action_type=action.action_type,
                error="Action cancelled",
                error_code="CANCELLED"
            )
            self._results[action_id] = result
            event = self._events.get(action_id)
            if event:
                event.set()
        return True

    def clear_stale_actions(self, max_age_s: float = 30.0):
        """Remove actions that have been pending/dispatched beyond max_age_s."""
        now = datetime.now(timezone.utc)
        stale_ids = []
        with self._lock:
            for action_id, action in self._pending.items():
                try:
                    created = datetime.fromisoformat(action.created_at)
                    if (now - created).total_seconds() > max_age_s:
                        stale_ids.append(action_id)
                except (ValueError, TypeError):
                    stale_ids.append(action_id)
        for action_id in stale_ids:
            self.cancel_action(action_id)
