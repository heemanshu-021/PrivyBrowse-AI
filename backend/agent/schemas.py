"""
PrivyBrowse AI — Agent Schemas & Data Models
Strongly typed models for Agent State, Tasks, Objectives, Candidate Actions,
Planning Traces, Risk Classifications, and Verification Results.
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
    signal: str  # "PAGE_NAVIGATED", "DOM_UPDATED", "TARGET_FILLED", "NO_CHANGE", etc.
    details: str
    re_perception_required: bool = False


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
