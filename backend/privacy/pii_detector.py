import re
import cv2
import numpy as np
import os
from typing import List, Dict, Any

class PIIDetector:
    def __init__(self):
        # Load OpenCV face detector Haar Cascade
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            self.face_cascade = None

        # Regex patterns
        self.email_regex = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
        self.phone_regex = re.compile(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}')
        self.card_regex = re.compile(r'\b(?:\d[ -]*?){13,16}\b') # 13 to 16 digit cards
        self.dob_regex = re.compile(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b|\b\d{4}[-/]\d{2}[-/]\d{2}\b')
        self.id_regex = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b[A-Z0-9]{9,12}\b') # SSN / ID-like patterns

    def detect_pii(self, screenshot_bytes: bytes, text_blocks: List[Dict[str, Any]], dom_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans layout text blocks, DOM attributes, and visual features to identify PII.
        """
        pii_entities = []

        # 1. SCAN TEXT BLOCKS WITH REGEXES (OCR TEXTS)
        for block in text_blocks:
            text = block["text"]
            bbox = block["bbox"]
            conf = block.get("confidence", 0.90)
            
            # Check Email
            for match in self.email_regex.finditer(text):
                pii_entities.append({
                    "type": "EMAIL",
                    "text": match.group(),
                    "confidence": 0.98,
                    "bbox": bbox,
                    "source": "OCR_REGEX"
                })

            # Check Phone (only if it matches digit criteria to avoid coordinate/number confusion)
            for match in self.phone_regex.finditer(text):
                val = match.group()
                digit_count = sum(c.isdigit() for c in val)
                if digit_count >= 10:
                    pii_entities.append({
                        "type": "PHONE",
                        "text": val,
                        "confidence": 0.90,
                        "bbox": bbox,
                        "source": "OCR_REGEX"
                    })

            # Check Credit Card
            for match in self.card_regex.finditer(text):
                val = match.group()
                digit_count = sum(c.isdigit() for c in val)
                if 12 <= digit_count <= 19:
                    pii_entities.append({
                        "type": "CARD",
                        "text": val,
                        "confidence": 0.95,
                        "bbox": bbox,
                        "source": "OCR_REGEX"
                    })

            # Check Date of Birth
            for match in self.dob_regex.finditer(text):
                pii_entities.append({
                    "type": "DOB",
                    "text": match.group(),
                    "confidence": 0.88,
                    "bbox": bbox,
                    "source": "OCR_REGEX"
                })

            # Check Identification numbers (e.g. SSN-like patterns)
            for match in self.id_regex.finditer(text):
                val = match.group()
                # Ignore plain coordinates/numbers
                if "-" in val or len(val) >= 9:
                    pii_entities.append({
                        "type": "ID_NUM",
                        "text": val,
                        "confidence": 0.85,
                        "bbox": bbox,
                        "source": "OCR_REGEX"
                    })

        # 2. SCAN DOM SEMANTICS (INPUT FIELDS, PASSWORDS, NAMES)
        for node in dom_nodes:
            # Check inputs that might be sensitive
            tag_name = node.get("tag_name", "").upper()
            input_type = node.get("type", "").lower()
            placeholder = node.get("placeholder", "").lower()
            name_attr = node.get("name", "").lower()
            id_attr = node.get("id", "").lower()
            node_value = node.get("value", "")
            bbox = node.get("bbox")

            if not bbox or tag_name != "INPUT":
                continue

            is_sensitive = False
            pii_type = None
            conf = 0.70

            # Password field
            if input_type == "password":
                is_sensitive = True
                pii_type = "PASSWORD"
                conf = 0.99
            # Credit Card attributes
            elif any(k in name_attr or k in id_attr or k in placeholder for k in ["card", "cc-", "cvv", "cvc", "expiry"]):
                is_sensitive = True
                pii_type = "CARD"
                conf = 0.92
            # Email fields
            elif input_type == "email" or any(k in name_attr or k in id_attr or k in placeholder for k in ["email", "mail"]):
                is_sensitive = True
                pii_type = "EMAIL"
                conf = 0.90
            # Phone inputs
            elif input_type == "tel" or any(k in name_attr or k in id_attr or k in placeholder for k in ["phone", "tel", "mobile"]):
                is_sensitive = True
                pii_type = "PHONE"
                conf = 0.90
            # Person Names
            elif any(k in name_attr or k in id_attr or k in placeholder for k in ["username", "name", "fname", "lname", "fullname"]):
                is_sensitive = True
                pii_type = "NAME"
                conf = 0.80
            # Addresses
            elif any(k in name_attr or k in id_attr or k in placeholder for k in ["address", "street", "city", "zip", "postal"]):
                is_sensitive = True
                pii_type = "ADDRESS"
                conf = 0.85

            if is_sensitive:
                pii_entities.append({
                    "type": pii_type,
                    "text": node_value or f"[{pii_type} FIELD]",
                    "confidence": conf,
                    "bbox": bbox,
                    "source": "DOM_SEMANTICS",
                    "element_id": node.get("id")
                })

        # 3. VISUAL FACE DETECTION (ON RAW SCREENSHOT)
        if self.face_cascade is not None and len(screenshot_bytes) > 0:
            try:
                nparr = np.frombuffer(screenshot_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    for (x, y, w, h) in faces:
                        pii_entities.append({
                            "type": "FACE",
                            "text": "[FACE DETECTED]",
                            "confidence": 0.90,
                            "bbox": [int(x), int(y), int(x + w), int(y + h)],
                            "source": "VISION_HAAR"
                        })
            except Exception as e:
                # Silently catch opencv errors if image loading fails
                pass

        # Deduplicate overlapping entities of the same type/bounding box
        unique_pii = []
        seen_boxes = set()
        for pii in pii_entities:
            box_key = tuple(pii["bbox"])
            type_key = pii["type"]
            # If we already have this box for this type, keep the one with higher confidence
            k = (box_key, type_key)
            if k not in seen_boxes:
                seen_boxes.add(k)
                unique_pii.append(pii)

        return unique_pii
