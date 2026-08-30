"""
PrivyBrowse AI — Agent Schemas & Data Models
Strongly typed models for Agent State, Tasks, Task Steps, Candidate Actions,
Planning Traces, Risk Classifications, and Evidence-Based Verification Results.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    IDLE = "IDLE"
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    OBSERVING = "OBSERVING"
    PERCEIVING = "PERCEIVING"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    VALIDATING = "VALIDATING"
    ACTING = "ACTING"
    VERIFYING = "VERIFYING"
    WAITING = "WAITING"
    RECOVERING = "RECOVERING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# TaskState alias mapped to AgentState for semantic clarity
TaskState = AgentState


class ActionType(str, Enum):
    CLICK = "CLICK"
    TYPE = "TYPE"
    SCROLL = "SCROLL"
    PRESS_KEY = "PRESS_KEY"
    NAVIGATE = "NAVIGATE"
    WAIT = "WAIT"
    FINISH = "FINISH"


class ObjectiveStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"


StepStatus = ObjectiveStatus


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VerificationStatus(str, Enum):
    ACTION_VERIFIED = "ACTION_VERIFIED"
    NO_STATE_CHANGE = "NO_STATE_CHANGE"
    UNVERIFIED = "UNVERIFIED"
    FAILED = "FAILED"
    STALE_TARGET = "STALE_TARGET"
    SCROLL_BOUNDARY = "SCROLL_BOUNDARY"


class FailureCategory(str, Enum):
    TARGET_NOT_FOUND = "TARGET_NOT_FOUND"
    TARGET_STALE = "TARGET_STALE"
    NO_STATE_CHANGE = "NO_STATE_CHANGE"
    UNEXPECTED_NAVIGATION = "UNEXPECTED_NAVIGATION"
    EXTENSION_DISCONNECTED = "EXTENSION_DISCONNECTED"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    PRIVACY_BLOCK = "PRIVACY_BLOCK"
    ACTION_TIMEOUT = "ACTION_TIMEOUT"
    LOOP_DETECTED = "LOOP_DETECTED"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


class RecoveryRecommendation(str, Enum):
    PROCEED = "PROCEED"
    REPERCEIVE = "REPERCEIVE"
    RETRY_ALTERNATIVE = "RETRY_ALTERNATIVE"
    REBUILD_CONTEXT = "REBUILD_CONTEXT"
    REQUEST_CONFIRMATION = "REQUEST_CONFIRMATION"
    SAFE_STOP = "SAFE_STOP"


class TaskStep(BaseModel):
    """A single sub-goal or step within a multi-step task."""
    id: str
    description: str
    target_type: Optional[str] = None  # INPUT, BUTTON, LINK, etc.
    semantic_intent: str = ""          # "search_input", "submit_search", "select_result", etc.
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    success_criteria: str = ""
    target_keywords: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)  # step_ids that must complete first
    required_browser_state: Optional[Dict[str, Any]] = None
    expected_result: str = ""
    candidate_action: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    failure_reason: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    completed_at: Optional[str] = None


# Backward-compatibility alias
Objective = TaskStep


class CandidateAction(BaseModel):
    """A scored potential action considered by the planner."""
    action: ActionType
    target_id: Optional[str] = None
    target: Optional[Dict[str, float]] = None  # {"x": float, "y": float}
    target_description: str = ""
    text: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    score: float = 0.0
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    reason: str = ""


class ExpectedState(BaseModel):
    """Anticipated browser state changes after action execution."""
    action_type: str = "CLICK"
    target_id: Optional[str] = None
    expected_url_pattern: Optional[str] = None
    expected_dom_mutation: bool = False
    expected_value_populated: bool = False
    expected_scroll_delta: Optional[Dict[str, float]] = None
    expected_element_appear: Optional[str] = None
    expected_element_disappear: Optional[str] = None
    is_sensitive: bool = False
    allow_boundary_stop: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Result of safety and policy validation before executing an action."""
    allowed: bool
    reason: str
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    """Outcome verification after an action has been executed."""
    success: bool
    signal: str  # "PAGE_NAVIGATED", "DOM_MUTATION_DETECTED", "INPUT_VALUE_UPDATED", "NO_CHANGE", etc.
    details: str
    status: VerificationStatus = VerificationStatus.ACTION_VERIFIED
    evidence: List[str] = Field(default_factory=list)
    failure_category: Optional[FailureCategory] = None
    recovery_recommendation: RecoveryRecommendation = RecoveryRecommendation.PROCEED
    re_perception_required: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PlanTraceEntry(BaseModel):
    """Explainable step trace for transparency, evaluation, and judges."""
    step: int
    timestamp: str
    goal: str
    current_objective: str
    observation_summary: str
    candidate_actions_count: int
    selected_action: Optional[Dict[str, Any]] = None
    validation: Optional[ValidationResult] = None
    verification: Optional[VerificationResult] = None
    state: AgentState


class TaskConstraints(BaseModel):
    """Guardrail constraints to prevent runaway agent loops."""
    max_actions: int = 15
    max_retries_per_step: int = 2
    max_retries_per_objective: int = 2
    max_replans: int = 3
    timeout_seconds: float = 60.0
    require_confirmation_for_sensitive: bool = True
    allow_financial_actions: bool = False


class AgentTask(BaseModel):
    """Structured high-level browser automation task."""
    task_id: str
    goal: str
    status: AgentState = AgentState.PLANNED
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)
    steps: List[TaskStep] = Field(default_factory=list)
    current_step_index: int = 0
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    failed_steps: List[str] = Field(default_factory=list)
    retry_count: int = 0
    replan_count: int = 0
    current_context: Optional[Dict[str, Any]] = None
    task_progress: float = 0.0
    task_result: Optional[Dict[str, Any]] = None
    failure_reason: Optional[str] = None
    actions_executed: int = 0
    trace: List[PlanTraceEntry] = Field(default_factory=list)
    is_paused: bool = False
    last_error: Optional[str] = None

    # Backward compatibility properties
    @property
    def objectives(self) -> List[TaskStep]:
        return self.steps

    @objectives.setter
    def objectives(self, val: List[TaskStep]):
        self.steps = val

    @property
    def current_objective_index(self) -> int:
        return self.current_step_index

    @current_objective_index.setter
    def current_objective_index(self, val: int):
        self.current_step_index = val


class TaskResult(BaseModel):
    """Structured final output returned upon task completion, interruption, or termination."""
    status: str
    task_id: str
    goal: str
    turns_executed: int
    completed_steps: List[str] = Field(default_factory=list)
    remaining_steps: List[str] = Field(default_factory=list)
    final_context: Dict[str, Any] = Field(default_factory=dict)
    result: Dict[str, Any] = Field(default_factory=dict)
    failure_reason: Optional[str] = None
    security_events: List[Dict[str, Any]] = Field(default_factory=list)
    confirmation_events: List[Dict[str, Any]] = Field(default_factory=list)
    total_latency_ms: float = 0.0
