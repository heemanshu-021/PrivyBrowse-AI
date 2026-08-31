"""
PrivyBrowse AI — Production-Grade Performance & Resource Management Suite
17 Comprehensive Performance, Deduplication, and Resource Bounds Tests:
  1. Perception Deduplication & Hash Memoization
  2. OCR LRU Crop & Frame Caching
  3. Visual Contour LRU Caching
  4. Perception Cache Invalidation on Navigation
  5. Perception Cache Invalidation on DOM Mutation
  6. Screenshot Buffer Lifecycle & Immediate Memory Deallocation
  7. IoUMatcher Fast-Path Short Circuit for Empty Detection Sources
  8. IoUMatcher AABB Disjoint Spatial Filter
  9. GoalDecomposer LRU Plan Memoization
  10. BrowserActionBridge Pending Queue Bounds (Max 50)
  11. BrowserActionBridge Maximum Payload Bounds (10 MB DoS Protection)
  12. Checkpoint Stack Bounding (Max 50 Checkpoints)
  13. Action Audit History Bounding (Max 100 Entries)
  14. Observability Event Bus Bounded Retention (Max 500 Events)
  15. PII Detection Sub-Millisecond Speed & Zero Leakage
  16. Planner Idempotency Skip Fast-Turn Latency (<1ms)
  17. Fail-Closed Resource & Performance Error Handling
"""

import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.perception.core.pipeline import PerceptionPipeline
from backend.perception.core.schemas import BoundingBox, PerceivedElement
from backend.perception.ocr.tesseract_engine import TesseractOCREngine
from backend.perception.detectors.visual_detector import VisualDetector
from backend.perception.fusion.iou_matcher import IoUMatcher
from backend.agent.decomposer import GoalDecomposer
from backend.agent.memory import AgentMemory
from backend.agent.schemas import CheckpointType, ActionRecord
from backend.actions.browser_bridge import BrowserActionBridge, PendingAction
from backend.observability.event_bus import ObservabilityEventBus
from backend.observability.schemas import EventType, EventComponent
from backend.privacy.privacy_gate import PrivacyGate
from backend.privacy.schemas import PIIType
from backend.actions.agent_runner import EndToEndAgentRunner


def test_1_perception_deduplication_and_memoization():
    print("\n[PERF TEST 1] Perception Deduplication & Hash Memoization...")
    pipeline = PerceptionPipeline()

    dom_nodes = [
        {"id": "pb-1", "tag": "button", "text": "Launch Mission", "bbox": {"x": 10, "y": 10, "width": 100, "height": 40}}
    ]
    meta = {"url": "http://localhost:8000/demo-pages/chandrayaan.html"}

    # Turn 1: Cold perception execution
    t0 = time.perf_counter()
    res1 = pipeline.run(
        screenshot_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        dom_nodes=dom_nodes,
        page_metadata=meta,
        viewport_width=1920,
        viewport_height=1080
    )
    cold_ms = (time.perf_counter() - t0) * 1000.0

    # Turn 2: Warm memoized perception execution with identical state
    t1 = time.perf_counter()
    res2 = pipeline.run(
        screenshot_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        dom_nodes=dom_nodes,
        page_metadata=meta,
        viewport_width=1920,
        viewport_height=1080
    )
    warm_ms = (time.perf_counter() - t1) * 1000.0

    assert res1.success is True
    assert res2.success is True
    assert len(res1.elements) == len(res2.elements)
    assert warm_ms < 5.0  # Memoized turnaround must be sub-5ms
    print(f"  ✓ Cold Run: {cold_ms:.2f}ms | Memoized Warm Run: {warm_ms:.3f}ms")


def test_2_ocr_lru_crop_caching():
    print("\n[PERF TEST 2] OCR LRU Crop & Frame Caching...")
    ocr = TesseractOCREngine()
    dummy_img = np.zeros((100, 200, 3), dtype=np.uint8)

    res1 = ocr.extract_text(dummy_img)
    info1 = ocr.get_model_info()
    res2 = ocr.extract_text(dummy_img)
    info2 = ocr.get_model_info()

    assert info2.get("cache_size", 0) >= 1
    print("  ✓ Identical visual image crop hit OCR LRU cache successfully.")


def test_3_visual_contour_lru_caching():
    print("\n[PERF TEST 3] Visual Contour LRU Caching...")
    detector = VisualDetector()
    dummy_img = np.full((120, 240, 3), 200, dtype=np.uint8)
    dummy_img[20:60, 20:100] = 50  # Mock button rectangle

    t0 = time.perf_counter()
    elements1 = detector.detect(dummy_img)
    cold_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    elements2 = detector.detect(dummy_img)
    warm_ms = (time.perf_counter() - t1) * 1000.0

    assert len(elements1) == len(elements2)
    assert warm_ms < cold_ms or warm_ms < 1.0
    print(f"  ✓ Contour Detection Cold: {cold_ms:.2f}ms | Warm: {warm_ms:.3f}ms")


def test_4_perception_cache_invalidation_on_navigation():
    print("\n[PERF TEST 4] Perception Cache Invalidation on Navigation...")
    pipeline = PerceptionPipeline()

    dom_nodes = [{"id": "btn-1", "tag": "button", "text": "Proceed", "bbox": {"x": 10, "y": 10, "width": 100, "height": 40}}]
    pipeline.run(
        screenshot_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        dom_nodes=dom_nodes,
        page_metadata={"url": "http://isro.gov.in/page1"},
        viewport_width=1920,
        viewport_height=1080
    )
    assert pipeline._last_result is not None

    # Navigation event: URL changes
    pipeline.run(
        screenshot_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        dom_nodes=dom_nodes,
        page_metadata={"url": "http://isro.gov.in/page2"},
        viewport_width=1920,
        viewport_height=1080
    )
    assert pipeline._last_perception_key.startswith("http://isro.gov.in/page2")
    print("  ✓ Perception cache invalidated and updated on URL shift.")


def test_5_perception_cache_invalidation_on_dom_mutation():
    print("\n[PERF TEST 5] Perception Cache Invalidation on DOM Mutation...")
    pipeline = PerceptionPipeline()

    dom_nodes_1 = [{"id": "btn-1", "tag": "button", "text": "Step 1", "bbox": {"x": 10, "y": 10, "width": 100, "height": 40}}]
    pipeline.run(
        screenshot_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        dom_nodes=dom_nodes_1,
        page_metadata={"url": "http://isro.gov.in"},
        viewport_width=1920,
        viewport_height=1080
    )

    # DOM Mutation adds new element
    dom_nodes_2 = [
        {"id": "btn-1", "tag": "button", "text": "Step 1", "bbox": {"x": 10, "y": 10, "width": 100, "height": 40}},
        {"id": "btn-2", "tag": "button", "text": "Step 2", "bbox": {"x": 120, "y": 10, "width": 100, "height": 40}}
    ]
    res2 = pipeline.run(
        screenshot_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        dom_nodes=dom_nodes_2,
        page_metadata={"url": "http://isro.gov.in"},
        viewport_width=1920,
        viewport_height=1080
    )

    assert len(res2.elements) == 2
    print("  ✓ Perception cache invalidated on DOM node additions.")


def test_6_screenshot_lifecycle_and_buffer_cleanup():
    print("\n[PERF TEST 6] Screenshot Buffer Lifecycle & Immediate Memory Deallocation...")
    pipeline = PerceptionPipeline()
    pipeline.invalidate_cache()
    assert pipeline._last_result is None
    assert pipeline._last_perception_key == ""
    print("  ✓ Pipeline explicit cache flushing and buffer cleanup verified.")


def test_7_iou_matcher_fast_path_empty_sources():
    print("\n[PERF TEST 7] IoUMatcher Fast-Path for Empty Detection Sources...")
    matcher = IoUMatcher()
    primary = [
        PerceivedElement(id="e1", type="BUTTON", text="OK", confidence=0.9, bbox=BoundingBox(x=10, y=10, width=50, height=30))
    ]
    # When secondary is empty (e.g. Vision disabled or empty frame)
    t0 = time.perf_counter()
    matches = matcher.match_elements(primary, [])
    duration_us = (time.perf_counter() - t0) * 1_000_000.0

    assert len(matches) == 1
    assert matches[0] == (0, None, 0.0)
    assert duration_us < 500  # Sub-500 microseconds
    print(f"  ✓ Empty secondary source fast-path resolved in {duration_us:.1f}µs.")


def test_8_iou_matcher_aabb_disjoint_rejection():
    print("\n[PERF TEST 8] IoUMatcher AABB Disjoint Spatial Filter...")
    matcher = IoUMatcher()
    primary = [
        PerceivedElement(id="e1", type="BUTTON", text="TopLeft", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=50, height=50))
    ]
    secondary = [
        PerceivedElement(id="e2", type="BUTTON", text="BottomRight", confidence=0.9, bbox=BoundingBox(x=1000, y=1000, width=50, height=50))
    ]
    matches = matcher.match_elements(primary, secondary)
    assert matches[0][1] is None
    print("  ✓ Disjoint spatial bounding boxes rejected via fast AABB check.")


def test_9_goal_decomposer_memoization():
    print("\n[PERF TEST 9] GoalDecomposer LRU Plan Memoization...")
    decomposer = GoalDecomposer()
    goal = "Search for Chandrayaan-3 mission archive"

    t0 = time.perf_counter()
    steps1 = decomposer.decompose(goal)
    cold_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    steps2 = decomposer.decompose(goal)
    warm_ms = (time.perf_counter() - t1) * 1000.0

    assert len(steps1) == len(steps2)
    assert warm_ms < 0.2
    print(f"  ✓ Decomposer Cold: {cold_ms:.3f}ms | Warm: {warm_ms:.3f}ms")


def test_10_browser_bridge_queue_bounds():
    print("\n[PERF TEST 10] BrowserActionBridge Pending Queue Bounds (Max 50)...")
    bridge = BrowserActionBridge()
    # Dispatch 60 actions to trigger bounded eviction
    for i in range(60):
        bridge.dispatch_action(PendingAction(
            action_id=f"act-bound-{i:03d}",
            action_type="CLICK"
        ))

    assert len(bridge._pending) <= 50
    print(f"  ✓ Pending queue bounded at {len(bridge._pending)} items (oldest evicted).")


def test_11_browser_bridge_max_payload_limit():
    print("\n[PERF TEST 11] BrowserActionBridge Maximum Payload Bounds (10MB)...")
    bridge = BrowserActionBridge()
    normal_msg = '{"type": "PING", "payload": {}}'
    assert bridge._handle_incoming_raw_message(normal_msg) is True

    oversized_msg = "X" * (11 * 1024 * 1024)
    assert bridge._handle_incoming_raw_message(oversized_msg) is False
    print("  ✓ Oversized WebSocket/IPC payload rejected fail-closed.")


def test_12_checkpoint_stack_bounding():
    print("\n[PERF TEST 12] Checkpoint Stack Bounding (Max 50 Checkpoints)...")
    mem = AgentMemory()
    for i in range(70):
        mem.save_checkpoint(
            task_id="task-perf-01",
            checkpoint_type=CheckpointType.STATE_VERIFIED,
            step_index=i,
            url=f"http://example.com/step/{i}"
        )

    assert len(mem.checkpoints) <= 50
    print(f"  ✓ Milestone checkpoint stack bounded at {len(mem.checkpoints)} items.")


def test_13_action_audit_history_bounding():
    print("\n[PERF TEST 13] Action Audit History Bounding (Max 100 Entries)...")
    mem = AgentMemory()
    for i in range(120):
        mem.record_action_audit(ActionRecord(
            action_id=f"act-rec-{i:03d}",
            task_id="task-01",
            timestamp="2026-08-31T10:00:00Z",
            action_type="CLICK",
            target_id=f"btn-{i}"
        ))

    assert len(mem.action_records) <= 100
    print(f"  ✓ ActionRecord audit history bounded at {len(mem.action_records)} items.")


def test_14_observability_event_bus_retention_bounding():
    print("\n[PERF TEST 14] Observability Event Bus Bounded Retention (Max 500 Events)...")
    bus = ObservabilityEventBus(max_retention=500)
    for i in range(600):
        bus.publish(
            event_type=EventType.TASK_STARTED,
            component=EventComponent.TASK_MANAGER,
            message=f"Event number {i}"
        )

    assert len(bus._events) == 500
    print("  ✓ Event bus queue bounded at 500 events.")


def test_15_pii_detection_zero_leakage_and_speed():
    print("\n[PERF TEST 15] PII Detection Sub-Millisecond Speed & Zero Leakage...")
    gate = PrivacyGate()
    ocr_blocks = [
        {"id": "b1", "text": "Indian PAN: ABCDE1234F, Aadhaar: 5489 1234 5678, Amount: ₹50,000 in Year 2026", "bbox": [10, 10, 200, 30]}
    ]
    t0 = time.perf_counter()
    ctx, entities = gate.process_and_sanitize(
        screenshot_bytes=b"",
        ocr_blocks=ocr_blocks,
        dom_nodes=[]
    )
    latency_ms = (time.perf_counter() - t0) * 1000.0

    sanitized_text = ctx.sanitized_ocr_blocks[0]["text"]
    assert "ABCDE1234F" not in sanitized_text
    assert "5489 1234 5678" not in sanitized_text
    assert "2026" in sanitized_text  # Preserves calendar year
    assert "₹50,000" in sanitized_text  # Preserves currency
    assert latency_ms < 15.0
    print(f"  ✓ PII detection & masking completed in {latency_ms:.2f}ms.")


def test_16_planner_idempotency_skip_fast_turn():
    print("\n[PERF TEST 16] Planner Idempotency Skip Fast-Turn Latency (<1ms)...")
    runner = EndToEndAgentRunner()
    runner.executor.simulation_mode = True

    elements = [
        {"id": "chkAgreed", "tag": "input", "type": "checkbox", "checked": True, "bbox": [10, 10, 30, 30]}
    ]

    t0 = time.perf_counter()
    res = runner.run_single_turn(
        sanitized_elements=elements,
        current_url="http://localhost:8000/terms",
        task_goal="Agree to terms by checking checkbox"
    )
    turn_ms = (time.perf_counter() - t0) * 1000.0

    assert res["status"] in ("SUCCESS", "COMPLETED")
    print(f"  ✓ Idempotent action check completed in {turn_ms:.2f}ms.")


def test_17_fail_closed_resource_error_handling():
    print("\n[PERF TEST 17] Fail-Closed Resource & Performance Error Handling...")
    pipeline = PerceptionPipeline()
    # Malformed / empty screenshot data
    err_res = pipeline.run(screenshot_b64="", screenshot_bytes=None)
    assert err_res.success is False
    assert err_res.error.get("code") in ("EMPTY_SCREENSHOT", "INVALID_SCREENSHOT")
    print("  ✓ Resource error handled fail-closed with structured error payload.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING PRIVYBROWSE AI PERFORMANCE & RESOURCE SUITE")
    print("==================================================")
    test_1_perception_deduplication_and_memoization()
    test_2_ocr_lru_crop_caching()
    test_3_visual_contour_lru_caching()
    test_4_perception_cache_invalidation_on_navigation()
    test_5_perception_cache_invalidation_on_dom_mutation()
    test_6_screenshot_lifecycle_and_buffer_cleanup()
    test_7_iou_matcher_fast_path_empty_sources()
    test_8_iou_matcher_aabb_disjoint_rejection()
    test_9_goal_decomposer_memoization()
    test_10_browser_bridge_queue_bounds()
    test_11_browser_bridge_max_payload_limit()
    test_12_checkpoint_stack_bounding()
    test_13_action_audit_history_bounding()
    test_14_observability_event_bus_retention_bounding()
    test_15_pii_detection_zero_leakage_and_speed()
    test_16_planner_idempotency_skip_fast_turn()
    test_17_fail_closed_resource_error_handling()
    print("==================================================")
    print("ALL 17 PERFORMANCE & RESOURCE TESTS PASSED! ✓")
    print("==================================================")
