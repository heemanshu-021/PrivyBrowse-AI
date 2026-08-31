"""
PrivyBrowse AI — On-Device PII Detector Engine
Multi-signal on-device privacy engine combining OCR text analysis, DOM semantics,
keyword context, algorithmic checksums (Luhn, Aadhaar), and OpenCV facial detection.
"""

import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

from backend.privacy.schemas import (
    PIIEntity, PIIType, DataClassification, PII_CLASSIFICATION_MAP
)
from backend.privacy.rules.pattern_rules import (
    matches_email, matches_phone, matches_card, matches_pan,
    matches_aadhaar, matches_bank_account, matches_secret_token,
    matches_otp
)
from backend.privacy.rules.context_rules import (
    is_false_positive_number, boost_confidence_with_context
)
from backend.observability.publisher import global_event_publisher


class PIIDetector:
    """
    On-device PII Detection Engine.
    Operates strictly within the local trust boundary.
    """

    def __init__(self):
        # Load OpenCV Haar Cascade face detector
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            self.face_cascade = None

    def mask_value_for_display(self, text: str, pii_type: str) -> str:
        """
        Creates a privacy-safe preview representation for local UI display.
        Original raw secrets are never displayed in plaintext.
        """
        if not text:
            return f"[{pii_type}]"

        if pii_type == "PASSWORD":
            return "••••••••"
        elif pii_type == "CARD":
            clean = "".join(c for c in text if c.isdigit())
            last4 = clean[-4:] if len(clean) >= 4 else "****"
            return f"•••• •••• •••• {last4}"
        elif pii_type == "EMAIL":
            if "@" in text:
                parts = text.split("@", 1)
                user = parts[0]
                domain = parts[1]
                prefix = user[:2] if len(user) >= 2 else user[:1]
                return f"{prefix}***@{domain}"
            return "masked_email@domain.com"
        elif pii_type == "PHONE":
            clean = "".join(c for c in text if c.isdigit())
            last4 = clean[-4:] if len(clean) >= 4 else "****"
            return f"+**-***-***-{last4}"
        elif pii_type == "PAN":
            if len(text) == 10:
                return f"{text[:2]}***{text[-2:]}"
            return "PAN_CARD_NUMBER"
        elif pii_type == "AADHAAR":
            clean = "".join(c for c in text if c.isdigit())
            last4 = clean[-4:] if len(clean) >= 4 else "****"
            return f"XXXX XXXX {last4}"
        elif pii_type == "OTP":
            return "••••••"
        elif pii_type == "SECRET_TOKEN":
            return f"{text[:4]}...[REDACTED_SECRET]"
        elif pii_type == "FACE":
            return "[FACE DETECTED]"
        elif pii_type == "ADDRESS":
            return "[ADDRESS REDACTED]"
        elif pii_type == "NAME":
            words = text.split()
            if len(words) >= 2:
                return f"{words[0][0]}. {words[1]}"
            return f"{text[:2]}***"

        return f"[{pii_type} REDACTED]"

    def _normalize_bbox(self, bbox_raw: Any) -> List[int]:
        """Normalizes any bounding box (list, dict, or BoundingBox object) to [x1, y1, x2, y2]."""
        if not bbox_raw:
            return [0, 0, 0, 0]
        if isinstance(bbox_raw, list) and len(bbox_raw) >= 4:
            return [int(bbox_raw[0]), int(bbox_raw[1]), int(bbox_raw[2]), int(bbox_raw[3])]
        elif isinstance(bbox_raw, dict):
            x = int(bbox_raw.get("x", bbox_raw.get("left", 0)))
            y = int(bbox_raw.get("y", bbox_raw.get("top", 0)))
            w = int(bbox_raw.get("width", 0))
            h = int(bbox_raw.get("height", 0))
            if w <= 0 and "right" in bbox_raw:
                w = int(bbox_raw["right"]) - x
            if h <= 0 and "bottom" in bbox_raw:
                h = int(bbox_raw["bottom"]) - y
            return [x, y, x + max(0, w), y + max(0, h)]
        elif hasattr(bbox_raw, "to_xyxy"):
            return [int(c) for c in bbox_raw.to_xyxy()]
        return [0, 0, 0, 0]

    def detect_all_pii(
        self,
        screenshot_bytes: bytes,
        text_blocks: List[Any],
        dom_nodes: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Main entry point. Runs multi-signal detection across OCR, DOM, and Vision.
        Returns legacy-compatible and typed PII dictionary list.
        """
        entities = self.detect(screenshot_bytes, text_blocks, dom_nodes)
        return [e.to_safe_dict() for e in entities]

    def detect_pii(
        self,
        screenshot_bytes: bytes,
        text_blocks: List[Any],
        dom_nodes: List[Any]
    ) -> List[Dict[str, Any]]:
        """Backwards-compatible wrapper."""
        return self.detect_all_pii(screenshot_bytes, text_blocks, dom_nodes)

    def detect(
        self,
        screenshot_bytes: bytes,
        text_blocks: List[Any],
        dom_nodes: List[Any]
    ) -> List[PIIEntity]:
        """
        Executes full multi-layered PII detection pipeline.
        Returns strongly typed PIIEntity objects with raw_text populated internally.
        """
        detected_entities: List[PIIEntity] = []
        entity_counter = 1

        # Combine text for global context lookup
        global_context_parts = []
        for b in text_blocks or []:
            b_text = b.get("text", "") if isinstance(b, dict) else getattr(b, "text", "")
            if b_text:
                global_context_parts.append(str(b_text))

        for node in dom_nodes or []:
            if isinstance(node, dict):
                global_context_parts.extend([
                    str(node.get('placeholder', '')),
                    str(node.get('name', '')),
                    str(node.get('id', '')),
                    str(node.get('text', '')),
                    str(node.get('value', ''))
                ])
            else:
                global_context_parts.extend([
                    getattr(node, 'label', ''),
                    getattr(node, 'text', ''),
                    str(getattr(node, 'attributes', {}).get('placeholder', '')),
                    str(getattr(node, 'attributes', {}).get('name', ''))
                ])

        global_context = " ".join(global_context_parts)

        # -------------------------------------------------------------
        # 1. OCR TEXT BLOCKS WITH PATTERN MATCHING & CONTEXT BOOSTING
        # -------------------------------------------------------------
        for block in text_blocks or []:
            text = str(block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")).strip()
            raw_bbox = block.get("bbox") if isinstance(block, dict) else getattr(block, "bbox", [0, 0, 0, 0])
            bbox = self._normalize_bbox(raw_bbox)
            if not text:
                continue

            elem_id = block.get("element_id") if isinstance(block, dict) else getattr(block, "id", None)

            # (A) Email Match
            for match_str, _, _ in matches_email(text):
                conf, signals = boost_confidence_with_context(0.96, "EMAIL", text)
                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=PIIType.EMAIL.value,
                    text=self.mask_value_for_display(match_str, "EMAIL"),
                    raw_text=match_str,
                    confidence=conf,
                    confidence_level="HIGH" if conf >= 0.85 else "MEDIUM",
                    bbox=bbox,
                    source=["OCR_REGEX", "PATTERN"] + signals,
                    classification=PII_CLASSIFICATION_MAP[PIIType.EMAIL].value,
                    element_id=block.get("element_id")
                ))
                entity_counter += 1

            # (B) Credit / Debit Card Match
            for match_str, _, _, is_luhn in matches_card(text):
                # False positive check
                is_fp, reason = is_false_positive_number(match_str, text)
                if is_fp and not is_luhn:
                    continue

                base_conf = 0.98 if is_luhn else 0.88
                conf, signals = boost_confidence_with_context(base_conf, "CARD", text)
                if is_luhn:
                    signals.append("LUHN_CHECKSUM_VALID")

                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=PIIType.CARD.value,
                    text=self.mask_value_for_display(match_str, "CARD"),
                    raw_text=match_str,
                    confidence=conf,
                    confidence_level="HIGH" if conf >= 0.85 else "MEDIUM",
                    bbox=bbox,
                    source=["OCR_REGEX", "PATTERN"] + signals,
                    classification=PII_CLASSIFICATION_MAP[PIIType.CARD].value,
                    element_id=block.get("element_id")
                ))
                entity_counter += 1

            # (C) Indian PAN Card Match
            for match_str, _, _ in matches_pan(text):
                conf, signals = boost_confidence_with_context(0.95, "PAN", text)
                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=PIIType.PAN.value,
                    text=self.mask_value_for_display(match_str, "PAN"),
                    raw_text=match_str,
                    confidence=conf,
                    confidence_level="HIGH",
                    bbox=bbox,
                    source=["OCR_REGEX", "PATTERN", "PAN_STRUCTURE"] + signals,
                    classification=PII_CLASSIFICATION_MAP[PIIType.PAN].value,
                    element_id=block.get("element_id")
                ))
                entity_counter += 1

            # (D) Indian Aadhaar Number Match
            for match_str, _, _ in matches_aadhaar(text):
                is_fp, _ = is_false_positive_number(match_str, text)
                if is_fp:
                    continue

                conf, signals = boost_confidence_with_context(0.93, "AADHAAR", text)
                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=PIIType.AADHAAR.value,
                    text=self.mask_value_for_display(match_str, "AADHAAR"),
                    raw_text=match_str,
                    confidence=conf,
                    confidence_level="HIGH",
                    bbox=bbox,
                    source=["OCR_REGEX", "PATTERN", "AADHAAR_FORMAT"] + signals,
                    classification=PII_CLASSIFICATION_MAP[PIIType.AADHAAR].value,
                    element_id=block.get("element_id")
                ))
                entity_counter += 1

            # (E) Phone Number Match
            for match_str, _, _ in matches_phone(text):
                is_fp, _ = is_false_positive_number(match_str, text)
                if is_fp:
                    continue


                conf, signals = boost_confidence_with_context(0.90, "PHONE", text)
                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=PIIType.PHONE.value,
                    text=self.mask_value_for_display(match_str, "PHONE"),
                    raw_text=match_str,
                    confidence=conf,
                    confidence_level="HIGH" if conf >= 0.85 else "MEDIUM",
                    bbox=bbox,
                    source=["OCR_REGEX", "PATTERN"] + signals,
                    classification=PII_CLASSIFICATION_MAP[PIIType.PHONE].value,
                    element_id=block.get("element_id")
                ))
                entity_counter += 1

            # (F) API Keys, JWTs, Secret Tokens
            for match_str, _, _, token_kind in matches_secret_token(text):
                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=PIIType.SECRET_TOKEN.value,
                    text=self.mask_value_for_display(match_str, "SECRET_TOKEN"),
                    raw_text=match_str,
                    confidence=0.99,
                    confidence_level="HIGH",
                    bbox=bbox,
                    source=["OCR_REGEX", f"TOKEN_TYPE({token_kind})"],
                    classification=PII_CLASSIFICATION_MAP[PIIType.SECRET_TOKEN].value,
                    element_id=block.get("element_id")
                ))
                entity_counter += 1

            # (G) OTP with verification context
            for match_str, _, _ in matches_otp(text, text):
                is_fp, _ = is_false_positive_number(match_str, text)
                if is_fp:
                    continue

                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=PIIType.OTP.value,
                    text=self.mask_value_for_display(match_str, "OTP"),
                    raw_text=match_str,
                    confidence=0.92,
                    confidence_level="HIGH",
                    bbox=bbox,
                    source=["OCR_REGEX", "OTP_VERIFICATION_CONTEXT"],
                    classification=PII_CLASSIFICATION_MAP[PIIType.OTP].value,
                    element_id=block.get("element_id")
                ))
                entity_counter += 1

        # -------------------------------------------------------------
        # 2. DOM SEMANTIC & ATTRIBUTE INSPECTION
        # -------------------------------------------------------------
        for node in dom_nodes or []:
            if isinstance(node, dict):
                tag_name = str(node.get("tag_name") or node.get("tag") or node.get("tagName") or "").upper()
                input_type = str(node.get("inputType") or node.get("type") or "").lower()
                placeholder = str(node.get("placeholder", "")).lower()
                name_attr = str(node.get("name", "")).lower()
                id_attr = str(node.get("id_attr") or node.get("id") or "").lower()
                aria_attr = str(node.get("aria_label") or node.get("ariaLabel") or "").lower()
                node_value = str(node.get("value", ""))
                node_text = str(node.get("text", ""))
                raw_bbox = node.get("bbox")
                element_id = str(node.get("id", ""))
            else:
                tag_name = str(getattr(node, "type", "")).upper()
                attrs = getattr(node, "attributes", {}) or {}
                input_type = str(attrs.get("type", "")).lower()
                placeholder = str(attrs.get("placeholder", "")).lower()
                name_attr = str(attrs.get("name", "")).lower()
                id_attr = str(attrs.get("id_attr", getattr(node, "id", ""))).lower()
                aria_attr = str(attrs.get("aria_label", "")).lower()
                node_value = str(attrs.get("value", ""))
                node_text = str(getattr(node, "text", ""))
                raw_bbox = getattr(node, "bbox", None)
                element_id = str(getattr(node, "id", ""))

            bbox = self._normalize_bbox(raw_bbox)
            if bbox == [0, 0, 0, 0]:
                continue

            pii_type = None
            conf = 0.70
            source_signals = ["DOM_SEMANTICS"]

            # Combined context for attribute matching
            comb_attrs = f"{name_attr} {id_attr} {placeholder} {aria_attr}"

            is_form_control = tag_name in ("INPUT", "TEXTAREA", "SELECT") or input_type != ""

            # Check false positive on value/text
            val_to_check = node_value or node_text
            if val_to_check:
                is_fp, _ = is_false_positive_number(val_to_check, comb_attrs)
                if is_fp:
                    continue

            # (A0) Direct Regex Pattern Match on DOM Node Value
            if node_value:
                if matches_pan(node_value):
                    pii_type = PIIType.PAN
                    conf = 0.95
                    source_signals.append("DOM_VALUE_REGEX_PAN")
                elif matches_card(node_value):
                    pii_type = PIIType.CARD
                    conf = 0.95
                    source_signals.append("DOM_VALUE_REGEX_CARD")
                elif matches_aadhaar(node_value):
                    pii_type = PIIType.AADHAAR
                    conf = 0.95
                    source_signals.append("DOM_VALUE_REGEX_AADHAAR")

            # (A) Password input fields (CRITICAL: highest sensitivity)
            if pii_type is not None:
                pass
            elif input_type == "password" or (is_form_control and any(k in comb_attrs for k in ["pass", "pwd", "secret"])):
                pii_type = PIIType.PASSWORD
                conf = 0.99
                source_signals.append("DOM_INPUT_PASSWORD")

            # (B) OTP / Security code inputs
            elif any(k in comb_attrs for k in ["otp", "2fa", "verification_code", "passcode"]):
                pii_type = PIIType.OTP
                conf = 0.96
                source_signals.append("DOM_OTP_ATTRIBUTE")

            # (C) Credit / Debit Card DOM fields (must be payment context, not UI component card)
            elif is_form_control and (any(k in comb_attrs for k in ["card_number", "card-number", "cardnumber", "card_num", "card-num", "credit_card", "creditcard", "debit_card", "debitcard", "cc-number", "cc_number", "cc-num", "cc_num", "cvv", "cvc", "expiry", "cardholder", "payment_card", "payment-card"]) or (any(c in comb_attrs for c in ["credit", "debit", "payment", "checkout"]) and "card" in comb_attrs)):
                pii_type = PIIType.CARD
                conf = 0.94
                source_signals.append("DOM_PAYMENT_FIELD")

            # (D) Indian PAN Card DOM fields
            elif any(k in comb_attrs for k in ["pan_number", "pan-number", "pannumber", "pan_card", "pan-card", "pancard", "tax_id"]):
                pii_type = PIIType.PAN
                conf = 0.92
                source_signals.append("DOM_PAN_FIELD")

            # (E) Indian Aadhaar DOM fields
            elif any(k in comb_attrs for k in ["aadhaar", "aadhar", "uidai"]):
                pii_type = PIIType.AADHAAR
                conf = 0.92
                source_signals.append("DOM_AADHAAR_FIELD")

            # (F) Email fields
            elif input_type == "email" or (is_form_control and any(k in comb_attrs for k in ["email", "mail", "user_email"])):
                pii_type = PIIType.EMAIL
                conf = 0.93
                source_signals.append("DOM_EMAIL_FIELD")

            # (G) Phone fields
            elif input_type == "tel" or (is_form_control and any(k in comb_attrs for k in ["phone", "tel", "mobile"])):
                pii_type = PIIType.PHONE
                conf = 0.92
                source_signals.append("DOM_TEL_FIELD")

            # (H) Personal Name fields
            elif is_form_control and any(k in comb_attrs for k in ["fullname", "first_name", "last_name", "user_name", "fname", "lname"]):
                pii_type = PIIType.NAME
                conf = 0.85
                source_signals.append("DOM_NAME_FIELD")

            # (I) Physical Address fields
            elif is_form_control and any(k in comb_attrs for k in ["address", "street", "city", "zip", "pincode", "postal"]):
                pii_type = PIIType.ADDRESS
                conf = 0.88
                source_signals.append("DOM_ADDRESS_FIELD")

            # (J) Identification Numbers (SSN, Employee ID)
            elif is_form_control and any(k in comb_attrs for k in ["id_num", "ssn", "gov_id", "national_id"]):
                pii_type = PIIType.ID_NUM
                conf = 0.88
                source_signals.append("DOM_ID_FIELD")

            if pii_type:
                raw_val = node_value or node_text or f"[{pii_type.value} FIELD]"
                masked_val = self.mask_value_for_display(raw_val, pii_type.value)

                detected_entities.append(PIIEntity(
                    id=f"pii-{entity_counter:03d}",
                    type=pii_type.value,
                    text=masked_val,
                    raw_text=raw_val,
                    confidence=conf,
                    confidence_level="HIGH" if conf >= 0.85 else "MEDIUM",
                    bbox=bbox,
                    source=source_signals,
                    classification=PII_CLASSIFICATION_MAP[pii_type].value,
                    element_id=element_id
                ))
                entity_counter += 1

        # -------------------------------------------------------------
        # 3. VISUAL FACE DETECTION (OpenCV Haar Cascade)
        # -------------------------------------------------------------
        if self.face_cascade is not None and screenshot_bytes and len(screenshot_bytes) > 0:
            try:
                nparr = np.frombuffer(screenshot_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(
                        gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30)
                    )
                    for (fx, fy, fw, fh) in faces:
                        detected_entities.append(PIIEntity(
                            id=f"pii-{entity_counter:03d}",
                            type=PIIType.FACE.value,
                            text="[FACE DETECTED]",
                            raw_text="[FACE_REGION]",
                            confidence=0.92,
                            confidence_level="HIGH",
                            bbox=[int(fx), int(fy), int(fx + fw), int(fy + fh)],
                            source=["VISION_HAAR", "OPENCV_FACE_CASCADE"],
                            classification=PII_CLASSIFICATION_MAP[PIIType.FACE].value,
                            element_id=None
                        ))
                        entity_counter += 1
            except Exception:
                pass

        # -------------------------------------------------------------
        # 4. DEDUPLICATION & BOX COALESCENCE
        # -------------------------------------------------------------
        deduplicated = self._deduplicate_entities(detected_entities)
        if deduplicated:
            unique_types = sorted(list(set(e.type for e in deduplicated)))
            global_event_publisher.pii_detected(
                count=len(deduplicated),
                pii_types=unique_types
            )
        return deduplicated

    def _deduplicate_entities(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Merges duplicate entities with overlapping boxes and identical types."""
        if not entities:
            return []

        # Sort by confidence descending
        sorted_entities = sorted(entities, key=lambda e: e.confidence, reverse=True)
        kept: List[PIIEntity] = []

        for entity in sorted_entities:
            is_dup = False
            for existing in kept:
                # Same type and overlapping box
                if existing.type == entity.type:
                    boxA = entity.bbox
                    boxB = existing.bbox
                    # Overlap check
                    xA = max(boxA[0], boxB[0])
                    yA = max(boxA[1], boxB[1])
                    xB = min(boxA[2], boxB[2])
                    yB = min(boxA[3], boxB[3])
                    inter = max(0, xB - xA) * max(0, yB - yA)
                    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
                    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
                    union = areaA + areaB - inter
                    iou = inter / float(union) if union > 0 else 0.0

                    if iou > 0.40 or (entity.element_id and entity.element_id == existing.element_id):
                        # Merge source signals
                        for src in entity.source:
                            if src not in existing.source:
                                existing.source.append(src)
                        is_dup = True
                        break

            if not is_dup:
                kept.append(entity)

        # Re-index IDs
        for i, ent in enumerate(kept):
            ent.id = f"pii-{i+1:03d}"

        return kept
