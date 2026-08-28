# Perception engine package
from backend.perception.core.pipeline import PerceptionPipeline
from backend.perception.core.schemas import (
    BoundingBox, PerceivedElement, PerceptionResult,
    PerceptionLatency, PerceptionSummary, PageRepresentation,
    CoordinateSystem, ElementType, Visibility, DetectionSource
)
from backend.perception.core.coordinator import CoordinateConverter
from backend.perception.preprocessing.image_processor import ImageProcessor
from backend.perception.ocr.tesseract_engine import TesseractOCREngine
from backend.perception.detectors.dom_detector import DOMDetector
from backend.perception.detectors.visual_detector import VisualDetector
from backend.perception.detectors.text_detector import TextDetector
from backend.perception.fusion.context_fuser import ContextFuser

# Legacy compatibility exports
from backend.perception.element_detector import ElementDetector
from backend.perception.ocr_engine import OCREngine

__all__ = [
    "PerceptionPipeline",
    "BoundingBox",
    "PerceivedElement",
    "PerceptionResult",
    "PerceptionLatency",
    "PerceptionSummary",
    "PageRepresentation",
    "CoordinateSystem",
    "CoordinateConverter",
    "ImageProcessor",
    "TesseractOCREngine",
    "DOMDetector",
    "VisualDetector",
    "TextDetector",
    "ContextFuser",
    "ElementDetector",
    "OCREngine",
]
