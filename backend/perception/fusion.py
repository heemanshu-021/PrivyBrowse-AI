from typing import List, Dict, Any

class ContextFuser:
    def __init__(self):
        pass

    def _calculate_iou(self, boxA: List[int], boxB: List[int]) -> float:
        """
        Calculates Intersection over Union (IoU) of two bounding boxes [x1, y1, x2, y2].
        """
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        if interArea == 0:
            return 0.0

        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def fuse_context(
        self, 
        dom_nodes: List[Dict[str, Any]], 
        vision_elements: List[Dict[str, Any]], 
        ocr_blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fuses DOM elements, OpenCV visual elements, and OCR texts, merging overlaps.
        """
        fused_elements = []
        used_vision_indices = set()
        
        # 1. Iterate through DOM nodes as the core layout anchor
        for node in dom_nodes:
            bbox = node.get("bbox")
            if not bbox:
                continue

            node_id = node.get("id", "")
            tag_name = node.get("tag_name", "").upper()
            input_type = node.get("type", "").upper()
            
            # Map element type
            element_type = "ELEMENT"
            if tag_name == "BUTTON" or (tag_name == "INPUT" and input_type in ["SUBMIT", "BUTTON"]):
                element_type = "BUTTON"
            elif tag_name == "INPUT" and input_type in ["CHECKBOX", "RADIO"]:
                element_type = "CHECKBOX"
            elif tag_name == "INPUT":
                element_type = "INPUT"
            elif tag_name in ["SELECT", "TEXTAREA"]:
                element_type = tag_name
            elif tag_name in ["A", "LINK"]:
                element_type = "LINK"
            elif tag_name == "IMG":
                element_type = "IMAGE"

            # Check if any vision-detected contours overlap with this DOM node
            matched_vision = None
            for idx, vis in enumerate(vision_elements):
                if idx in used_vision_indices:
                    continue
                
                iou = self._calculate_iou(bbox, vis["bbox"])
                # If they overlap significantly, we fuse them
                if iou >= 0.40:
                    matched_vision = vis
                    used_vision_indices.add(idx)
                    break
            
            # Find any associated text block from OCR
            associated_text = node.get("text", "")
            if not associated_text:
                for block in ocr_blocks:
                    # If the OCR text box is completely inside or overlaps the DOM node
                    iou = self._calculate_iou(bbox, block["bbox"])
                    if iou > 0.60:
                        associated_text = block["text"]
                        break

            # Build fused element
            fused_elements.append({
                "id": node_id,
                "type": matched_vision["type"] if matched_vision else element_type,
                "bbox": bbox,
                "text": associated_text,
                "value": node.get("value", ""),
                "attributes": {
                    "tag_name": tag_name,
                    "placeholder": node.get("placeholder", ""),
                    "type": node.get("type", ""),
                    "id": node.get("id_attr", ""),
                    "class": node.get("class_attr", "")
                },
                "confidence": max(node.get("confidence", 0.90), matched_vision["confidence"] if matched_vision else 0.0),
                "source": "FUSED" if matched_vision else "DOM"
            })

        # 2. Append visual detections that did NOT match any DOM element
        for idx, vis in enumerate(vision_elements):
            if idx in used_vision_indices:
                continue
            
            fused_elements.append({
                "id": vis["id"],
                "type": vis["type"],
                "bbox": vis["bbox"],
                "text": "",
                "value": "",
                "attributes": {},
                "confidence": vis["confidence"],
                "source": "VISION"
            })

        return fused_elements
