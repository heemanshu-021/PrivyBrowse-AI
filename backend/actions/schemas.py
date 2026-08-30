"""
PrivyBrowse AI — Action Execution Schemas & Models
Strongly typed models for real browser action execution payloads, results,
page mutation signals, and execution safety configurations.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    TIMEOUT = "TIMEOUT"
    STALE_TARGET = "STALE_TARGET"
    EXTENSION_UNAVAILABLE = "EXTENSION_UNAVAILABLE"
    EXTENSION_TIMEOUT = "EXTENSION_TIMEOUT"


class SupportedKey(str, Enum):
    ENTER = "Enter"
    TAB = "Tab"
    ESCAPE = "Escape"
    ARROW_DOWN = "ArrowDown"
    ARROW_UP = "ArrowUp"
    ARROW_LEFT = "ArrowLeft"
    ARROW_RIGHT = "ArrowRight"
    BACKSPACE = "Backspace"
    SPACE = "Space"


class ActionError(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ActionResult(BaseModel):
    """Standardized response from executing a real browser action."""
    success: bool
    action_id: str
    action: str
    target_id: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: str
    page_changed: bool = False
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    error: Optional[ActionError] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PageChangeSignal(BaseModel):
    """Detection of webpage state change following an action."""
    page_changed: bool
    url_changed: bool = False
    dom_mutated: bool = False
    scroll_changed: bool = False
    previous_url: str = ""
    current_url: str = ""
    change_summary: str = ""


class ExecutionConfig(BaseModel):
    """Safety and timing configuration for the browser action executor."""
    max_action_timeout_ms: float = 5000.0
    scroll_step_px: int = 400
    stabilization_wait_ms: float = 150.0
    allowed_url_schemes: List[str] = Field(default_factory=lambda: ["http", "https", "file", "/demo"])
    enforce_safe_keys_only: bool = True
    screen_width: int = 1920
    screen_height: int = 1080
