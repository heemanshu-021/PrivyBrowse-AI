from typing import List, Dict, Any

class OCREngine:
    def __init__(self):
        pass

    def extract_text(self, dom_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts visible text blocks mapped to visual coordinate coordinates.
        Uses the high-fidelity DOM coordinates sent by the browser client as the ground truth layout,
        replicating localized OCR results by combining text content and bounding boxes.
        """
        text_blocks = []
        for i, node in enumerate(dom_nodes):
            text = node.get("text", "").strip()
            # Only consider nodes with actual text and a bounding rect
            if not text or "bbox" not in node:
                continue
            
            bbox = node["bbox"]  # [x1, y1, x2, y2]
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            
            # Avoid invalid coordinates
            if w <= 0 or h <= 0:
                continue

            text_blocks.append({
                "id": f"ocr_{i}",
                "text": text,
                "bbox": bbox,
                "confidence": 0.99,
                "element_id": node.get("id"),
                "tag_name": node.get("tag_name", "")
            })
            
        return text_blocks
