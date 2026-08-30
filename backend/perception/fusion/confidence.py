"""
PrivyBrowse AI — Multi-Source Confidence Scoring
Transparent, documented confidence calculation for fused perception elements.

Scoring formula:
  confidence = w_dom * dom_evidence +
               w_ocr * ocr_evidence +
               w_vision * vision_evidence +
               w_geometry * geometry_evidence

Weights:
  DOM       = 0.35  (structural ground truth from browser)
  OCR       = 0.30  (text recognition confirmation)
  VISION    = 0.25  (visual contour / shape confirmation)
  GEOMETRY  = 0.10  (size/ratio consistency bonus)

Each evidence factor is in [0.0, 1.0].
"""

from typing import List, Optional
from backend.perception.core.schemas import PerceivedElement, BoundingBox

# Scoring weights
W_DOM = 0.35
W_OCR = 0.30
W_VISION = 0.25
W_GEOMETRY = 0.10


def calculate_fused_confidence(
    dom_element: Optional[PerceivedElement],
    vision_element: Optional[PerceivedElement],
    ocr_text_match: bool,
    ocr_confidence: float = 0.0,
    iou_score: float = 0.0,
) -> float:
    """
    Calculate a transparent multi-source confidence score.

    Args:
        dom_element: The DOM-detected element (or None if not detected by DOM)
        vision_element: The vision-detected element (or None)
        ocr_text_match: Whether OCR text was found overlapping this element
        ocr_confidence: The OCR engine's confidence for the matched text
        iou_score: IoU overlap score between DOM and Vision detections

    Returns:
        A confidence value in [0.0, 1.0]
    """
    dom_evidence = 0.0
    ocr_evidence = 0.0
    vision_evidence = 0.0
    geometry_evidence = 0.0

    # DOM evidence: high if DOM node exists with a valid bbox
    if dom_element is not None:
        dom_evidence = dom_element.confidence

    # OCR evidence: based on OCR text match and OCR engine confidence
    if ocr_text_match:
        ocr_evidence = max(0.5, ocr_confidence)  # At least 0.5 if text was found

    # Vision evidence: based on vision detector confidence
    if vision_element is not None:
        vision_evidence = vision_element.confidence

    # Geometry evidence: bonus based on IoU agreement between detectors
    if iou_score >= 0.60:
        geometry_evidence = 0.95
    elif iou_score >= 0.40:
        geometry_evidence = 0.75
    elif iou_score >= 0.20:
        geometry_evidence = 0.50
    else:
        # If only one source, give moderate geometry score for reasonable size
        geometry_evidence = 0.30

    # Weighted sum
    confidence = (
        W_DOM * dom_evidence +
        W_OCR * ocr_evidence +
        W_VISION * vision_evidence +
        W_GEOMETRY * geometry_evidence
    )

    # Clamp to [0.0, 1.0]
    return round(max(0.0, min(1.0, confidence)), 3)


def calculate_single_source_confidence(element: PerceivedElement) -> float:
    """
    Confidence for an element detected by only a single source.
    Apply a penalty since there's no cross-validation.
    """
    base = element.confidence
    # Single-source penalty: -10%
    return round(max(0.0, base * 0.90), 3)


def explain_confidence(
    dom_element: Optional[PerceivedElement],
    vision_element: Optional[PerceivedElement],
    ocr_text_match: bool,
    ocr_confidence: float = 0.0,
    iou_score: float = 0.0,
) -> dict:
    """
    Provide an explainable mathematical breakdown of a fused confidence score.
    Returns weights, evidence values, contributions, and the final score.
    """
    dom_evidence = dom_element.confidence if dom_element is not None else 0.0
    ocr_evidence = max(0.5, ocr_confidence) if ocr_text_match else 0.0
    vision_evidence = vision_element.confidence if vision_element is not None else 0.0

    if iou_score >= 0.60:
        geometry_evidence = 0.95
    elif iou_score >= 0.40:
        geometry_evidence = 0.75
    elif iou_score >= 0.20:
        geometry_evidence = 0.50
    else:
        geometry_evidence = 0.30

    dom_contrib = round(W_DOM * dom_evidence, 3)
    ocr_contrib = round(W_OCR * ocr_evidence, 3)
    vision_contrib = round(W_VISION * vision_evidence, 3)
    geom_contrib = round(W_GEOMETRY * geometry_evidence, 3)
    total = round(max(0.0, min(1.0, dom_contrib + ocr_contrib + vision_contrib + geom_contrib)), 3)

    return {
        "formula": "confidence = 0.35*DOM + 0.30*OCR + 0.25*Vision + 0.10*Geometry",
        "evidence": {
            "dom": round(dom_evidence, 3),
            "ocr": round(ocr_evidence, 3),
            "vision": round(vision_evidence, 3),
            "geometry": round(geometry_evidence, 3),
        },
        "contributions": {
            "dom": dom_contrib,
            "ocr": ocr_contrib,
            "vision": vision_contrib,
            "geometry": geom_contrib,
        },
        "iou_score": round(iou_score, 3),
        "total_confidence": total,
    }
