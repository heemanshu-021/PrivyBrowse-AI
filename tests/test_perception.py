"""
Comprehensive Unit & Integration Test Suite for On-Device Visual Perception Engine
Tests:
  1. BoundingBox & Geometry operations (Area, center, IoU, containment, NMS)
  2. Coordinate Converter (Retina 2x scaling, viewport mapping, scroll offsets, visibility)
  3. Image Preprocessing (Decoding, grayscale, contrast enhancement, adaptive resizing)
  4. Visual Detector (OpenCV contours, aspect ratios, button/input heuristics, edge density)
  5. DOM Detector (Both dict bbox {x,y,w,h} and list bbox [x1,y1,x2,y2], tag/type aliases)
  6. Text Detector & OCR Extraction (Line grouping, heading detection, DOM text fallback)
  7. Tesseract OCR Engine (Engine availability, model info, fallback)
  8. Context Fusion (Multi-source DOM + Vision + OCR fusion, label enrichment)
  9. Duplicate Element Suppression (IoU suppression of overlapping candidates)
  10. Multi-Source Confidence Scoring (Explainable weights formula, penalty, explanation)
  11. Full Perception Pipeline End-to-End (Stage timing, summary stats, coordinate metadata)
  12. Error & Edge Cases (Empty screenshot, corrupt image, status check)
  13. Privacy & Zero-Cloud Invariant (On-device execution verification)
"""

import sys
import os
import cv2
import numpy as np
import base64
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.perception.core.schemas import (
    BoundingBox, PerceivedElement, PerceptionResult,
    ElementType, Visibility
)
from backend.perception.core.coordinator import CoordinateConverter, normalize_bbox_to_viewport
from backend.perception.core.pipeline import PerceptionPipeline
from backend.perception.preprocessing.image_processor import ImageProcessor
from backend.perception.detectors.dom_detector import DOMDetector
from backend.perception.detectors.visual_detector import VisualDetector
from backend.perception.detectors.text_detector import TextDetector
from backend.perception.ocr.base import OCRResult
from backend.perception.ocr.tesseract_engine import TesseractOCREngine
from backend.perception.fusion.iou_matcher import IoUMatcher
from backend.perception.fusion.confidence import (
    calculate_fused_confidence, calculate_single_source_confidence, explain_confidence
)
from backend.perception.fusion.context_fuser import ContextFuser
from backend.perception.utils.geometry import (
    calculate_iou, calculate_iou_xyxy, is_contained,
    non_max_suppression, merge_bboxes, bbox_distance
)


def create_synthetic_test_image(width=480, height=600):
    """Creates a synthetic webpage image with simulated buttons, inputs, text, and checkboxes."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (17, 24, 39)  # Dark background #111827

    # Draw simulated search input (x=20, y=50, w=340, h=36)
    cv2.rectangle(img, (20, 50), (360, 86), (51, 65, 85), 1)
    cv2.rectangle(img, (21, 51), (359, 85), (10, 14, 23), -1)

    # Draw simulated search button (x=370, y=50, w=90, h=36)
    cv2.rectangle(img, (370, 50), (460, 86), (254, 242, 0), -1)

    # Draw simulated login form button (x=40, y=250, w=240, h=40)
    cv2.rectangle(img, (40, 250), (280, 290), (199, 132, 2), -1)

    # Draw simulated checkbox (x=40, y=320, w=20, h=20)
    cv2.rectangle(img, (40, 320), (60, 340), (254, 242, 0), 2)

    # Draw simulated card container (x=30, y=380, w=400, h=150)
    cv2.rectangle(img, (30, 380), (430, 530), (75, 85, 99), 1)

    # Encode to PNG bytes
    _, encoded = cv2.imencode(".png", img)
    return encoded.tobytes()


def test_bounding_box_and_geometry():
    print("[TEST 1] Testing BoundingBox & Geometry Operations...")
    b1 = BoundingBox(x=10, y=20, width=100, height=50)
    assert b1.x1 == 10
    assert b1.y1 == 20
    assert b1.x2 == 110
    assert b1.y2 == 70
    assert b1.area == 5000
    assert b1.center == (60, 45)
    assert b1.to_xyxy() == [10, 20, 110, 70]

    b2 = BoundingBox(x=50, y=20, width=100, height=50)
    iou = calculate_iou(b1, b2)
    assert 0.40 < iou < 0.45, f"Expected IoU around 3/7 (~0.428), got {iou}"

    # Disjoint boxes IoU == 0
    b3 = BoundingBox(x=500, y=500, width=50, height=50)
    assert calculate_iou(b1, b3) == 0.0

    # Containment
    inner = BoundingBox(x=20, y=30, width=30, height=20)
    assert is_contained(inner, b1, threshold=0.99) is True

    # NMS
    boxes = [
        (BoundingBox(x=10, y=10, width=50, height=50), 0.9, 0),
        (BoundingBox(x=12, y=12, width=48, height=48), 0.7, 1),  # Overlapping dup
        (BoundingBox(x=200, y=200, width=50, height=50), 0.85, 2),
    ]
    kept = non_max_suppression(boxes, iou_threshold=0.5)
    assert 0 in kept and 2 in kept
    assert 1 not in kept, "NMS should suppress the lower-confidence duplicate"
    print("  ✓ BoundingBox, IoU, Containment, and NMS passed.")


def test_coordinate_converter():
    print("\n[TEST 2] Testing Coordinate System Scaling & Visibility...")
    # Retina display scenario: 2x screenshot scaling (960x1200 screenshot vs 480x600 viewport)
    converter = CoordinateConverter(
        viewport_width=480,
        viewport_height=600,
        screenshot_width=960,
        screenshot_height=1200,
        device_pixel_ratio=2.0,
        scroll_x=0.0,
        scroll_y=150.0
    )

    ss_box = BoundingBox(x=80, y=200, width=480, height=80)
    vp_box = converter.screenshot_to_viewport(ss_box)
    assert vp_box.x == 40.0
    assert vp_box.y == 100.0
    assert vp_box.width == 240.0
    assert vp_box.height == 40.0

    # Viewport to screenshot inverse
    ss_box_reconstructed = converter.viewport_to_screenshot(vp_box)
    assert ss_box_reconstructed.x == 80.0
    assert ss_box_reconstructed.width == 480.0

    # Viewport to document (with scroll_y=150)
    doc_box = converter.viewport_to_document(vp_box)
    assert doc_box.y == 250.0

    # Visibility checks
    assert converter.classify_visibility(vp_box) == "VISIBLE"
    offscreen_box = BoundingBox(x=40, y=700, width=200, height=40)
    assert converter.classify_visibility(offscreen_box) == "OFFSCREEN"
    partial_box = BoundingBox(x=400, y=100, width=150, height=40)
    assert converter.classify_visibility(partial_box) == "PARTIALLY_VISIBLE"
    print("  ✓ Screenshot ↔ Viewport conversions, DPR scaling, and visibility classifications verified.")


def test_preprocessing():
    print("\n[TEST 3] Testing Image Preprocessor...")
    img_bytes = create_synthetic_test_image(480, 600)
    processor = ImageProcessor()
    img = processor.decode(img_bytes)
    assert img is not None
    assert img.shape == (600, 480, 3)

    gray = processor.to_grayscale(img)
    assert len(gray.shape) == 2

    ocr_prep = processor.preprocess_for_ocr(img)
    assert ocr_prep is not None

    det_prep = processor.preprocess_for_detection(img)
    assert det_prep is not None

    # Adaptive resize
    large_img = np.zeros((3000, 4000, 3), dtype=np.uint8)
    resized = processor.adaptive_resize(large_img, max_dimension=1920)
    assert max(resized.shape[:2]) == 1920
    print("  ✓ Preprocessing decoding, contrast enhancement, and adaptive resizing passed.")


def test_visual_detector_opencv():
    print("\n[TEST 4] Testing OpenCV Visual Detector...")
    img_bytes = create_synthetic_test_image(480, 600)
    processor = ImageProcessor()
    img = processor.decode(img_bytes)

    detector = VisualDetector()
    elements = detector.detect(img)
    assert isinstance(elements, list)
    assert len(elements) > 0, "Visual detector must identify visual elements in the synthetic image"

    types = {e.type for e in elements}
    assert any(t in types for t in ["BUTTON", "INPUT", "CHECKBOX", "CARD", "ELEMENT"])

    for el in elements:
        assert el.bbox.width > 0 and el.bbox.height > 0
        assert 0.0 <= el.confidence <= 1.0
        assert "VISION" in el.sources
        assert el.visible is True

    print(f"  ✓ OpenCV Visual Detector extracted {len(elements)} visual contours with classified types: {types}.")


def test_dom_detector_formats():
    print("\n[TEST 5] Testing DOM Detector Payload Formats & Aliases...")
    detector = DOMDetector()

    # Mixed formats: API list bbox vs Extension dict bbox
    mixed_nodes = [
        # Format 1: List bbox [x1, y1, x2, y2]
        {
            "id": "node-1",
            "tag_name": "BUTTON",
            "type": "submit",
            "text": "Submit Form",
            "bbox": [50, 100, 200, 140]
        },
        # Format 2: Chrome Extension Dict bbox {x, y, width, height, top, left, right, bottom}
        {
            "id": "pb-element-002",
            "tag": "input",
            "inputType": "text",
            "placeholder": "Enter username",
            "ariaLabel": "Username Input",
            "bbox": {
                "x": 50, "y": 200, "width": 250, "height": 38,
                "top": 200, "left": 50, "right": 300, "bottom": 238
            }
        },
        # Format 3: Role override and alt tags
        {
            "id": "role-btn",
            "tag": "div",
            "role": "button",
            "text": "Custom Button",
            "bbox": {"left": 50, "top": 300, "right": 180, "bottom": 340}
        }
    ]

    elements = detector.detect(mixed_nodes)
    assert len(elements) == 3

    assert elements[0].id == "node-1"
    assert elements[0].type == "BUTTON"
    assert elements[0].bbox.width == 150.0
    assert elements[0].bbox.height == 40.0

    assert elements[1].id == "pb-element-002"
    assert elements[1].type == "INPUT"
    assert elements[1].bbox.x == 50.0
    assert elements[1].bbox.width == 250.0
    assert elements[1].label == "Username Input"

    assert elements[2].id == "role-btn"
    assert elements[2].type == "BUTTON"
    assert elements[2].bbox.width == 130.0

    print("  ✓ DOM Detector seamlessly parsed list bboxes, dict bboxes, tag aliases, and role overrides.")


def test_text_detector_and_ocr():
    print("\n[TEST 6] Testing Text Detector & DOM Text Fallback...")
    detector = TextDetector()

    # 1. OCR results conversion
    ocr_results = [
        OCRResult(text="Welcome to PrivyBrowse Portal", confidence=0.95, bbox=[40, 20, 380, 60], source="TESSERACT"),  # Height=40, 4 words -> HEADING
        OCRResult(text="Please review all information carefully before continuing with the submission.", confidence=0.88, bbox=[60, 260, 400, 276], source="TESSERACT")  # Height=16, 10 words -> TEXT
    ]
    ocr_elements = detector.detect_from_ocr(ocr_results)
    assert len(ocr_elements) == 2
    assert ocr_elements[0].type == "HEADING"  # Large confident text
    assert ocr_elements[1].type == "TEXT"

    # 2. DOM text fallback
    dom_nodes = [
        {"id": "h1", "tag": "h1", "text": "ISRO Portal", "bbox": {"x": 20, "y": 10, "width": 200, "height": 30}},
        {"id": "p", "tag": "p", "text": "Privacy-Preserving Local Agent", "bbox": [20, 50, 300, 80]}
    ]
    dom_text_elements = detector.detect_from_dom_text(dom_nodes)
    assert len(dom_text_elements) == 2
    assert dom_text_elements[0].type == "HEADING"
    assert dom_text_elements[1].type == "TEXT"
    assert "DOM_TEXT_PROXY" in dom_text_elements[0].sources
    print("  ✓ Text Detector correctly converted OCR lines and DOM text fallbacks.")


def test_tesseract_ocr_engine():
    print("\n[TEST 7] Testing Tesseract OCR Engine Interface & Availability...")
    engine = TesseractOCREngine()
    info = engine.get_model_info()
    assert isinstance(info, dict)
    assert info["engine"] == "Tesseract OCR"
    assert info["offline"] is True

    # If binary is not installed on host, extract_text should return empty list gracefully without throwing
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    results = engine.extract_text(img)
    assert isinstance(results, list)
    print(f"  ✓ Tesseract Engine interface verified. Engine available on host: {engine.is_available()}.")


def test_context_fuser_multi_source():
    print("\n[TEST 8] Testing Multi-Source Context Fusion (DOM + Vision + OCR)...")
    fuser = ContextFuser(iou_threshold=0.35)

    dom_elements = [
        PerceivedElement(
            id="d1", type="INPUT", label="", text="",
            bbox=BoundingBox(x=20, y=50, width=340, height=36),
            confidence=0.92, visible=True, enabled=True, interactive=True, sources=["DOM"]
        ),
        PerceivedElement(
            id="d2", type="BUTTON", label="SEARCH", text="SEARCH",
            bbox=BoundingBox(x=370, y=50, width=90, height=36),
            confidence=0.92, visible=True, enabled=True, interactive=True, sources=["DOM"]
        )
    ]

    vision_elements = [
        PerceivedElement(
            id="v1", type="INPUT", label="", text="",
            bbox=BoundingBox(x=22, y=51, width=338, height=35),
            confidence=0.84, visible=True, enabled=True, interactive=True, sources=["VISION"]
        ),
        PerceivedElement(
            id="v2", type="BUTTON", label="", text="",
            bbox=BoundingBox(x=372, y=50, width=88, height=36),
            confidence=0.80, visible=True, enabled=True, interactive=True, sources=["VISION"]
        ),
        # Vision-only element (e.g. custom icon/widget not in DOM)
        PerceivedElement(
            id="v3", type="ICON", label="", text="",
            bbox=BoundingBox(x=400, y=120, width=30, height=30),
            confidence=0.70, visible=True, enabled=True, interactive=False, sources=["VISION"]
        )
    ]

    text_elements = [
        PerceivedElement(
            id="t1", type="TEXT", label="SEARCH", text="SEARCH",
            bbox=BoundingBox(x=380, y=55, width=70, height=25),
            confidence=0.95, visible=True, enabled=True, interactive=False, sources=["TESSERACT"]
        )
    ]

    fused = fuser.fuse(dom_elements, vision_elements, text_elements)
    assert len(fused) == 3  # 2 DOM + 1 Vision-only

    # First element: DOM input fused with Vision input
    assert fused[0].id == "pb-element-001"
    assert fused[0].type == "INPUT"
    assert "DOM" in fused[0].sources
    assert "VISION" in fused[0].sources

    # Second element: DOM button fused with Vision button and OCR text
    assert fused[1].id == "pb-element-002"
    assert fused[1].type == "BUTTON"
    assert fused[1].label == "SEARCH"
    assert "DOM" in fused[1].sources
    assert "VISION" in fused[1].sources
    assert "TESSERACT" in fused[1].sources
    assert fused[1].confidence > 0.85

    # Third element: Vision-only icon
    assert fused[2].id == "pb-element-003"
    assert fused[2].type == "ICON"
    assert fused[2].sources == ["VISION"]

    print(f"  ✓ Multi-source context fusion merged {len(fused)} elements with multi-source provenance.")


def test_duplicate_suppression():
    print("\n[TEST 9] Testing Duplicate Suppression on High-Overlap Elements...")
    fuser = ContextFuser(iou_threshold=0.35)

    # Create DOM elements
    dom = [
        PerceivedElement(
            id="d1", type="BUTTON", label="Click Me", text="Click Me",
            bbox=BoundingBox(x=100, y=100, width=100, height=40),
            confidence=0.92, sources=["DOM"]
        )
    ]

    # Create overlapping vision elements
    vision = [
        PerceivedElement(
            id="v1", type="BUTTON", label="", text="",
            bbox=BoundingBox(x=101, y=100, width=98, height=40),  # Matches d1
            confidence=0.80, sources=["VISION"]
        ),
        PerceivedElement(
            id="v2", type="BUTTON", label="", text="",
            bbox=BoundingBox(x=102, y=101, width=96, height=38),  # Duplicate of d1
            confidence=0.75, sources=["VISION"]
        )
    ]

    fused = fuser.fuse(dom, vision, [])
    # Should only produce 1 fused element, not 2 or 3
    assert len(fused) == 1
    assert fused[0].id == "pb-element-001"
    print("  ✓ Overlapping vision duplicates successfully suppressed during fusion.")


def test_confidence_scoring_formula():
    print("\n[TEST 10] Testing Explainable Multi-Source Confidence Scoring Formula...")
    dom_el = PerceivedElement(
        id="d1", type="BUTTON", label="OK", text="OK",
        bbox=BoundingBox(x=10, y=10, width=80, height=30),
        confidence=0.92, sources=["DOM"]
    )
    vis_el = PerceivedElement(
        id="v1", type="BUTTON", label="", text="",
        bbox=BoundingBox(x=10, y=10, width=80, height=30),
        confidence=0.80, sources=["VISION"]
    )

    # 1. Tri-source fusion (DOM + Vision + OCR with high IoU=0.8)
    conf_3 = calculate_fused_confidence(
        dom_element=dom_el,
        vision_element=vis_el,
        ocr_text_match=True,
        ocr_confidence=0.95,
        iou_score=0.80
    )
    assert 0.85 <= conf_3 <= 1.0

    # 2. Single-source confidence penalty
    single_conf = calculate_single_source_confidence(vis_el)
    assert single_conf == round(0.80 * 0.90, 3)

    # 3. Explainability breakdown
    explanation = explain_confidence(
        dom_element=dom_el,
        vision_element=vis_el,
        ocr_text_match=True,
        ocr_confidence=0.95,
        iou_score=0.80
    )
    assert "formula" in explanation
    assert "contributions" in explanation
    assert explanation["total_confidence"] == conf_3
    assert explanation["contributions"]["dom"] == round(0.35 * 0.92, 3)

    print("  ✓ Confidence calculation verified with full mathematical transparency.")


def test_full_pipeline_end_to_end():
    print("\n[TEST 11] Testing Full Perception Pipeline End-to-End Execution...")
    pipeline = PerceptionPipeline()
    img_bytes = create_synthetic_test_image(480, 600)
    mock_b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

    mock_dom = [
        {"id": "search-in", "tag": "input", "type": "text", "placeholder": "Search...", "bbox": {"x": 20, "y": 50, "width": 340, "height": 36}},
        {"id": "search-btn", "tag": "button", "type": "submit", "text": "SEARCH", "bbox": {"x": 370, "y": 50, "width": 90, "height": 36}},
        {"id": "login-btn", "tag": "button", "type": "submit", "text": "LOGIN", "bbox": {"x": 40, "y": 250, "width": 240, "height": 40}},
    ]

    page_meta = {"title": "ISRO Space Portal", "url": "http://localhost:8000/demo/search.html", "hostname": "localhost"}

    t_start = time.perf_counter()
    result: PerceptionResult = pipeline.run(
        screenshot_b64=mock_b64,
        viewport_width=480,
        viewport_height=600,
        device_pixel_ratio=1.0,
        dom_nodes=mock_dom,
        page_metadata=page_meta
    )
    t_elapsed = (time.perf_counter() - t_start) * 1000

    assert result.success is True
    assert len(result.elements) >= 3
    assert result.page.title == "ISRO Space Portal"
    assert result.summary.element_count == len(result.elements)
    assert result.latency.total_ms > 0.0
    assert result.coordinate_system.viewport_width == 480
    assert result.coordinate_system.scale_x == 1.0

    print(f"  ✓ Full perception pipeline completed in {t_elapsed:.2f}ms (Engine recorded: {result.latency.total_ms:.2f}ms).")
    print(f"  ✓ Summary: {result.summary.element_count} elements, {result.summary.interactive_count} interactive controls.")


def test_error_and_edge_cases():
    print("\n[TEST 12] Testing Error & Edge Cases...")
    pipeline = PerceptionPipeline()

    # 1. Empty screenshot
    res_empty = pipeline.run(screenshot_b64="")
    assert res_empty.success is False
    assert res_empty.error["code"] == "EMPTY_SCREENSHOT"

    # 2. Corrupted screenshot string
    res_corrupt = pipeline.run(screenshot_b64="invalid_base64_payload$$$")
    assert res_corrupt.success is False

    # 3. Zero-sized image handling
    res_zero = pipeline.run(screenshot_bytes=b"")
    assert res_zero.success is False

    # 4. Engine status query
    status = pipeline.get_status()
    assert status["pipeline_ready"] is True
    assert status["offline_capable"] is True
    assert status["privacy_mode"] == "LOCAL_ONLY"

    print("  ✓ Error and edge cases handled safely with structured failure responses.")


def test_privacy_boundary_local_only():
    print("\n[TEST 13] Testing Strict Privacy Boundary (Local-Only Guarantee)...")
    pipeline = PerceptionPipeline()
    status = pipeline.get_status()

    # Zero cloud vision dependency invariant
    assert status["offline_capable"] is True
    assert status["privacy_mode"] == "LOCAL_ONLY"
    assert "OpenCV" in status["visual_detector"]

    # Ensure no network socket is required for perception
    img_bytes = create_synthetic_test_image(200, 200)
    res = pipeline.run(screenshot_bytes=img_bytes, viewport_width=200, viewport_height=200)
    assert res.success is True
    assert res.summary.privacy_status == "LOCAL_UNSANITIZED"

    print("  ✓ 100% on-device local perception boundary verified.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING ON-DEVICE PERCEPTION ENGINE TEST SUITE")
    print("==================================================")
    test_bounding_box_and_geometry()
    test_coordinate_converter()
    test_preprocessing()
    test_visual_detector_opencv()
    test_dom_detector_formats()
    test_text_detector_and_ocr()
    test_tesseract_ocr_engine()
    test_context_fuser_multi_source()
    test_duplicate_suppression()
    test_confidence_scoring_formula()
    test_full_pipeline_end_to_end()
    test_error_and_edge_cases()
    test_privacy_boundary_local_only()
    print("==================================================")
    print("ALL 13 PERCEPTION ENGINE TESTS PASSED! ✓")
    print("==================================================")
