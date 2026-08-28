import sys
import os
import base64

# Append project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.perception.element_detector import ElementDetector
from backend.perception.ocr_engine import OCREngine
from backend.privacy.pii_detector import PIIDetector
from backend.privacy.redactor import Redactor
from backend.agent.planner import AgentPlanner
from backend.agent.validator import ActionValidator

def run_tests():
    print("==================================================")
    print("STARTING ON-DEVICE PERCEPTION ENGINE VALIDATION")
    print("==================================================")

    # 1. Mock Base64 Image
    # 1x1 black pixel PNG
    mock_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    image_bytes = base64.b64decode(mock_png_b64)

    # 2. Test OpenCV Element Detector
    print("\n[TEST 1] Testing OpenCV Contour Element Detector...")
    detector = ElementDetector()
    detected_elements = detector.detect_elements(image_bytes)
    print(f"✓ Detected elements list returned successfully. Count: {len(detected_elements)}")
    assert isinstance(detected_elements, list), "Should return a list"

    # 3. Test OCR Engine layout extraction
    print("\n[TEST 2] Testing OCR Engine layout mapping...")
    ocr = OCREngine()
    mock_dom = [
        {"id": "dom_0", "tag_name": "INPUT", "type": "email", "text": "", "value": "amit.sharma@example.com", "bbox": [10, 100, 300, 130]}
    ]
    ocr_blocks = ocr.extract_text(mock_dom)
    print(f"✓ OCR blocks count: {len(ocr_blocks)}")
    assert isinstance(ocr_blocks, list), "Should return a list"

    # 4. Test PII Detector
    print("\n[TEST 3] Testing PII Pattern Classifier...")
    pii_filter = PIIDetector()
    ocr_blocks_test = [
        {"id": "ocr_0", "text": "Contact us at support@sih2026.gov.in or 9876543210", "bbox": [10, 10, 400, 30]}
    ]
    detected_pii = pii_filter.detect_pii(image_bytes, ocr_blocks_test, mock_dom)
    print(f"✓ Detected PII count: {len(detected_pii)}")
    for p in detected_pii:
        print(f"  - Category: {p['type']}, Confidence: {p['confidence']}, Source: {p['source']}")
    assert len(detected_pii) >= 2, "Should find email and phone from mock OCR + DOM"

    # 5. Test Redaction Engine
    print("\n[TEST 4] Testing Redaction Engine...")
    redactor = Redactor()
    redacted_bytes, redacted_dom = redactor.redact(image_bytes, detected_pii, mock_dom, redaction_style="opaque")
    print(f"✓ Visual redaction completed. Output image bytes length: {len(redacted_bytes)}")
    print(f"✓ DOM redaction completed. Redacted DOM: {redacted_dom}")
    assert "[REDACTED_EMAIL]" in redacted_dom[0]["value"] or "[EMAIL REDACTED]" in redacted_dom[0]["value"], "DOM email value should be redacted"

    # 6. Test Agent Planner & Action Validator
    print("\n[TEST 5] Testing Agent Planner & Safety Validation...")
    planner = AgentPlanner()
    validator = ActionValidator()
    
    fused_mock = [
        {"id": "dom_0", "type": "INPUT", "bbox": [10, 100, 300, 130], "text": "[EMAIL REDACTED]", "value": "[EMAIL REDACTED]", "attributes": {"tag_name": "INPUT", "type": "email"}},
        {"id": "dom_2", "type": "INPUT", "bbox": [10, 200, 300, 230], "text": "", "value": "", "attributes": {"tag_name": "INPUT", "type": "password"}},
        {"id": "dom_3", "type": "BUTTON", "bbox": [10, 300, 150, 340], "text": "Login", "value": "", "attributes": {"tag_name": "BUTTON"}}
    ]
    
    planned_action = planner.plan_action("Login to portal", fused_mock, [])
    print(f"✓ Planner decision: {planned_action}")
    assert planned_action["action"] == "TYPE", "Should type password as email is already filled/redacted"
    
    is_valid, msg = validator.validate_action(planned_action)
    print(f"✓ Action validation check: {msg} (Is Valid: {is_valid})")
    assert is_valid, "Action should be valid"

    print("\n==================================================")
    print("ALL LOCAL CORE SERVICES VALIDATED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
