"""
Comprehensive Unit & Integration Test Suite for On-Device Visual Perception Engine
Tests:
  - BoundingBox & Coordinate conversions
  - Preprocessing & image decoding
  - Visual element contour detection
  - DOM element detection & normalization
  - Text & OCR detection
  - IoU matching & NMS duplicate suppression
  - Multi-source confidence scoring
  - Context fusion & stable ID assignment
  - Full perception pipeline integration
  - Error and edge-case handling
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
from backend.perception.fusion.iou_matcher import IoUMatcher
from backend.perception.fusion.confidence import calculate_fused_confidence, calculate_single_source_confidence
from backend.perception.fusion.context_fuser import ContextFuser
from backend.perception.utils.geometry import (
    calculate_iou, calculate_iou_xyxy, is_contained,
    non_max_suppression, merge_bboxes, bbox_distance
)


def create_synthetic_test_image(width=480, height=600):
    """Creates a synthetic webpage image with simulated buttons and input boxes."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (17, 24, 39) # Dark background #111827

    # Draw simulated search input (x=20, y=50, w=340, h=36)
    cv2.rectangle(img, (20, 50), (360, 86), (51, 65, 85), 1)
    cv2.rectangle(img, (21, 51), (359, 85), (10, 14, 23), -1)

    # Draw simulated search button (x=370, y=50, w=90, h=36)
    cv2.rectangle(img, (370, 50), (460, 86), (254, 242, 0), -1)

    # Draw simulated login form button (x=40, y=250, w=240, h=40)
    cv2.rectangle(img, (40, 250), (280, 290), (199, 132, 2), -1)

    # Draw simulated checkbox (x=40, y=320, w=20, h=20)
    cv2.rectangle(img, (40, 320), (60, 340), (254, 242, 0), 2)

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
        (BoundingBox(x=12, y=12, width=48, height=48), 0.7, 1), # Overlapping dup
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

    # Visibility checks
    assert converter.classify_visibility(vp_box) == "VISIBLE"
    offscreen_box = BoundingBox(x=40, y=700, width=200, height=40)
    assert converter.classify_visibility(offscreen_box) == "OFFSCREEN"
    partial_box = BoundingBox(x=400, y=100, width=150, height=40)
    assert converter.classify_visibility(partial_box) == "PARTIALLY_VISIBLE"
    print("  ✓ Screenshot ↔ Viewport conversions and visibility classifications verified.")


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


def test_detectors_and_fusion():
    print("\n[TEST 4] Testing DOM, Visual Detectors, and Context Fuser...")
    img_bytes = create_synthetic_test_image(480, 600)
    processor = ImageProcessor()
    img = processor.decode(img_bytes)

    # 1. Visual detection
    vis_detector = VisualDetector()
    vis_elements = vis_detector.detect(img)
    assert isinstance(vis_elements, list)
    assert len(vis_elements) > 0, "Should detect synthetic visual contours"

    # 2. DOM detection
    dom_detector = DOMDetector()
    mock_dom = [
        {"id": "dom_0", "tag_name": "INPUT", "type": "text", "placeholder": "Search...", "bbox": [20, 50, 360, 86]},
        {"id": "dom_1", "tag_name": "BUTTON", "type": "submit", "text": "SEARCH", "bbox": [370, 50, 460, 86]},
        {"id": "dom_2", "tag_name": "BUTTON", "type": "button", "text": "LOGIN", "bbox": [40, 250, 280, 290]},
    ]
    dom_elements = dom_detector.detect(mock_dom)
    assert len(dom_elements) == 3
    assert dom_elements[0].type == "INPUT"
    assert dom_elements[1].type == "BUTTON"

    # 3. Text detection
    text_detector = TextDetector()
    text_elements = text_detector.detect_from_dom_text(mock_dom)
    assert len(text_elements) >= 2 # Buttons have text

    # 4. Context fusion
    fuser = ContextFuser(iou_threshold=0.35)
    fused = fuser.fuse(dom_elements, vis_elements, text_elements)
    assert len(fused) >= 3

    # Verify stable IDs
    assert fused[0].id == "pb-element-001"
    assert fused[1].id == "pb-element-002"
    assert fused[2].id == "pb-element-003"

    # Verify confidence calculation
    for el in fused:
        assert 0.0 <= el.confidence <= 1.0
        assert len(el.sources) > 0

    print(f"  ✓ Fused {len(fused)} elements with stable IDs and multi-source confidence.")


def test_full_pipeline_integration():
    print("\n[TEST 5] Testing Full Perception Pipeline Integration...")
    pipeline = PerceptionPipeline()
    img_bytes = create_synthetic_test_image(480, 600)
    mock_b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

    mock_dom = [
        {"id": "dom_0", "tag_name": "INPUT", "type": "text", "placeholder": "Search...", "bbox": [20, 50, 360, 86]},
        {"id": "dom_1", "tag_name": "BUTTON", "type": "submit", "text": "SEARCH", "bbox": [370, 50, 460, 86]},
        {"id": "dom_2", "tag_name": "BUTTON", "type": "submit", "text": "LOGIN", "bbox": [40, 250, 280, 290]},
    ]

    page_meta = {"title": "Synthetic Test Portal", "url": "http://localhost:8000/demo/synthetic_eval.html"}

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
    assert result.page.title == "Synthetic Test Portal"
    assert result.summary.element_count == len(result.elements)
    assert result.latency.total_ms > 0.0
    assert result.coordinate_system.viewport_width == 480

    print(f"  ✓ Full pipeline executed successfully in {t_elapsed:.2f}ms (Engine recorded: {result.latency.total_ms:.2f}ms).")
    print(f"  ✓ Summary: {result.summary.element_count} elements, {result.summary.interactive_count} interactive, OCR engine: {result.summary.ocr_engine}")


def test_error_and_edge_cases():
    print("\n[TEST 6] Testing Error and Edge Cases...")
    pipeline = PerceptionPipeline()

    # 1. Empty screenshot
    res_empty = pipeline.run(screenshot_b64="")
    assert res_empty.success is False
    assert res_empty.error["code"] == "EMPTY_SCREENSHOT"

    # 2. Corrupted screenshot
    res_corrupt = pipeline.run(screenshot_b64="not-a-valid-base64-string!!!")
    assert res_corrupt.success is False
    assert "SCREENSHOT" in res_corrupt.error["code"] or "IMAGE" in res_corrupt.error["code"]

    # 3. Status check
    status = pipeline.get_status()
    assert status["pipeline_ready"] is True
    assert status["offline_capable"] is True
    assert status["privacy_mode"] == "LOCAL_ONLY"
    print("  ✓ Error handling and status query validated.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING ON-DEVICE PERCEPTION ENGINE TEST SUITE")
    print("==================================================")
    test_bounding_box_and_geometry()
    test_coordinate_converter()
    test_preprocessing()
    test_detectors_and_fusion()
    test_full_pipeline_integration()
    test_error_and_edge_cases()
    print("==================================================")
    print("ALL PERCEPTION ENGINE TESTS PASSED SUCCESSFULLY! ✓")
    print("==================================================")
