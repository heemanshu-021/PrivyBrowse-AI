"""
PrivyBrowse AI — Security & Adversarial Defense Schemas
Data models for trust boundary definitions, threat classifications,
prompt injection detections, deceptive UI, link safety, and audit log records.
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
    INDIRECT_INJECTION_DETECTED = "INDIRECT_INJECTION_DETECTED"
    UNTRUSTED_INSTRUCTION = "UNTRUSTED_INSTRUCTION"
    UNTRUSTED_ACTION_BLOCKED = "UNTRUSTED_ACTION_BLOCKED"
    RAW_CONTEXT_BLOCKED = "RAW_CONTEXT_BLOCKED"
    HIGH_RISK_ACTION_BLOCKED = "HIGH_RISK_ACTION_BLOCKED"
    STALE_TARGET_DETECTED = "STALE_TARGET_DETECTED"
    STALE_SECURITY_CONTEXT = "STALE_SECURITY_CONTEXT"
    SUSPICIOUS_NAVIGATION_BLOCKED = "SUSPICIOUS_NAVIGATION_BLOCKED"
    UNSAFE_EXTERNAL_DOMAIN = "UNSAFE_EXTERNAL_DOMAIN"
    PROTOCOL_DOWNGRADE_BLOCKED = "PROTOCOL_DOWNGRADE_BLOCKED"
    DECEPTIVE_UI_DETECTED = "DECEPTIVE_UI_DETECTED"
    DECEPTIVE_LINK_DETECTED = "DECEPTIVE_LINK_DETECTED"
    HIDDEN_ELEMENT_BLOCKED = "HIDDEN_ELEMENT_BLOCKED"
    HIDDEN_INJECTION_BLOCKED = "HIDDEN_INJECTION_BLOCKED"
    SENSITIVE_DATA_EXFILTRATION_ATTEMPT = "SENSITIVE_DATA_EXFILTRATION_ATTEMPT"
    DATA_EXFILTRATION_BLOCKED = "DATA_EXFILTRATION_BLOCKED"
    REPLAY_ATTACK_BLOCKED = "REPLAY_ATTACK_BLOCKED"
    FORGED_CONFIRMATION_BLOCKED = "FORGED_CONFIRMATION_BLOCKED"
    SSRF_BLOCKED = "SSRF_BLOCKED"
    COMMAND_INJECTION_BLOCKED = "COMMAND_INJECTION_BLOCKED"
    PATH_TRAVERSAL_BLOCKED = "PATH_TRAVERSAL_BLOCKED"
    RESOURCE_LIMIT_REACHED = "RESOURCE_LIMIT_REACHED"
    SECRET_LEAK_DETECTED = "SECRET_LEAK_DETECTED"
    RACE_CONDITION_DETECTED = "RACE_CONDITION_DETECTED"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"


class ActionAuthorizationSource(str, Enum):
    USER_DIRECTED = "USER_DIRECTED"
    POLICY_VERIFIED = "POLICY_VERIFIED"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"
    UNTRUSTED_CLIENT_CLAIM = "UNTRUSTED_CLIENT_CLAIM"
    REJECTED_FORGERY = "REJECTED_FORGERY"


class TrustContext(BaseModel):
    """Explicitly tags data origins to maintain strict trust boundaries."""
    source_type: str = "WEBPAGE"  # SYSTEM, USER, WEBPAGE, EXTENSION, OCR
    trust_level: TrustLevel = TrustLevel.UNTRUSTED
    is_authoritative: bool = False
    origin_domain: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
    is_indirect: bool = False
    context_intent: Optional[str] = None


class LinkSafetyResult(BaseModel):
    is_safe: bool = True
    risk_level: ThreatLevel = ThreatLevel.NORMAL
    error_code: str = "SAFE"
    reason: str = ""
    target_url: str = ""
    is_external_domain: bool = False
    is_protocol_downgrade: bool = False
    is_deceptive_text: bool = False


class DeceptiveUIResult(BaseModel):
    is_deceptive: bool = False
    risk_level: ThreatLevel = ThreatLevel.NORMAL
    mismatch_type: Optional[str] = None  # LABEL_ACTION_MISMATCH, HIDDEN_DESTRUCTIVE, EXFILTRATION_FORM
    reason: str = ""
    action_type: Optional[str] = None
    target_id: Optional[str] = None


class SecretScanResult(BaseModel):
    clean: bool = True
    files_scanned: int = 0
    secrets_found_count: int = 0
    findings: List[Dict[str, Any]] = Field(default_factory=list)
