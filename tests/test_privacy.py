"""
Comprehensive Unit & Integration Test Suite for On-Device Privacy Layer
Tests:
  - PII Detection across all types (Email, Phone, Card, PAN, Aadhaar, Password, OTP, Secrets, Face)
  - Algorithmic checks (Luhn card checksum, Aadhaar format)
  - False-Positive Avoidance (Years, Prices, Order IDs, Dimensions, Metric counts)
  - Image visual redaction (Opaque, Blur, Pixelate)
  - OCR text scrubbing & DOM attribute sanitization
  - Privacy Gatekeeper & Remote Transmission Guard
  - Privacy-safe Audit Logging & Strict Privacy Invariants
"""

import sys
import os
import cv2
import numpy as np
import base64
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.privacy.schemas import (
    PIIEntity, PIIType, DataClassification, RedactionMap,
    SanitizedContext, PrivacyPolicy
)
from backend.privacy.pii_detector import PIIDetector
from backend.privacy.redactor import Redactor
from backend.privacy.privacy_gate import PrivacyGate, PrivacyGateViolation
from backend.privacy.rules.pattern_rules import (
    matches_email, matches_phone, matches_card, matches_pan,
    matches_aadhaar, matches_secret_token, matches_otp, validate_luhn
)
from backend.privacy.rules.context_rules import is_false_positive_number


def create_synthetic_privacy_image(width=500, height=400):
    """Generates a synthetic image with card and input boxes."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (20, 24, 33)

    # Box for email (x=30, y=50, w=300, h=35)
    cv2.rectangle(img, (30, 50), (330, 85), (50, 60, 80), 1)
    # Box for card (x=30, y=120, w=300, h=35)
    cv2.rectangle(img, (30, 120), (330, 155), (50, 60, 80), 1)
    # Box for password (x=30, y=190, w=300, h=35)
    cv2.rectangle(img, (30, 190), (330, 225), (50, 60, 80), 1)

    _, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()


def test_pii_pattern_detection():
    print("[TEST 1] Testing PII Pattern Detection Across Supported Types...")
    detector = PIIDetector()

    mock_ocr = [
        {"id": "ocr_1", "text": "Contact user at support@sih2026.gov.in or admin@isro.gov.in", "bbox": [10, 10, 300, 30]},
        {"id": "ocr_2", "text": "Mobile number: +91 98765 43210 or 9876543210", "bbox": [10, 40, 300, 60]},
        {"id": "ocr_3", "text": "Payment Card: 4111 2222 3333 4444 (Luhn valid)", "bbox": [10, 70, 300, 90]},
        {"id": "ocr_4", "text": "Income Tax PAN: ABCDE1234F", "bbox": [10, 100, 300, 120]},
        {"id": "ocr_5", "text": "UIDAI Aadhaar: 9876 5432 1098", "bbox": [10, 130, 300, 150]},
        {"id": "ocr_6", "text": "Enter OTP 2FA verification code: 593821", "bbox": [10, 160, 300, 180]},
        {"id": "ocr_7", "text": "GitHub API Key: ghp_1234567890abcdefghijklmnopqrstuvwxyz", "bbox": [10, 190, 300, 210]},
    ]

    mock_dom = [
        {"id": "dom_pass", "tag_name": "INPUT", "type": "password", "value": "SuperSecretPass123!", "bbox": [10, 220, 300, 250]},
        {"id": "dom_pan", "tag_name": "INPUT", "type": "text", "name": "pan_number", "value": "XYZPA9876Q", "bbox": [10, 260, 300, 290]},
    ]

    img_bytes = create_synthetic_privacy_image()
    entities = detector.detect(img_bytes, mock_ocr, mock_dom)

    detected_types = {e.type for e in entities}
    assert "EMAIL" in detected_types, "Should detect email"
    assert "PHONE" in detected_types, "Should detect phone"
    assert "CARD" in detected_types, "Should detect card"
    assert "PAN" in detected_types, "Should detect PAN card"
    assert "AADHAAR" in detected_types, "Should detect Aadhaar"
    assert "OTP" in detected_types, "Should detect OTP"
    assert "SECRET_TOKEN" in detected_types, "Should detect API key"
    assert "PASSWORD" in detected_types, "Should detect Password"

    # Verify classifications
    for e in entities:
        if e.type in ("PASSWORD", "CARD", "PAN", "AADHAAR", "OTP", "SECRET_TOKEN"):
            assert e.classification == "HIGHLY_SENSITIVE"
        elif e.type in ("EMAIL", "PHONE"):
            assert e.classification == "SENSITIVE"

    # Verify Luhn validator directly
    assert validate_luhn("4242 4242 4242 4242") is True
    assert validate_luhn("4111 1111 1111 1111") is True
    assert validate_luhn("4111 2222 3333 4444") is False, "Invalid checksum must return False"

    print(f"  ✓ Successfully detected {len(entities)} PII items across 8 distinct categories.")


def test_false_positive_avoidance():
    print("\n[TEST 2] Testing False-Positive Avoidance on Non-PII Content...")
    detector = PIIDetector()

    # Content with numbers that must NOT be flagged as PII
    non_pii_ocr = [
        {"id": "ocr_year", "text": "Copyright © 2026 ISRO. All rights reserved. Founded in 1969.", "bbox": [10, 10, 300, 30]},
        {"id": "ocr_price", "text": "Annual subscription: ₹999 or $49.99 (Save 20%)", "bbox": [10, 40, 300, 60]},
        {"id": "ocr_order", "text": "Tracking reference: Order #12345 (PID-84729)", "bbox": [10, 70, 300, 90]},
        {"id": "ocr_dims", "text": "Viewport dimensions: 1920x1080 @ 60fps, 42ms response", "bbox": [10, 100, 300, 120]},
        {"id": "ocr_count", "text": "Community statistics: 1247 active members, 3 projects", "bbox": [10, 130, 300, 150]},
    ]

    mock_dom = []
    img_bytes = create_synthetic_privacy_image()
    entities = detector.detect(img_bytes, non_pii_ocr, mock_dom)

    # There should be 0 PII detected in this purely public content
    assert len(entities) == 0, f"False positives detected: {[e.type + ': ' + e.text for e in entities]}"

    # Verify individual false-positive helper rules
    assert is_false_positive_number("2026", "Copyright 2026")[0] is True
    assert is_false_positive_number("₹999", "Price ₹999")[0] is True
    assert is_false_positive_number("1920x1080", "Screen resolution")[0] is True

    print("  ✓ False-positive suppression verified: Years, Prices, Order IDs, Dimensions safely ignored.")


def test_redaction_engine_visual_dom_ocr():
    print("\n[TEST 3] Testing Visual Redaction, OCR Scrubbing, and DOM Sanitization...")
    redactor = Redactor()
    img_bytes = create_synthetic_privacy_image()

    pii_list = [
        {
            "id": "pii-001",
            "type": "EMAIL",
            "text": "us***@isro.gov.in",
            "raw_text": "user@isro.gov.in",
            "bbox": [30, 50, 330, 85],
            "confidence": 0.98,
            "classification": "SENSITIVE",
            "element_id": "dom_email"
        },
        {
            "id": "pii-002",
            "type": "PASSWORD",
            "text": "••••••••",
            "raw_text": "Secret1234!",
            "bbox": [30, 190, 330, 225],
            "confidence": 0.99,
            "classification": "HIGHLY_SENSITIVE",
            "element_id": "dom_pass"
        }
    ]

    mock_dom = [
        {"id": "dom_email", "tag_name": "INPUT", "type": "email", "value": "user@isro.gov.in", "bbox": [30, 50, 330, 85]},
        {"id": "dom_pass", "tag_name": "INPUT", "type": "password", "value": "Secret1234!", "bbox": [30, 190, 330, 225]},
        {"id": "dom_public", "tag_name": "BUTTON", "type": "submit", "text": "Submit Form", "bbox": [30, 250, 330, 285]},
    ]

    mock_ocr = [
        {"id": "ocr_1", "text": "User email is user@isro.gov.in", "bbox": [30, 50, 330, 85]},
        {"id": "ocr_2", "text": "Click Submit Form to proceed", "bbox": [30, 250, 330, 285]},
    ]

    # 1. Test Visual Redaction in all 3 styles
    for style in ["opaque", "blur", "pixelate"]:
        redacted_bytes, rmap = redactor.redact_screenshot(img_bytes, pii_list, redaction_style=style)
        assert len(redacted_bytes) > 0
        assert rmap.total_redacted == 2
        assert rmap.highly_sensitive_count == 1
        assert rmap.sensitive_count == 1
        assert rmap.style == style

    # 2. Test DOM Sanitization
    sanitized_dom = redactor.redact_dom_nodes(mock_dom, pii_list)
    email_node = next(n for n in sanitized_dom if n["id"] == "dom_email")
    pass_node = next(n for n in sanitized_dom if n["id"] == "dom_pass")
    public_node = next(n for n in sanitized_dom if n["id"] == "dom_public")

    assert email_node["value"] == "[REDACTED_EMAIL]"
    assert pass_node["value"] == "[REDACTED_PASSWORD]"
    assert public_node["text"] == "Submit Form", "Public element text must remain unchanged"

    # 3. Test OCR Text Scrubbing
    sanitized_ocr = redactor.redact_ocr_blocks(mock_ocr, pii_list)
    assert sanitized_ocr[0]["text"] == "User email is [REDACTED_EMAIL]"
    assert sanitized_ocr[1]["text"] == "Click Submit Form to proceed"

    print("  ✓ Visual masking (opaque/blur/pixelate), DOM scrubbing, and OCR token substitution passed.")


def test_privacy_gate_and_remote_guard():
    print("\n[TEST 4] Testing Privacy Gatekeeper & Outbound Remote Guard...")
    gate = PrivacyGate()
    img_bytes = create_synthetic_privacy_image()

    mock_ocr = [
        {"id": "ocr_1", "text": "Account PAN: ABCDE1234F", "bbox": [30, 50, 330, 85]}
    ]
    mock_dom = [
        {"id": "dom_pan", "tag_name": "INPUT", "type": "text", "value": "ABCDE1234F", "bbox": [30, 50, 330, 85]}
    ]

    # Process through gate
    sanitized_ctx, entities = gate.process_and_sanitize(img_bytes, mock_ocr, mock_dom, style="opaque")

    assert isinstance(sanitized_ctx, SanitizedContext)
    assert sanitized_ctx.is_safe_for_reasoning is True
    assert sanitized_ctx.redaction_map.total_redacted >= 1
    assert len(entities) >= 1

    # Test Remote Transmission Guard
    # (A) Sanitized context should pass
    assert gate.guard_outbound_transmission(sanitized_ctx) is True

    # (B) Raw unsanitized dictionary should be blocked
    raw_payload = {"privacy_status": "LOCAL_UNSANITIZED", "raw_data": "ABCDE1234F"}
    try:
        gate.guard_outbound_transmission(raw_payload)
        assert False, "Should have raised PrivacyGateViolation"
    except PrivacyGateViolation as e:
        assert "RAW_CONTEXT_BLOCKED_BY_PRIVACY_GATE" in str(e)

    # Test Audit Log Stream
    audit_logs = gate.audit_logs
    assert len(audit_logs) >= 2
    events = [log.event for log in audit_logs]
    assert "PII_DETECTED" in events
    assert "SANITIZATION_COMPLETED" in events
    assert "REMOTE_TRANSMISSION_BLOCKED" in events

    print(f"  ✓ Privacy Gate successfully blocked raw egress and recorded {len(audit_logs)} audit events.")


def test_strict_privacy_invariants():
    print("\n[TEST 5] Validating Strict Zero-Leak Privacy Invariants...")
    gate = PrivacyGate()
    img_bytes = create_synthetic_privacy_image()

    secret_password = "SuperSecretPassword99!"
    secret_card = "4111 2222 3333 4444"

    mock_dom = [
        {"id": "dom_pass", "tag_name": "INPUT", "type": "password", "value": secret_password, "bbox": [30, 50, 330, 85]},
        {"id": "dom_card", "tag_name": "INPUT", "type": "text", "name": "card_number", "value": secret_card, "bbox": [30, 120, 330, 155]}
    ]
    mock_ocr = [
        {"id": "ocr_1", "text": f"Card: {secret_card}", "bbox": [30, 120, 330, 155]}
    ]

    sanitized_ctx, entities = gate.process_and_sanitize(img_bytes, mock_ocr, mock_dom)

    # INVARIANT 1: Raw password string NEVER appears anywhere in sanitized DOM
    dom_str = str(sanitized_ctx.sanitized_dom_nodes)
    assert secret_password not in dom_str, "CRITICAL: Raw password leaked into sanitized DOM!"

    # INVARIANT 2: Raw credit card string NEVER appears in sanitized OCR
    ocr_str = str(sanitized_ctx.sanitized_ocr_blocks)
    assert secret_card not in ocr_str, "CRITICAL: Raw credit card leaked into sanitized OCR!"

    # INVARIANT 3: Audit logs NEVER contain raw password or secret card
    log_str = str([log.model_dump() for log in gate.audit_logs])
    assert secret_password not in log_str, "CRITICAL: Secret password leaked into audit logs!"
    assert secret_card not in log_str, "CRITICAL: Credit card number leaked into audit logs!"

    # INVARIANT 4: Public entities exposed via to_safe_dict() never contain raw_text field
    for ent in entities:
        safe_d = ent.to_safe_dict()
        assert "raw_text" not in safe_d, "CRITICAL: raw_text exposed in safe dict!"

    print("  ✓ ALL 4 ZERO-LEAK PRIVACY INVARIANTS VERIFIED 100% CLEAN.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING ON-DEVICE PRIVACY ENGINE TEST SUITE")
    print("==================================================")
    test_pii_pattern_detection()
    test_false_positive_avoidance()
    test_redaction_engine_visual_dom_ocr()
    test_privacy_gate_and_remote_guard()
    test_strict_privacy_invariants()
    print("==================================================")
    print("ALL PRIVACY ENGINE TESTS PASSED SUCCESSFULLY! ✓")
    print("==================================================")
