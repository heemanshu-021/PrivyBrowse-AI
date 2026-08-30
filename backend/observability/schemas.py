"""
Observability and Event System Schemas for PrivyBrowse-AI.
Defines typed models for system events, severity levels, components, and telemetry snapshots.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class EventSeverity(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventComponent(str, Enum):
    TASK_MANAGER = "TASK_MANAGER"
    PLANNER = "PLANNER"
    AGENT_RUNNER = "AGENT_RUNNER"
    BROWSER_CONTEXT = "BROWSER_CONTEXT"
    PERCEPTION = "PERCEPTION"
    OCR = "OCR"
    PRIVACY = "PRIVACY"
    SECURITY = "SECURITY"
    ACTION_VALIDATOR = "ACTION_VALIDATOR"
    ACTION_EXECUTOR = "ACTION_EXECUTOR"
    ACTION_VERIFIER = "ACTION_VERIFIER"
    RECOVERY = "RECOVERY"
    EXTENSION = "EXTENSION"
    SYSTEM = "SYSTEM"


class EventType(str, Enum):
    # Task Lifecycle Events
    TASK_CREATED = "TASK_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_STEP_STARTED = "TASK_STEP_STARTED"
    TASK_STEP_COMPLETED = "TASK_STEP_COMPLETED"
    TASK_STEP_FAILED = "TASK_STEP_FAILED"
    TASK_REPLANNED = "TASK_REPLANNED"
    TASK_PAUSED = "TASK_PAUSED"
    TASK_RESUMED = "TASK_RESUMED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_CANCELLED = "TASK_CANCELLED"

    # Browser Context Events
    BROWSER_CONTEXT_UPDATED = "BROWSER_CONTEXT_UPDATED"
    NAVIGATION_DETECTED = "NAVIGATION_DETECTED"
    TAB_CHANGED = "TAB_CHANGED"
    TAB_CLOSED = "TAB_CLOSED"
    DOM_MUTATED = "DOM_MUTATED"
    SCROLL_UPDATED = "SCROLL_UPDATED"

    # Perception Events
    PERCEPTION_STARTED = "PERCEPTION_STARTED"
    PERCEPTION_COMPLETED = "PERCEPTION_COMPLETED"
    PERCEPTION_FAILED = "PERCEPTION_FAILED"
    OCR_STARTED = "OCR_STARTED"
    OCR_COMPLETED = "OCR_COMPLETED"
    OCR_FAILED = "OCR_FAILED"

    # Privacy Events
    PRIVACY_SCAN_STARTED = "PRIVACY_SCAN_STARTED"
    PII_DETECTED = "PII_DETECTED"
    PII_REDACTED = "PII_REDACTED"
    PRIVACY_BLOCKED = "PRIVACY_BLOCKED"

    # Security Events
    SECURITY_SCAN = "SECURITY_SCAN"
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    SUSPICIOUS_NAVIGATION = "SUSPICIOUS_NAVIGATION"
    DECEPTIVE_UI_DETECTED = "DECEPTIVE_UI_DETECTED"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"

    # Action & Verification Events
    ACTION_VALIDATED = "ACTION_VALIDATED"
    ACTION_REJECTED = "ACTION_REJECTED"
    ACTION_STARTED = "ACTION_STARTED"
    ACTION_COMPLETED = "ACTION_COMPLETED"
    ACTION_VERIFIED = "ACTION_VERIFIED"
    ACTION_VERIFICATION_FAILED = "ACTION_VERIFICATION_FAILED"

    # Recovery & Loop Events
    RECOVERY_TRIGGERED = "RECOVERY_TRIGGERED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    RECOVERY_COMPLETED = "RECOVERY_COMPLETED"
    LOOP_DETECTED = "LOOP_DETECTED"

    # Confirmation Events
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    CONFIRMATION_RECEIVED = "CONFIRMATION_RECEIVED"

    # System & Health Events
    HEALTH_HEARTBEAT = "HEALTH_HEARTBEAT"
    EXTENSION_CONNECTED = "EXTENSION_CONNECTED"
    EXTENSION_DISCONNECTED = "EXTENSION_DISCONNECTED"


class ObservabilityEvent(BaseModel):
    """
    Structured telemetry event emitted by core backend engines.
    Guaranteed clean of sensitive credentials, raw passwords, or private PII payloads.
    """
    seq_id: int = Field(..., description="Monotonically increasing sequence number")
    event_id: str = Field(..., description="Unique event identifier (e.g. evt-000123)")
    event_type: EventType = Field(..., description="High-level category of event")
    severity: EventSeverity = Field(default=EventSeverity.INFO, description="Event severity level")
    component: EventComponent = Field(..., description="Originating subsystem")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )
    task_id: Optional[str] = Field(None, description="Active task ID if associated")
    step_id: Optional[str] = Field(None, description="Active step ID if associated")
    tab_id: Optional[int] = Field(None, description="Active browser tab ID")
    message: str = Field(..., description="Safe human-readable summary")
    duration_ms: Optional[float] = Field(None, description="Execution duration in milliseconds")
    status: Optional[str] = Field(None, description="Execution or verification status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Sanitized structured metadata")

    def to_sse_payload(self) -> str:
        """Formats the event as an SSE data payload string."""
        return self.model_dump_json()


class SystemHealthStatus(BaseModel):
    """Real-time connectivity and health evaluation."""
    backend_healthy: bool = True
    extension_connected: bool = False
    browser_connected: bool = False
    event_stream_active: bool = True
    perception_available: bool = True
    ocr_available: bool = True
    last_heartbeat: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status_summary: str = "HEALTHY"


class DashboardSnapshot(BaseModel):
    """Complete aggregated snapshot for dashboard hydration."""
    health: SystemHealthStatus
    active_task: Optional[Dict[str, Any]] = None
    browser_context: Optional[Dict[str, Any]] = None
    agent_state: str = "IDLE"
    privacy_metrics: Dict[str, Any] = Field(default_factory=dict)
    security_metrics: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    recent_events: List[ObservabilityEvent] = Field(default_factory=list)
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
