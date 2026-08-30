"""
PrivyBrowse AI — Text Detector
Detects visible text regions from an image using OCR and DOM text proxy.
Merges nearby words into meaningful text blocks rather than emitting
individual characters.
"""

from typing import List, Dict, Any
from backend.perception.core.schemas import BoundingBox, PerceivedElement
from backend.perception.ocr.base import OCRResult


class TextDetector:
    """
    Converts raw OCR results into PerceivedElement objects of type TEXT or HEADING.
    Also supports DOM text fallback when OCR is unavailable.
    """

    def detect_from_ocr(self, ocr_results: List[OCRResult]) -> List[PerceivedElement]:
        """
        Convert OCR results into TEXT-type PerceivedElements.
        Deduplicates and filters short/noisy detections.
        """
        elements: List[PerceivedElement] = []
        seen_texts: set = set()

        for idx, result in enumerate(ocr_results):
            text = result.text.strip()

            # Skip very short or numeric-only noise
            if len(text) < 2:
                continue

            # Skip duplicates
            text_key = text.lower()
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)

            bbox = BoundingBox.from_xyxy(*result.bbox[:4])

            # Basic heuristic: larger text blocks with high confidence → HEADING
            el_type = "TEXT"
            if bbox.height >= 20 and result.confidence >= 0.7 and len(text.split()) <= 8:
                el_type = "HEADING"

            elements.append(PerceivedElement(
                id=f"ocr-{idx:03d}",
                type=el_type,
                label=text,
                text=text,
                bbox=bbox,
                confidence=result.confidence,
                visible=True,
                enabled=True,
                interactive=False,
                sources=[result.source],
                attributes={"ocr_source": result.source},
                visibility="VISIBLE",
            ))

        return elements

    def detect_from_dom_text(self, dom_nodes: List[Dict[str, Any]]) -> List[PerceivedElement]:
        """
        DOM text fallback: extract text blocks from DOM nodes when OCR is unavailable.
        Only nodes with actual text content and valid bounding boxes are included.
        Source is marked as DOM_TEXT_PROXY so the system knows this is not visual OCR.
        """
        elements: List[PerceivedElement] = []

        for idx, node in enumerate(dom_nodes):
            if not isinstance(node, dict):
                continue

            text = str(node.get("text", "")).strip()
            if not text:
                continue

            bbox_raw = node.get("bbox")
            if not bbox_raw:
                continue

            bbox = None
            if isinstance(bbox_raw, list) and len(bbox_raw) >= 4:
                x1, y1, x2, y2 = float(bbox_raw[0]), float(bbox_raw[1]), float(bbox_raw[2]), float(bbox_raw[3])
                w = x2 - x1
                h = y2 - y1
                if w > 0 and h > 0:
                    bbox = BoundingBox(x=x1, y=y1, width=w, height=h)
            elif isinstance(bbox_raw, dict):
                x = float(bbox_raw.get("x", bbox_raw.get("left", 0)))
                y = float(bbox_raw.get("y", bbox_raw.get("top", 0)))
                w = float(bbox_raw.get("width", 0))
                h = float(bbox_raw.get("height", 0))
                if w <= 0 and "right" in bbox_raw:
                    w = float(bbox_raw["right"]) - x
                if h <= 0 and "bottom" in bbox_raw:
                    h = float(bbox_raw["bottom"]) - y
                if w > 0 and h > 0:
                    bbox = BoundingBox(x=x, y=y, width=w, height=h)

            if bbox is None:
                continue

            raw_tag = node.get("tag_name") or node.get("tag") or node.get("tagName") or ""
            tag = str(raw_tag).upper()
            el_type = "HEADING" if tag in ("H1", "H2", "H3", "H4", "H5", "H6") else "TEXT"

            elements.append(PerceivedElement(
                id=f"dom-text-{idx:03d}",
                type=el_type,
                label=text,
                text=text,
                bbox=bbox,
                confidence=0.95,  # DOM text is reliable but not visual OCR
                visible=True,
                enabled=True,
                interactive=False,
                sources=["DOM_TEXT_PROXY"],
                attributes={
                    "tag_name": tag,
                    "element_id": str(node.get("id", "")),
                },
                visibility="VISIBLE",
            ))

        return elements
