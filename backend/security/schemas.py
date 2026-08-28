"""
PrivyBrowse AI — Security & Adversarial Defense Schemas
Data models for trust boundary definitions, threat classifications,
prompt injection detections, and audit log records.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TrustLevel(str, Enum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"


class ThreatLevel(str, Enum):
    NORMAL = "NORMAL"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"


class SecurityEventType(str, Enum):
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    UNTRUSTED_ACTION_BLOCKED = "UNTRUSTED_ACTION_BLOCKED"
    RAW_CONTEXT_BLOCKED = "RAW_CONTEXT_BLOCKED"
    HIGH_RISK_ACTION_BLOCKED = "HIGH_RISK_ACTION_BLOCKED"
    STALE_TARGET_DETECTED = "STALE_TARGET_DETECTED"
    SUSPICIOUS_NAVIGATION_BLOCKED = "SUSPICIOUS_NAVIGATION_BLOCKED"
    RESOURCE_LIMIT_REACHED = "RESOURCE_LIMIT_REACHED"
    SECRET_LEAK_DETECTED = "SECRET_LEAK_DETECTED"
    RACE_CONDITION_DETECTED = "RACE_CONDITION_DETECTED"


class SecurityEvent(BaseModel):
    """Immutable, zero-leak security event record."""
    event_id: str
    event_type: SecurityEventType
    threat_level: ThreatLevel
    timestamp: str
    description: str
    target_id: Optional[str] = None
    blocked_url: Optional[str] = None
    mitigation_action: str = "BLOCKED"
    details: Dict[str, Any] = Field(default_factory=dict)


class PromptInjectionScanResult(BaseModel):
    has_injection: bool = False
    threat_level: ThreatLevel = ThreatLevel.NORMAL
    matched_patterns: List[str] = Field(default_factory=list)
    sanitized_text: str = ""
    original_length: int = 0
    sanitized_length: int = 0


class SecretScanResult(BaseModel):
    clean: bool = True
    files_scanned: int = 0
    secrets_found_count: int = 0
    findings: List[Dict[str, Any]] = Field(default_factory=list)
