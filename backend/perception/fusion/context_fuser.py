"""
PrivyBrowse AI — Context Fuser
Merges DOM, OCR, and Vision detections into a unified element list.
Uses IoU matching, multi-source confidence, label resolution, and
duplicate suppression.
"""

from typing import List, Dict, Any, Optional
from backend.perception.core.schemas import BoundingBox, PerceivedElement
from backend.perception.fusion.iou_matcher import IoUMatcher
from backend.perception.fusion.confidence import (
    calculate_fused_confidence,
    calculate_single_source_confidence,
)
from backend.perception.utils.geometry import calculate_iou, is_contained


INTERACTIVE_TYPES = {"BUTTON", "LINK", "INPUT", "TEXTAREA", "CHECKBOX", "RADIO", "SELECT"}


class ContextFuser:
    """
    The core fusion engine. Combines detections from DOM, Vision, and OCR/Text
    into a deduplicated, confidence-scored, agent-ready element list.

    Fusion strategy:
      1. Use DOM elements as the primary anchor (highest structural reliability)
      2. Match vision elements to DOM via IoU
      3. Match OCR/text elements to DOM via IoU (for label enrichment)
      4. Append unmatched vision elements (vision-only detections)
      5. Assign stable IDs (pb-element-001, pb-element-002, ...)
      6. Calculate multi-source confidence for each fused element
    """

    def __init__(self, iou_threshold: float = 0.35):
        self.matcher = IoUMatcher(iou_threshold=iou_threshold)

    def fuse(
        self,
        dom_elements: List[PerceivedElement],
        vision_elements: List[PerceivedElement],
        text_elements: List[PerceivedElement],
    ) -> List[PerceivedElement]:
        """
        Fuse three lists of PerceivedElements from different detectors.
        Returns a unified, deduplicated list with stable IDs.
        """
        fused: List[PerceivedElement] = []

        # Track which vision/text elements have been consumed
        used_vision = set()
        used_text = set()

        # 1. DOM-anchored fusion: for each DOM element, find matching vision + text
        dom_vision_matches = self.matcher.match_elements(dom_elements, vision_elements)
        dom_text_matches = self.matcher.match_elements(dom_elements, text_elements)

        for i, dom_el in enumerate(dom_elements):
            # Find matched vision element
            _, vis_idx, vis_iou = dom_vision_matches[i]
            vis_el = vision_elements[vis_idx] if vis_idx is not None else None
            if vis_idx is not None:
                used_vision.add(vis_idx)

            # Find matched text element
            _, txt_idx, txt_iou = dom_text_matches[i]
            txt_el = text_elements[txt_idx] if txt_idx is not None else None
            if txt_idx is not None:
                used_text.add(txt_idx)

            # Resolve type: prefer DOM type, but vision can upgrade ELEMENT → BUTTON
            el_type = dom_el.type
            if el_type == "ELEMENT" and vis_el and vis_el.type in INTERACTIVE_TYPES:
                el_type = vis_el.type

            # Resolve label: DOM text > OCR text > placeholder > aria-label
            label = dom_el.label
            if not label and txt_el:
                label = txt_el.text
            if not label:
                label = dom_el.attributes.get("placeholder", "")

            # Build sources list
            sources = ["DOM"]
            if vis_el:
                sources.append("VISION")
            if txt_el:
                sources.extend(s for s in txt_el.sources if s not in sources)

            # Calculate confidence
            confidence = calculate_fused_confidence(
                dom_element=dom_el,
                vision_element=vis_el,
                ocr_text_match=txt_el is not None,
                ocr_confidence=txt_el.confidence if txt_el else 0.0,
                iou_score=vis_iou,
            )

            interactive = el_type in INTERACTIVE_TYPES

            fused.append(PerceivedElement(
                id="",  # Stable IDs assigned at the end
                type=el_type,
                label=label,
                text=dom_el.text or (txt_el.text if txt_el else ""),
                bbox=dom_el.bbox,  # Use DOM bbox as ground truth
                confidence=confidence,
                visible=dom_el.visible,
                enabled=dom_el.enabled,
                interactive=interactive,
                sources=sources,
                attributes=dom_el.attributes,
                visibility=dom_el.visibility,
            ))

        # 2. Append unmatched vision elements (elements visible on screen but not in DOM)
        for j, vis_el in enumerate(vision_elements):
            if j in used_vision:
                continue

            # Check if this vision element overlaps with any already-fused element
            is_dup = False
            for f_el in fused:
                if calculate_iou(vis_el.bbox, f_el.bbox) >= 0.40:
                    is_dup = True
                    break
            if is_dup:
                continue

            # Try to find a matching text element for labeling
            best_txt_idx = None
            best_txt_iou = 0.0
            for k, txt_el in enumerate(text_elements):
                if k in used_text:
                    continue
                iou = calculate_iou(vis_el.bbox, txt_el.bbox)
                if iou >= 0.30 and iou > best_txt_iou:
                    best_txt_iou = iou
                    best_txt_idx = k

            label = ""
            text = ""
            sources = ["VISION"]
            ocr_match = False
            ocr_conf = 0.0

            if best_txt_idx is not None:
                txt_el = text_elements[best_txt_idx]
                used_text.add(best_txt_idx)
                label = txt_el.text
                text = txt_el.text
                sources.extend(s for s in txt_el.sources if s not in sources)
                ocr_match = True
                ocr_conf = txt_el.confidence

            confidence = calculate_fused_confidence(
                dom_element=None,
                vision_element=vis_el,
                ocr_text_match=ocr_match,
                ocr_confidence=ocr_conf,
                iou_score=0.0,
            )

            fused.append(PerceivedElement(
                id="",
                type=vis_el.type,
                label=label,
                text=text,
                bbox=vis_el.bbox,
                confidence=confidence,
                visible=True,
                enabled=True,
                interactive=vis_el.type in INTERACTIVE_TYPES,
                sources=sources,
                attributes={},
                visibility="VISIBLE",
            ))

        # 3. Append unmatched text-only elements (OCR found text not in DOM or vision)
        for k, txt_el in enumerate(text_elements):
            if k in used_text:
                continue

            # Skip if it overlaps with any fused element
            is_dup = False
            for f_el in fused:
                if calculate_iou(txt_el.bbox, f_el.bbox) >= 0.40:
                    is_dup = True
                    break
            if is_dup:
                continue

            confidence = calculate_single_source_confidence(txt_el)

            fused.append(PerceivedElement(
                id="",
                type=txt_el.type,
                label=txt_el.text,
                text=txt_el.text,
                bbox=txt_el.bbox,
                confidence=confidence,
                visible=True,
                enabled=True,
                interactive=False,
                sources=txt_el.sources,
                attributes=txt_el.attributes,
                visibility="VISIBLE",
            ))

        # 4. Assign stable IDs
        for idx, el in enumerate(fused):
            el.id = f"pb-element-{idx + 1:03d}"

        return fused
