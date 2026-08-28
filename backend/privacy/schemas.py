"""
PrivyBrowse AI — Privacy Schemas & Data Classifications
Strongly typed models for PII entities, redaction maps, sanitization contexts, and privacy policies.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class PIIType(str, Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CARD = "CARD"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    PASSWORD = "PASSWORD"
    OTP = "OTP"
    SECRET_TOKEN = "SECRET_TOKEN"
    ADDRESS = "ADDRESS"
    NAME = "NAME"
    DOB = "DOB"
    FACE = "FACE"
    ID_NUM = "ID_NUM"
    GENERIC_SENSITIVE = "GENERIC_SENSITIVE"


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    SENSITIVE = "SENSITIVE"
    HIGHLY_SENSITIVE = "HIGHLY_SENSITIVE"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Classification lookup for each PII type
PII_CLASSIFICATION_MAP: Dict[PIIType, DataClassification] = {
    PIIType.PASSWORD: DataClassification.HIGHLY_SENSITIVE,
    PIIType.OTP: DataClassification.HIGHLY_SENSITIVE,
    PIIType.SECRET_TOKEN: DataClassification.HIGHLY_SENSITIVE,
    PIIType.CARD: DataClassification.HIGHLY_SENSITIVE,
    PIIType.BANK_ACCOUNT: DataClassification.HIGHLY_SENSITIVE,
    PIIType.AADHAAR: DataClassification.HIGHLY_SENSITIVE,
    PIIType.PAN: DataClassification.HIGHLY_SENSITIVE,
    PIIType.EMAIL: DataClassification.SENSITIVE,
    PIIType.PHONE: DataClassification.SENSITIVE,
    PIIType.DOB: DataClassification.SENSITIVE,
    PIIType.ADDRESS: DataClassification.SENSITIVE,
    PIIType.NAME: DataClassification.SENSITIVE,
    PIIType.FACE: DataClassification.SENSITIVE,
    PIIType.ID_NUM: DataClassification.SENSITIVE,
    PIIType.GENERIC_SENSITIVE: DataClassification.SENSITIVE,
}


class PIIEntity(BaseModel):
    """A detected sensitive PII instance located on a webpage."""
    id: str = Field(..., description="Unique ID for this PII detection, e.g. pii-001")
    type: str = Field(..., description="PII category, e.g. EMAIL, CARD, PAN, AADHAAR")
    text: str = Field(..., description="Masked or descriptive value safe for UI display")
    raw_text: Optional[str] = Field(
        default=None,
        description="Original raw text. Retained only inside local privacy boundary; excluded from remote serialization."
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0.0 - 1.0]")
    confidence_level: str = Field("HIGH", description="HIGH, MEDIUM, or LOW")
    bbox: List[int] = Field(..., description="Bounding box [x1, y1, x2, y2] in viewport coordinates")
    source: List[str] = Field(default_factory=list, description="Detection sources: OCR, DOM, PATTERN, VISION")
    classification: str = Field(DataClassification.SENSITIVE.value, description="PUBLIC, SENSITIVE, HIGHLY_SENSITIVE")
    element_id: Optional[str] = Field(None, description="Associated DOM or perception element ID")
    redaction_required: bool = True
    details: Dict[str, Any] = Field(default_factory=dict)

    def to_safe_dict(self) -> Dict[str, Any]:
        """Returns entity dict with raw_text guaranteed stripped."""
        d = self.model_dump(exclude={"raw_text"})
        return d


class RedactionItem(BaseModel):
    """Record of a single visual or textual redaction applied."""
    id: str
    pii_type: str
    bbox: List[int]
    replacement: str
    confidence: float
    classification: str
    element_id: Optional[str] = None


class RedactionMap(BaseModel):
    """Complete ledger of all redactions applied to a page frame."""
    redactions: List[RedactionItem] = Field(default_factory=list)
    total_redacted: int = 0
    highly_sensitive_count: int = 0
    sensitive_count: int = 0
    style: str = "opaque"
    timestamp: str = ""


class SanitizedContext(BaseModel):
    """Sanitized context ready for downstream reasoning, guaranteed clean."""
    redacted_screenshot: str = ""
    sanitized_dom_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    sanitized_ocr_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    redaction_map: RedactionMap = Field(default_factory=RedactionMap)
    is_safe_for_reasoning: bool = True
    timestamp: str = ""
    privacy_policy_applied: str = "STRICT_LOCAL_ONLY"


class PrivacyPolicy(BaseModel):
    """Machine-readable privacy policy."""
    process_locally: bool = True
    redact_pii: bool = True
    allow_raw_remote_transmission: bool = False
    allow_sanitized_remote_transmission: bool = True
    min_confidence_threshold: float = 0.50
    enforce_zero_password_logging: bool = True
    default_redaction_style: str = "opaque"


class PrivacyAuditLogEntry(BaseModel):
    """Privacy-safe audit log entry (NEVER contains raw PII values)."""
    id: str
    event: str  # PII_DETECTED, PII_REDACTED, SANITIZATION_COMPLETED, REMOTE_TRANSMISSION_BLOCKED, etc.
    type: Optional[str] = None
    classification: Optional[str] = None
    confidence: Optional[float] = None
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)
