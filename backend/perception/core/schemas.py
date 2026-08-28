"""
PrivyBrowse AI — Perception Schemas
Strongly typed Pydantic models for the visual perception pipeline.
All bounding boxes use viewport coordinates.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class ElementType(str, Enum):
    BUTTON = "BUTTON"
    LINK = "LINK"
    INPUT = "INPUT"
    TEXTAREA = "TEXTAREA"
    CHECKBOX = "CHECKBOX"
    RADIO = "RADIO"
    SELECT = "SELECT"
    IMAGE = "IMAGE"
    TEXT = "TEXT"
    HEADING = "HEADING"
    NAV = "NAV"
    FORM = "FORM"
    CARD = "CARD"
    ICON = "ICON"
    ELEMENT = "ELEMENT"


class Visibility(str, Enum):
    VISIBLE = "VISIBLE"
    HIDDEN = "HIDDEN"
    PARTIALLY_VISIBLE = "PARTIALLY_VISIBLE"
    OFFSCREEN = "OFFSCREEN"
    OBSCURED = "OBSCURED"


class DetectionSource(str, Enum):
    DOM = "DOM"
    OCR = "OCR"
    VISION = "VISION"
    TESSERACT = "TESSERACT"
    DOM_TEXT_PROXY = "DOM_TEXT_PROXY"
    FUSED = "FUSED"
    GEOMETRY = "GEOMETRY"


class BoundingBox(BaseModel):
    """Viewport-coordinate bounding box."""
    x: float
    y: float
    width: float
    height: float

    @property
    def x1(self) -> float:
        return self.x

    @property
    def y1(self) -> float:
        return self.y

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> tuple:
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_xyxy(self) -> list:
        """Return [x1, y1, x2, y2] format."""
        return [self.x, self.y, self.x + self.width, self.y + self.height]

    def to_dict(self) -> dict:
        return {
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height,
            "top": self.y, "left": self.x,
            "right": self.x + self.width, "bottom": self.y + self.height
        }

    @classmethod
    def from_xyxy(cls, x1: float, y1: float, x2: float, y2: float) -> "BoundingBox":
        return cls(x=x1, y=y1, width=x2 - x1, height=y2 - y1)


class PerceivedElement(BaseModel):
    """A single element detected by the perception pipeline."""
    id: str = Field(..., description="Stable temporary ID, e.g. pb-element-001")
    type: str = Field(..., description="Element type classification")
    label: str = Field("", description="Human-readable label")
    text: str = Field("", description="Visible text content")
    bbox: BoundingBox
    confidence: float = Field(..., ge=0.0, le=1.0)
    visible: bool = True
    enabled: bool = True
    interactive: bool = False
    sources: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    visibility: str = "VISIBLE"

    def to_agent_dict(self) -> dict:
        """Compact representation for the browser agent."""
        return {
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "confidence": round(self.confidence, 3),
            "visible": self.visible,
            "enabled": self.enabled,
            "interactive": self.interactive,
            "sources": self.sources,
            "attributes": self.attributes,
            "visibility": self.visibility
        }

    def to_legacy_dict(self) -> dict:
        """Backwards-compatible dict matching old FusedElement shape for existing frontend."""
        return {
            "id": self.id,
            "type": self.type,
            "bbox": self.bbox.to_xyxy(),
            "text": self.label or self.text,
            "value": self.attributes.get("value", ""),
            "attributes": self.attributes,
            "confidence": round(self.confidence, 3),
            "source": "FUSED" if len(self.sources) > 1 else (self.sources[0] if self.sources else "UNKNOWN")
        }


class PerceptionLatency(BaseModel):
    """Per-stage latency measurement in milliseconds."""
    preprocessing_ms: float = 0.0
    ocr_ms: float = 0.0
    visual_detection_ms: float = 0.0
    dom_detection_ms: float = 0.0
    text_detection_ms: float = 0.0
    fusion_ms: float = 0.0
    total_ms: float = 0.0


class PerceptionSummary(BaseModel):
    """High-level summary of the perception result."""
    element_count: int = 0
    interactive_count: int = 0
    text_regions: int = 0
    buttons: int = 0
    inputs: int = 0
    links: int = 0
    images: int = 0
    headings: int = 0
    sources_used: List[str] = Field(default_factory=list)
    ocr_engine: str = "UNAVAILABLE"
    privacy_status: str = "LOCAL_UNSANITIZED"


class CoordinateSystem(BaseModel):
    """Metadata about the coordinate space used."""
    viewport_width: int = 0
    viewport_height: int = 0
    screenshot_width: int = 0
    screenshot_height: int = 0
    device_pixel_ratio: float = 1.0
    scroll_x: float = 0.0
    scroll_y: float = 0.0
    document_width: float = 0.0
    document_height: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0


class PageRepresentation(BaseModel):
    """Structured page representation for agent reasoning."""
    title: str = ""
    url: str = ""
    hostname: str = ""
    viewport: Dict[str, int] = Field(default_factory=dict)
    scroll_position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    document_dimensions: Dict[str, float] = Field(default_factory=lambda: {"width": 0.0, "height": 0.0})


class PerceptionResult(BaseModel):
    """Complete result from the perception pipeline."""
    success: bool = True
    page: PageRepresentation = Field(default_factory=PageRepresentation)
    elements: List[PerceivedElement] = Field(default_factory=list)
    summary: PerceptionSummary = Field(default_factory=PerceptionSummary)
    latency: PerceptionLatency = Field(default_factory=PerceptionLatency)
    coordinate_system: CoordinateSystem = Field(default_factory=CoordinateSystem)
    timestamp: str = ""
    version: str = "1.0.0"
    warnings: List[str] = Field(default_factory=list)
    error: Optional[Dict[str, str]] = None
