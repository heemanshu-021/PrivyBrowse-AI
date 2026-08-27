import cv2
import numpy as np
import base64
from typing import List, Dict, Any, Tuple

class Redactor:
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
        Redacts sensitive items from both the screenshot image and DOM node array.
        Supports redaction styles: 'opaque' (solid fill), 'blur' (Gaussian blur), 'pixelate'.
        """
        # --- 1. REDACT VISUAL SCREENSHOT ---
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is not None:
            h, w, _ = img.shape
            for pii in pii_entities:
                bbox = pii["bbox"] # [x1, y1, x2, y2]
                x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                
                # Boundary checks
                x1, x2 = max(0, min(x1, w - 1)), max(0, min(x2, w - 1))
                y1, y2 = max(0, min(y1, h - 1)), max(0, min(y2, h - 1))
                
                if x2 <= x1 or y2 <= y1:
                    continue
                
                pii_type = pii["type"]
                
                if redaction_style == "blur":
                    # Extract region, apply strong blur, replace
                    roi = img[y1:y2, x1:x2]
                    # Kernel size proportional to size, must be odd
                    k_w = int(max(3, (x2 - x1) // 3)) | 1
                    k_h = int(max(3, (y2 - y1) // 3)) | 1
                    roi_blurred = cv2.GaussianBlur(roi, (k_w, k_h), 0)
                    img[y1:y2, x1:x2] = roi_blurred
                    
                    # Optional: Add boundary line
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 140, 0), 1)
                    
                elif redaction_style == "pixelate":
                    roi = img[y1:y2, x1:x2]
                    # Resize to small, then scale back up to pixelate
                    temp_w = max(4, (x2 - x1) // 8)
                    temp_h = max(4, (y2 - y1) // 8)
                    small = cv2.resize(roi, (temp_w, temp_h), interpolation=cv2.INTER_LINEAR)
                    pixelated = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)
                    img[y1:y2, x1:x2] = pixelated
                    
                    # Optional: Add boundary line
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 140, 0), 1)
                    
                else: # "opaque" default
                    # Solid gray or black rectangle
                    cv2.rectangle(img, (x1, y1), (x2, y2), (40, 40, 40), -1)
                    # Text label overlay (e.g. "[CARD REDACTED]")
                    label = f"[{pii_type}]"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    scale = 0.4
                    thickness = 1
                    text_size, _ = cv2.getTextSize(label, font, scale, thickness)
                    text_w, text_h = text_size
                    # Draw label in center if space permits, else skip label
                    if (x2 - x1) > text_w and (y2 - y1) > text_h:
                        text_x = x1 + (x2 - x1 - text_w) // 2
                        text_y = y1 + (y2 - y1 + text_h) // 2
                        cv2.putText(img, label, (text_x, text_y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)

            # Encode back to bytes
            _, encoded_img = cv2.imencode(".png", img)
            redacted_bytes = encoded_img.tobytes()
        else:
            redacted_bytes = screenshot_bytes

        # --- 2. REDACT DOM NODES ---
        # Deep copy/transform DOM nodes so we don't expose raw PII in redacted output
        redacted_nodes = []
        for node in dom_nodes:
            new_node = dict(node)
            node_id = node.get("id")
            
            # Find if this node is associated with any detected PII
            associated_pii = None
            for pii in pii_entities:
                if pii.get("element_id") == node_id:
                    associated_pii = pii
                    break
            
            # If not direct element match, check text matching
            node_text = new_node.get("text", "")
            node_value = new_node.get("value", "")
            
            # If there's an associated PII, mask it
            if associated_pii:
                pii_type = associated_pii["type"]
                if "value" in new_node:
                    new_node["value"] = f"[{pii_type} REDACTED]"
                if "text" in new_node:
                    new_node["text"] = f"[{pii_type} REDACTED]"
            else:
                # Run text replacement for inline matches
                for pii in pii_entities:
                    pii_text = pii.get("text", "")
                    if pii_text and pii_text in node_text:
                        node_text = node_text.replace(pii_text, f"[{pii['type']} REDACTED]")
                        new_node["text"] = node_text
                    if pii_text and pii_text in node_value:
                        node_value = node_value.replace(pii_text, f"[{pii['type']} REDACTED]")
                        new_node["value"] = node_value
                        
            redacted_nodes.append(new_node)
            
        return redacted_bytes, redacted_nodes
