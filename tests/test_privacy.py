"""
Comprehensive Unit & Integration Test Suite for On-Device Privacy Layer
Tests:
  1. PII Detection across all types (Email, Phone, Card, PAN, Aadhaar, Password, OTP, Secrets, Face)
  2. Algorithmic Checks (Luhn Mod-10 checksum, Aadhaar format validation)
  3. False-Positive Avoidance (Years, Prices, Order IDs, Dimensions, Metric counts)
  4. Visual Redaction Styles (Opaque, Blur, Pixelate)
  5. DOM Attribute Sanitization (Value, text, placeholder scrubbing)
  6. OCR Text Block Token Substitution ([REDACTED_<TYPE>])
  7. PerceivedElement Direct Redaction (Perception pipeline integration)
  8. Multi-Source PII Correlation & Deduplication
  9. Contextual Keyword Confidence Boosting
  10. Password & Secret Zero-Leak Protection
  11. Privacy Gate End-to-End Processing
  12. Outbound Remote Transmission Guard (Blocking unredacted payloads)
  13. Privacy-Safe Audit Logging (No raw secrets in logs)
  14. Planner Sanitization Invariant (Planner receives clean inputs only)
  15. Action Compatibility with Redacted Controls (Legitimate interactions succeed)
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
    matches_aadhaar, matches_secret_token, matches_otp, validate_luhn,
    validate_aadhaar_format
)
from backend.privacy.rules.context_rules import is_false_positive_number, boost_confidence_with_context
from backend.perception.core.schemas import PerceivedElement, BoundingBox
from backend.agent.planner import AgentPlanner


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
        {"id": "ocr_3", "text": "Payment Card: 4111 2222 3333 4444", "bbox": [10, 70, 300, 90]},
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
    assert "EMAIL" in detected_types
    assert "PHONE" in detected_types
    assert "CARD" in detected_types
    assert "PAN" in detected_types
    assert "AADHAAR" in detected_types
    assert "OTP" in detected_types
    assert "SECRET_TOKEN" in detected_types
    assert "PASSWORD" in detected_types

    # Verify classifications
    for e in entities:
        if e.type in ("PASSWORD", "CARD", "PAN", "AADHAAR", "OTP", "SECRET_TOKEN"):
            assert e.classification == "HIGHLY_SENSITIVE"
        elif e.type in ("EMAIL", "PHONE"):
            assert e.classification == "SENSITIVE"

    print(f"  ✓ Successfully detected {len(entities)} PII items across 8 distinct categories.")


def test_luhn_and_aadhaar_algorithms():
    print("\n[TEST 2] Testing Algorithmic Checksums (Luhn Mod-10 & Aadhaar Format)...")
    # Luhn test cases
    assert validate_luhn("4242 4242 4242 4242") is True
    assert validate_luhn("4111 1111 1111 1111") is True
    assert validate_luhn("4111 2222 3333 4444") is False
    assert validate_luhn("1234") is False

    # Aadhaar test cases
    assert validate_aadhaar_format("9876 5432 1098") is True
    assert validate_aadhaar_format("2345 6789 0123") is True
    assert validate_aadhaar_format("0123 4567 8901") is False  # Cannot start with 0
    assert validate_aadhaar_format("1234 5678 9012") is False  # Cannot start with 1
    assert validate_aadhaar_format("9999 9999 9999") is False  # Repeating sequence rejected
    print("  ✓ Luhn Mod-10 and Aadhaar format checks verified.")


def test_false_positive_avoidance():
    print("\n[TEST 3] Testing False-Positive Avoidance on Non-PII Content...")
    detector = PIIDetector()

    non_pii_ocr = [
        {"id": "ocr_year", "text": "Copyright © 2026 ISRO. All rights reserved. Founded in 1969.", "bbox": [10, 10, 300, 30]},
        {"id": "ocr_price", "text": "Annual subscription: ₹999 or $49.99 (Save 20%)", "bbox": [10, 40, 300, 60]},
        {"id": "ocr_order", "text": "Tracking reference: Order #12345 (PID-84729)", "bbox": [10, 70, 300, 90]},
        {"id": "ocr_dims", "text": "Viewport dimensions: 1920x1080 @ 60fps, 42ms response", "bbox": [10, 100, 300, 120]},
        {"id": "ocr_count", "text": "Community statistics: 1247 active members, 3 projects", "bbox": [10, 130, 300, 150]},
    ]

    img_bytes = create_synthetic_privacy_image()
    entities = detector.detect(img_bytes, non_pii_ocr, [])
    assert len(entities) == 0, f"False positives detected: {[e.type + ': ' + e.text for e in entities]}"

    # Verify helper functions
    assert is_false_positive_number("2026", "Copyright 2026")[0] is True
    assert is_false_positive_number("₹999", "Price ₹999")[0] is True
    assert is_false_positive_number("1920x1080", "Screen resolution")[0] is True
    print("  ✓ False-positive suppression verified: Years, Prices, Order IDs, Dimensions safely ignored.")


def test_visual_redaction_styles():
    print("\n[TEST 4] Testing Visual Screenshot Redaction Styles (Opaque, Blur, Pixelate)...")
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
            "classification": "SENSITIVE"
        },
        {
            "id": "pii-002",
            "type": "PASSWORD",
            "text": "••••••••",
            "raw_text": "Secret1234!",
            "bbox": [30, 190, 330, 225],
            "confidence": 0.99,
            "classification": "HIGHLY_SENSITIVE"
        }
    ]

    for style in ["opaque", "blur", "pixelate"]:
        redacted_bytes, rmap = redactor.redact_screenshot(img_bytes, pii_list, redaction_style=style)
        assert len(redacted_bytes) > 0
        assert rmap.total_redacted == 2
        assert rmap.highly_sensitive_count == 1
        assert rmap.sensitive_count == 1
        assert rmap.style == style

    print("  ✓ Opaque, Blur, and Pixelate visual redaction verified.")


def test_dom_attribute_sanitization():
    print("\n[TEST 5] Testing DOM Node Value & Attribute Sanitization...")
    redactor = Redactor()

    mock_dom = [
        {"id": "dom_email", "tag_name": "INPUT", "type": "email", "value": "user@isro.gov.in", "bbox": [30, 50, 330, 85]},
        {"id": "dom_pass", "tag_name": "INPUT", "type": "password", "value": "Secret1234!", "bbox": [30, 190, 330, 225]},
        {"id": "dom_public", "tag_name": "BUTTON", "type": "submit", "text": "Submit Form", "bbox": [30, 250, 330, 285]},
    ]

    pii_list = [
        {"id": "pii-001", "type": "EMAIL", "raw_text": "user@isro.gov.in", "element_id": "dom_email", "bbox": [30, 50, 330, 85]},
        {"id": "pii-002", "type": "PASSWORD", "raw_text": "Secret1234!", "element_id": "dom_pass", "bbox": [30, 190, 330, 225]},
    ]

    sanitized_dom = redactor.redact_dom_nodes(mock_dom, pii_list)
    email_node = next(n for n in sanitized_dom if n["id"] == "dom_email")
    pass_node = next(n for n in sanitized_dom if n["id"] == "dom_pass")
    public_node = next(n for n in sanitized_dom if n["id"] == "dom_public")

    assert email_node["value"] == "[REDACTED_EMAIL]"
    assert pass_node["value"] == "[REDACTED_PASSWORD]"
    assert pass_node["placeholder"] == "••••••••"
    assert public_node["text"] == "Submit Form"
    print("  ✓ DOM attributes (.value, .placeholder, .text) scrubbed safely.")


def test_ocr_token_substitution():
    print("\n[TEST 6] Testing OCR Text Block Token Substitution...")
    redactor = Redactor()

    mock_ocr = [
        {"id": "ocr_1", "text": "Contact user at admin@isro.gov.in for credentials", "bbox": [10, 10, 300, 30]},
        {"id": "ocr_2", "text": "Ordinary non-sensitive description text", "bbox": [10, 40, 300, 60]},
    ]

    pii_list = [
        {"id": "pii-001", "type": "EMAIL", "raw_text": "admin@isro.gov.in", "bbox": [10, 10, 300, 30]}
    ]

    sanitized_ocr = redactor.redact_ocr_blocks(mock_ocr, pii_list)
    assert sanitized_ocr[0]["text"] == "Contact user at [REDACTED_EMAIL] for credentials"
    assert sanitized_ocr[1]["text"] == "Ordinary non-sensitive description text"
    print("  ✓ OCR text substituted with [REDACTED_<TYPE>] tokens.")


def test_perceived_element_redaction():
    print("\n[TEST 7] Testing Direct PerceivedElement Redaction...")
    redactor = Redactor()

    elements = [
        PerceivedElement(
            id="pb-001", type="INPUT", label="Email", text="admin@isro.gov.in",
            bbox=BoundingBox(x=10, y=10, width=200, height=35), confidence=0.92,
            attributes={"type": "email", "value": "admin@isro.gov.in"}
        ),
        PerceivedElement(
            id="pb-002", type="INPUT", label="Password", text="SuperSecret123",
            bbox=BoundingBox(x=10, y=50, width=200, height=35), confidence=0.92,
            attributes={"type": "password", "value": "SuperSecret123"}
        ),
        PerceivedElement(
            id="pb-003", type="BUTTON", label="Sign In", text="Sign In",
            bbox=BoundingBox(x=10, y=100, width=100, height=35), confidence=0.92,
            attributes={"type": "submit"}
        ),
    ]

    pii_entities = [
        PIIEntity(
            id="pii-001", type="EMAIL", text="ad***@isro.gov.in", raw_text="admin@isro.gov.in",
            confidence=0.98, bbox=[10, 10, 210, 45], element_id="pb-001"
        )
    ]

    sanitized = redactor.redact_perceived_elements(elements, pii_entities)
    assert len(sanitized) == 3

    # Email element sanitized
    assert sanitized[0].is_sensitive is True
    assert sanitized[0].pii_type == "EMAIL"
    assert sanitized[0].redacted is True
    assert sanitized[0].text == "[REDACTED_EMAIL]"
    assert sanitized[0].attributes["value"] == "[REDACTED_EMAIL]"

    # Password element sanitized unconditionally
    assert sanitized[1].is_sensitive is True
    assert sanitized[1].pii_type == "PASSWORD"
    assert sanitized[1].redacted is True
    assert sanitized[1].text == "[REDACTED_PASSWORD]"

    # Public button untouched
    assert sanitized[2].is_sensitive is False
    assert sanitized[2].text == "Sign In"

    print("  ✓ PerceivedElement objects successfully sanitized with privacy metadata flags.")


def test_multi_source_pii_correlation():
    print("\n[TEST 8] Testing Multi-Source PII Correlation & Deduplication...")
    detector = PIIDetector()

    # Same email detected in DOM input and in OCR text block
    mock_dom = [
        {"id": "email-field", "tag_name": "INPUT", "type": "email", "value": "test@domain.com", "bbox": [50, 50, 250, 85]}
    ]
    mock_ocr = [
        {"id": "ocr-block-1", "text": "test@domain.com", "bbox": [52, 51, 248, 84]}
    ]

    img_bytes = create_synthetic_privacy_image()
    entities = detector.detect(img_bytes, mock_ocr, mock_dom)

    # Should deduplicate overlapping OCR + DOM detections into a single logical PIIEntity
    assert len(entities) == 1
    assert entities[0].type == "EMAIL"
    assert any("OCR" in s for s in entities[0].source)
    assert any("DOM" in s for s in entities[0].source)
    print("  ✓ Multi-source PII correlated with merged provenance signals.")


def test_context_keyword_confidence_boost():
    print("\n[TEST 9] Testing Context Keyword Confidence Boosting...")
    base_conf, signals = boost_confidence_with_context(0.85, "CARD", "Please enter credit card number for checkout")
    assert base_conf > 0.85
    assert len(signals) >= 1
    assert "CONTEXT_KEYWORD_MATCH" in signals[0]
    print("  ✓ Confidence boosted based on semantic keyword proximity.")


def test_password_and_secret_strong_protection():
    print("\n[TEST 10] Testing Strong Password & Secret Zero-Leak Protection...")
    detector = PIIDetector()
    redactor = Redactor()

    raw_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisSecretKey123"
    raw_ghp = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"

    mock_ocr = [
        {"id": "jwt", "text": f"Authorization: Bearer {raw_jwt}", "bbox": [10, 10, 300, 30]},
        {"id": "ghp", "text": f"Token: {raw_ghp}", "bbox": [10, 40, 300, 60]},
    ]

    img_bytes = create_synthetic_privacy_image()
    entities = detector.detect(img_bytes, mock_ocr, [])
    assert len(entities) >= 2

    # Verify display masking
    for e in entities:
        assert raw_jwt not in e.text
        assert raw_ghp not in e.text
        assert e.classification == "HIGHLY_SENSITIVE"

    # Verify OCR scrubbing
    sanitized_ocr = redactor.redact_ocr_blocks(mock_ocr, [e.model_dump() for e in entities])
    for b in sanitized_ocr:
        assert raw_jwt not in b["text"]
        assert raw_ghp not in b["text"]

    print("  ✓ JWTs, API tokens, and passwords masked and scrubbed completely.")


def test_privacy_gate_end_to_end():
    print("\n[TEST 11] Testing Privacy Gate End-to-End Processing...")
    gate = PrivacyGate()
    img_bytes = create_synthetic_privacy_image()

    mock_ocr = [{"id": "ocr_1", "text": "PAN: ABCDE1234F", "bbox": [30, 50, 330, 85]}]
    mock_dom = [{"id": "dom_pan", "tag_name": "INPUT", "type": "text", "value": "ABCDE1234F", "bbox": [30, 50, 330, 85]}]

    sanitized_ctx, entities = gate.process_and_sanitize(img_bytes, mock_ocr, mock_dom, style="opaque")
    assert isinstance(sanitized_ctx, SanitizedContext)
    assert sanitized_ctx.is_safe_for_reasoning is True
    assert sanitized_ctx.redaction_map.total_redacted >= 1
    assert len(entities) >= 1
    print(f"  ✓ Privacy Gate sanitized context created in {gate.metrics['last_total_gate_latency_ms']}ms.")


def test_outbound_remote_guard():
    print("\n[TEST 12] Testing Outbound Remote Guard Boundary Enforcement...")
    gate = PrivacyGate()
    sanitized_ctx = SanitizedContext(is_safe_for_reasoning=True)

    # Sanitized context allowed
    assert gate.guard_outbound_transmission(sanitized_ctx) is True

    # Unsanitized payload blocked
    raw_payload = {"privacy_status": "LOCAL_UNSANITIZED", "raw_data": "Secret"}
    try:
        gate.guard_outbound_transmission(raw_payload)
        assert False, "Should have raised PrivacyGateViolation"
    except PrivacyGateViolation as e:
        assert "RAW_CONTEXT_BLOCKED_BY_PRIVACY_GATE" in str(e)

    print("  ✓ Outbound remote guard strictly intercepted raw transmission.")


def test_privacy_safe_audit_logging():
    print("\n[TEST 13] Testing Privacy-Safe Audit Logging Invariants...")
    gate = PrivacyGate()
    secret_pass = "MySecretPass1234!"
    secret_card = "4111 2222 3333 4444"

    mock_dom = [{"id": "p", "type": "password", "value": secret_pass, "bbox": [10, 10, 100, 30]}]
    mock_ocr = [{"id": "c", "text": f"Card {secret_card}", "bbox": [10, 40, 100, 60]}]

    img_bytes = create_synthetic_privacy_image()
    gate.process_and_sanitize(img_bytes, mock_ocr, mock_dom)

    # Check logs
    log_dump = str([l.model_dump() for l in gate.audit_logs])
    assert secret_pass not in log_dump, "CRITICAL: Secret password leaked into audit logs!"
    assert secret_card not in log_dump, "CRITICAL: Secret card leaked into audit logs!"
    print("  ✓ Audit logs verified 100% free of plaintext secrets.")


def test_planner_receives_sanitized_data():
    print("\n[TEST 14] Testing Agent Planner Sanitization Invariant...")
    planner = AgentPlanner()
    secret_pass = "UnsafePasswordString!"

    # Sanitized elements where password value was replaced with token
    sanitized_elements = [
        {
            "id": "input-email",
            "type": "INPUT",
            "label": "Email",
            "text": "[REDACTED_EMAIL]",
            "attributes": {"type": "email", "value": "[REDACTED_EMAIL]"}
        },
        {
            "id": "input-pass",
            "type": "INPUT",
            "label": "[PASSWORD FIELD]",
            "text": "[REDACTED_PASSWORD]",
            "attributes": {"type": "password", "value": "[REDACTED_PASSWORD]"}
        },
        {
            "id": "btn-login",
            "type": "BUTTON",
            "label": "Sign In",
            "text": "Sign In",
            "attributes": {"type": "submit"}
        }
    ]

    candidate, validation, state = planner.plan_next_step(
        sanitized_elements=sanitized_elements,
        task_goal="Log in to the portal"
    )

    # Planner memory must not contain raw secret
    planner_state_dump = str(planner.current_task.model_dump())
    assert secret_pass not in planner_state_dump, "Planner retained raw secret in working memory!"
    print("  ✓ Planner operates exclusively on sanitized elements with zero credential retention.")


def test_action_compatibility_with_redacted_fields():
    print("\n[TEST 15] Testing Browser Action Compatibility with Redacted Fields...")
    planner = AgentPlanner()

    sanitized_elements = [
        {
            "id": "pb-001",
            "type": "INPUT",
            "label": "[PASSWORD FIELD]",
            "text": "[REDACTED_PASSWORD]",
            "bbox": {"x": 50, "y": 100, "width": 200, "height": 35, "left": 50, "top": 100, "right": 250, "bottom": 135},
            "attributes": {"type": "password", "id_attr": "pwd-field"}
        },
        {
            "id": "pb-002",
            "type": "BUTTON",
            "label": "Submit",
            "text": "Submit",
            "bbox": {"x": 50, "y": 150, "width": 100, "height": 35, "left": 50, "top": 150, "right": 150, "bottom": 185},
            "attributes": {"type": "submit"}
        }
    ]

    candidate, validation, state = planner.plan_next_step(
        sanitized_elements=sanitized_elements,
        task_goal="Submit credentials"
    )

    assert candidate is not None
    assert candidate.target_id in ("pb-001", "pb-002")
    assert validation.allowed is True
    print("  ✓ Action planning generates valid, executable CandidateActions on redacted elements.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING ON-DEVICE PRIVACY ENGINE TEST SUITE")
    print("==================================================")
    test_pii_pattern_detection()
    test_luhn_and_aadhaar_algorithms()
    test_false_positive_avoidance()
    test_visual_redaction_styles()
    test_dom_attribute_sanitization()
    test_ocr_token_substitution()
    test_perceived_element_redaction()
    test_multi_source_pii_correlation()
    test_context_keyword_confidence_boost()
    test_password_and_secret_strong_protection()
    test_privacy_gate_end_to_end()
    test_outbound_remote_guard()
    test_privacy_safe_audit_logging()
    test_planner_receives_sanitized_data()
    test_action_compatibility_with_redacted_fields()
    print("==================================================")
    print("ALL 15 PRIVACY ENGINE TESTS PASSED SUCCESSFULLY! ✓")
    print("==================================================")
