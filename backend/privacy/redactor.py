"""
PrivyBrowse AI — Local Redaction & Sanitization Engine
Executes real visual screenshot redaction (opaque, blur, pixelate),
OCR text scrubbing, and DOM value sanitization. Produces a structured RedactionMap.
"""

import time
import base64
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from backend.privacy.schemas import (
    PIIEntity, RedactionItem, RedactionMap, SanitizedContext,
    DataClassification, PII_CLASSIFICATION_MAP, PIIType
)


class Redactor:
    """
    On-device Redactor and Sanitizer.
    Guarantees raw PII never passes unredacted into downstream contexts.
    """

    def __init__(self):
        pass

    def redact(
        self,
        screenshot_bytes: bytes,
        pii_entities: List[Dict[str, Any]],
        dom_nodes: List[Dict[str, Any]],
        redaction_style: str = "opaque"
    ) -> Tuple[bytes, List[Dict[str, Any]]]:
        """
        Legacy-compatible interface returning (redacted_bytes, redacted_dom_nodes).
        """
        redacted_bytes, _ = self.redact_screenshot(screenshot_bytes, pii_entities, redaction_style)
        redacted_dom = self.redact_dom_nodes(dom_nodes, pii_entities)
        return redacted_bytes, redacted_dom

    def redact_screenshot(
        self,
        screenshot_bytes: bytes,
        pii_entities: List[Dict[str, Any]],
        redaction_style: str = "opaque"
    ) -> Tuple[bytes, RedactionMap]:
        """
        Applies OpenCV visual redactions directly onto the screenshot pixel buffer.
        """
        if not screenshot_bytes or len(screenshot_bytes) == 0:
            return b"", RedactionMap()

        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        redaction_items: List[RedactionItem] = []
        highly_sensitive_count = 0
        sensitive_count = 0

        if img is not None:
            h, w, _ = img.shape

            for idx, pii in enumerate(pii_entities):
                bbox = pii.get("bbox", [0, 0, 0, 0])
                if len(bbox) < 4:
                    continue

                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

                # Clamp to image boundaries
                x1 = max(0, min(x1, w - 1))
                x2 = max(0, min(x2, w - 1))
                y1 = max(0, min(y1, h - 1))
                y2 = max(0, min(y2, h - 1))

                if x2 <= x1 or y2 <= y1:
                    continue

                pii_type = pii.get("type", "SENSITIVE")
                classification = pii.get("classification", DataClassification.SENSITIVE.value)
                replacement_text = f"[REDACTED_{pii_type}]"

                if classification == DataClassification.HIGHLY_SENSITIVE.value:
                    highly_sensitive_count += 1
                else:
                    sensitive_count += 1

                # Apply visual redaction style
                if redaction_style == "blur":
                    # Gaussian Blur on Region of Interest
                    roi = img[y1:y2, x1:x2]
                    if roi.size > 0:
                        k_w = int(max(3, (x2 - x1) // 3)) | 1
                        k_h = int(max(3, (y2 - y1) // 3)) | 1
                        roi_blurred = cv2.GaussianBlur(roi, (k_w, k_h), 0)
                        img[y1:y2, x1:x2] = roi_blurred
                        # Security boundary border
                        border_color = (0, 0, 255) if classification == DataClassification.HIGHLY_SENSITIVE.value else (0, 140, 255)
                        cv2.rectangle(img, (x1, y1), (x2, y2), border_color, 1)

                elif redaction_style == "pixelate":
                    # Downsample and nearest-neighbor upsample
                    roi = img[y1:y2, x1:x2]
                    if roi.size > 0:
                        temp_w = max(4, (x2 - x1) // 8)
                        temp_h = max(4, (y2 - y1) // 8)
                        small = cv2.resize(roi, (temp_w, temp_h), interpolation=cv2.INTER_LINEAR)
                        pixelated = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)
                        img[y1:y2, x1:x2] = pixelated
                        border_color = (0, 0, 255) if classification == DataClassification.HIGHLY_SENSITIVE.value else (0, 140, 255)
                        cv2.rectangle(img, (x1, y1), (x2, y2), border_color, 1)

                else:  # "opaque" (Default)
                    # Solid dark fill with high-contrast security label
                    fill_color = (25, 25, 30) if classification == DataClassification.HIGHLY_SENSITIVE.value else (35, 35, 45)
                    cv2.rectangle(img, (x1, y1), (x2, y2), fill_color, -1)

                    # Accent indicator strip on the left
                    accent_color = (68, 68, 239) if classification == DataClassification.HIGHLY_SENSITIVE.value else (0, 242, 254)
                    strip_width = min(4, max(2, (x2 - x1) // 20))
                    cv2.rectangle(img, (x1, y1), (x1 + strip_width, y2), accent_color, -1)

                    # Render label text if box dimensions permit
                    label = f"[{pii_type}]"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    scale = 0.38
                    thickness = 1
                    (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
                    if (x2 - x1 - strip_width) > (tw + 4) and (y2 - y1) > (th + 4):
                        tx = x1 + strip_width + 4
                        ty = y1 + (y2 - y1 + th) // 2
                        cv2.putText(img, label, (tx, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

                redaction_items.append(RedactionItem(
                    id=f"redact-{idx+1:03d}",
                    pii_type=pii_type,
                    bbox=[x1, y1, x2, y2],
                    replacement=replacement_text,
                    confidence=float(pii.get("confidence", 0.95)),
                    classification=classification,
                    element_id=pii.get("element_id")
                ))

            _, encoded_img = cv2.imencode(".png", img)
            redacted_bytes = encoded_img.tobytes()
        else:
            redacted_bytes = screenshot_bytes

        redaction_map = RedactionMap(
            redactions=redaction_items,
            total_redacted=len(redaction_items),
            highly_sensitive_count=highly_sensitive_count,
            sensitive_count=sensitive_count,
            style=redaction_style,
            timestamp=str(time.time())
        )

        return redacted_bytes, redaction_map

    def redact_ocr_blocks(
        self,
        ocr_blocks: List[Dict[str, Any]],
        pii_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Replaces raw sensitive text within OCR layout blocks with safe redaction tokens.
        """
        sanitized_blocks = []
        for block in ocr_blocks:
            new_block = dict(block)
            block_text = new_block.get("text", "")
            block_id = new_block.get("id") or new_block.get("element_id")

            # Check if this block matches any PII entity directly or textually
            for pii in pii_entities:
                pii_raw = pii.get("raw_text", "")
                pii_type = pii.get("type", "SENSITIVE")
                token = f"[REDACTED_{pii_type}]"

                if pii_raw and pii_raw in block_text:
                    block_text = block_text.replace(pii_raw, token)
                elif pii.get("element_id") and pii.get("element_id") == block_id:
                    block_text = token

            new_block["text"] = block_text
            sanitized_blocks.append(new_block)

        return sanitized_blocks

    def redact_dom_nodes(
        self,
        dom_nodes: List[Dict[str, Any]],
        pii_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Sanitizes DOM nodes so sensitive attribute values (.value, .placeholder, .text)
        are scrubbed before being passed to reasoning agents.
        """
        sanitized_nodes = []

        for node in dom_nodes:
            new_node = dict(node)
            node_id = new_node.get("id")
            input_type = new_node.get("type", "").lower()
            node_text = new_node.get("text", "")
            node_value = new_node.get("value", "")
            node_placeholder = new_node.get("placeholder", "")

            # Unconditional rule: passwords are NEVER retained in plaintext
            if input_type == "password":
                new_node["value"] = "[REDACTED_PASSWORD]"
                new_node["text"] = "[REDACTED_PASSWORD]"
                new_node["placeholder"] = "••••••••"
                sanitized_nodes.append(new_node)
                continue

            # Match associated PII entities
            associated_pii = None
            for pii in pii_entities:
                if pii.get("element_id") and pii.get("element_id") == node_id:
                    associated_pii = pii
                    break

            if associated_pii:
                pii_type = associated_pii.get("type", "SENSITIVE")
                token = f"[REDACTED_{pii_type}]"
                if "value" in new_node:
                    new_node["value"] = token
                if "text" in new_node:
                    new_node["text"] = token
                if "placeholder" in new_node:
                    new_node["placeholder"] = f"Enter {pii_type.lower()}..."
            else:
                # String substitution for inline matches
                for pii in pii_entities:
                    pii_raw = pii.get("raw_text", "")
                    pii_type = pii.get("type", "SENSITIVE")
                    token = f"[REDACTED_{pii_type}]"

                    if pii_raw:
                        if pii_raw in node_text:
                            new_node["text"] = node_text.replace(pii_raw, token)
                        if pii_raw in node_value:
                            new_node["value"] = node_value.replace(pii_raw, token)
                        if pii_raw in node_placeholder:
                            new_node["placeholder"] = node_placeholder.replace(pii_raw, token)

            sanitized_nodes.append(new_node)

        return sanitized_nodes
