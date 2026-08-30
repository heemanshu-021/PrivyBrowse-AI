"""
PrivyBrowse AI — Agent Schemas & Data Models
Strongly typed models for Agent State, Tasks, Objectives, Candidate Actions,
Planning Traces, Risk Classifications, and Evidence-Based Verification Results.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    IDLE = "IDLE"
    OBSERVING = "OBSERVING"
    PERCEIVING = "PERCEIVING"
    UNDERSTANDING = "UNDERSTANDING"
    PLANNING = "PLANNING"
    VALIDATING = "VALIDATING"
    ACTING = "ACTING"
    VERIFYING = "VERIFYING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


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


class Objective(BaseModel):
    """A sub-goal within a decomposed task."""
    id: str
    description: str
    target_type: Optional[str] = None  # INPUT, BUTTON, LINK, etc.
    semantic_intent: str = ""          # "search_query", "submit_form", "select_result", etc.
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    success_criteria: str = ""
    target_keywords: List[str] = Field(default_factory=list)
    completed_at: Optional[str] = None


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
    max_retries_per_objective: int = 3
    timeout_seconds: float = 60.0
    require_confirmation_for_sensitive: bool = True
    allow_financial_actions: bool = False


class AgentTask(BaseModel):
    """Structured high-level browser automation task."""
    task_id: str
    goal: str
    status: AgentState = AgentState.IDLE
    created_at: str = ""
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)
    objectives: List[Objective] = Field(default_factory=list)
    current_objective_index: int = 0
    actions_executed: int = 0
    trace: List[PlanTraceEntry] = Field(default_factory=list)
    is_paused: bool = False
    last_error: Optional[str] = None
