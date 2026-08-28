"""
PrivyBrowse AI — Abstract OCR Interface
Any OCR engine must implement this interface so it can be swapped transparently.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np


class OCRResult:
    """A single text detection result from OCR."""

    __slots__ = ("text", "confidence", "bbox", "source")

    def __init__(self, text: str, confidence: float, bbox: List[float], source: str = "OCR"):
        self.text = text
        self.confidence = confidence
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 3),
            "bbox": self.bbox,
            "source": self.source,
        }


class BaseOCREngine(ABC):
    """Abstract base class for all OCR implementations."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this engine is ready to perform inference."""
        ...

    @abstractmethod
    def extract_text(self, image: np.ndarray) -> List[OCRResult]:
        """
        Run OCR on a preprocessed image (grayscale or BGR).
        Returns a list of OCRResult objects with text, confidence, and bounding boxes.
        """
        ...

    @abstractmethod
    def get_engine_name(self) -> str:
        """Return the human-readable engine name."""
        ...

    def get_model_info(self) -> Dict[str, Any]:
        """Return metadata about the OCR model (size, version, etc.)."""
        return {
            "engine": self.get_engine_name(),
            "available": self.is_available(),
        }
