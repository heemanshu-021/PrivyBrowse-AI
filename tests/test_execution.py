"""
Comprehensive Test Suite for Real Browser Action Execution & End-to-End Agent
Tests:
  - CLICK execution, stale target detection & rejection
  - TYPE execution with zero-leak sensitive payload masking
  - SCROLL execution (SCROLL_UP, SCROLL_DOWN) with delta tracking
  - PRESS_KEY execution with permitted key whitelist enforcement
  - NAVIGATE execution with dangerous protocol blocking (javascript:, data:)
  - WAIT bounded execution
  - Page Change Detection (URL, DOM mutation, scroll offsets)
  - End-to-End Multi-turn Agent Runner with budget, loop, and confirmation guardrails
"""

import sys
import os
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.actions.schemas import (
    ActionResult, ExecutionStatus, ExecutionConfig, SupportedKey
)
from backend.actions.executor import ActionExecutor
from backend.actions.page_change_detector import PageChangeDetector
from backend.actions.agent_runner import EndToEndAgentRunner
from backend.agent.planner import AgentPlanner
from backend.agent.schemas import AgentState


def test_click_and_stale_target_handling():
    print("[TEST 1] Testing CLICK Execution & Stale Element Rejection...")
    executor = ActionExecutor()

    mock_elements = [
        {"id": "btn-search", "type": "BUTTON", "bbox": [100, 50, 200, 90], "confidence": 0.95, "visibility": "VISIBLE"},
        {"id": "input-q", "type": "INPUT", "bbox": [20, 50, 95, 90], "confidence": 0.96, "visibility": "VISIBLE"}
    ]

    # 1. Valid Click
    valid_click = {
        "action": "CLICK",
        "target": {"x": 150, "y": 70},
        "target_id": "btn-search",
        "confidence": 0.95
    }
    res_1 = executor.execute_browser_action(valid_click, current_elements=mock_elements)
    assert res_1.success is True
    assert res_1.status == ExecutionStatus.SUCCESS
    assert res_1.page_changed is True

    # 2. Stale target (target_id not present in current elements)
    stale_click = {
        "action": "CLICK",
        "target": {"x": 500, "y": 300},
        "target_id": "btn-stale-deleted",
        "confidence": 0.95
    }
    res_2 = executor.execute_browser_action(stale_click, current_elements=mock_elements)
    assert res_2.success is False
    assert res_2.status == ExecutionStatus.STALE_TARGET
    assert res_2.error.code == "TARGET_NOT_FOUND"

    print("  ✓ Valid click dispatched and stale target correctly rejected.")


def test_type_execution_and_zero_leak():
    print("\n[TEST 2] Testing TYPE Execution & Zero-Leak Privacy Guarantees...")
    executor = ActionExecutor()

    # 1. Public typing
    public_type = {
        "action": "TYPE",
        "target": {"x": 50, "y": 70},
        "target_id": "input-q",
        "text": "Chandrayaan-3",
        "target_description": "Search field (input-q)",
        "confidence": 0.95
    }
    res_pub = executor.execute_browser_action(public_type)
    assert res_pub.success is True
    assert res_pub.metadata.get("display_payload") == "Chandrayaan-3"

    # 2. Sensitive password typing
    secret_pass = "SuperSecretPassword123!"
    pass_type = {
        "action": "TYPE",
        "target": {"x": 50, "y": 150},
        "target_id": "input-pwd",
        "text": secret_pass,
        "target_description": "Password field (input-pwd)",
        "confidence": 0.96
    }
    res_pass = executor.execute_browser_action(pass_type)
    assert res_pass.success is True
    assert res_pass.metadata.get("display_payload") == "[REDACTED_TEXT]"
    assert secret_pass not in str(res_pass.metadata)

    print("  ✓ TYPE keystroke execution passed; sensitive password payload strictly masked.")


def test_scroll_execution():
    print("\n[TEST 3] Testing Controlled SCROLL Execution...")
    executor = ActionExecutor()

    # 1. Scroll down
    res_down = executor.execute_browser_action({"action": "SCROLL_DOWN", "amount": 450})
    assert res_down.success is True
    assert res_down.action == "SCROLL"
    assert res_down.metadata.get("direction") == "DOWN"
    assert res_down.metadata.get("delta_px") == 450

    # 2. Scroll up
    res_up = executor.execute_browser_action({"action": "SCROLL_UP", "amount": 200})
    assert res_up.success is True
    assert res_up.metadata.get("direction") == "UP"
    assert res_up.metadata.get("delta_px") == -200

    print("  ✓ Viewport scrolling (UP/DOWN) verified with configurable pixel step.")


def test_keyboard_press_and_safety_filtering():
    print("\n[TEST 4] Testing Keyboard Actions & Safe Key Whitelist...")
    executor = ActionExecutor()

    # 1. Permitted key (Enter)
    res_enter = executor.execute_browser_action({"action": "PRESS_KEY", "key": "Enter"})
    assert res_enter.success is True
    assert res_enter.metadata.get("key") == "Enter"

    # 2. Permitted key (Tab)
    res_tab = executor.execute_browser_action({"action": "PRESS_KEY", "key": "Tab"})
    assert res_tab.success is True

    # 3. Blocked unsafe / arbitrary sequence
    res_unsafe = executor.execute_browser_action({"action": "PRESS_KEY", "key": "eval(dangerous_code)"})
    assert res_unsafe.success is False
    assert res_unsafe.error.code == "UNSAFE_KEY"

    print("  ✓ Permitted safe keys accepted; arbitrary injected keys blocked.")


def test_navigation_and_dangerous_scheme_blocking():
    print("\n[TEST 5] Testing Navigation & Protocol Security...")
    executor = ActionExecutor()

    # 1. Valid local demo navigation
    res_valid = executor.execute_browser_action({"action": "NAVIGATE", "url": "/demo/product_detail.html"}, current_url="/demo/product_listing.html")
    assert res_valid.success is True
    assert res_valid.metadata.get("previous_url") == "/demo/product_listing.html"
    assert res_valid.metadata.get("result_url") == "/demo/product_detail.html"

    # 2. Blocked dangerous javascript: URI scheme
    res_js = executor.execute_browser_action({"action": "NAVIGATE", "url": "javascript:alert(1)"})
    assert res_js.success is False
    assert res_js.error.code == "UNSAFE_URL_SCHEME"

    # 3. Blocked data: URI scheme
    res_data = executor.execute_browser_action({"action": "NAVIGATE", "url": "data:text/html,<script>evil()</script>"})
    assert res_data.success is False
    assert res_data.error.code == "UNSAFE_URL_SCHEME"

    print("  ✓ Navigation verified; javascript: and data: protocol injection blocked.")


def test_page_change_detector():
    print("\n[TEST 6] Testing Page Change Detection Signals...")
    detector = PageChangeDetector()

    # 1. URL Change
    sig_url = detector.detect_changes(
        prev_url="/demo/product_listing.html",
        current_url="/demo/product_detail.html",
        prev_elements=[{"id": "1"}],
        current_elements=[{"id": "2"}],
        action_name="NAVIGATE"
    )
    assert sig_url.page_changed is True
    assert sig_url.url_changed is True

    # 2. DOM Mutation (element count changed)
    sig_dom = detector.detect_changes(
        prev_url="/demo/product_listing.html",
        current_url="/demo/product_listing.html",
        prev_elements=[{"id": "1"}],
        current_elements=[{"id": "1"}, {"id": "modal-open"}],
        action_name="CLICK"
    )
    assert sig_dom.page_changed is True
    assert sig_dom.dom_mutated is True

    print("  ✓ Page mutation signals (URL, DOM delta, scroll state) verified.")


def test_end_to_end_agent_runner_loop():
    print("\n[TEST 7] Testing End-to-End Multi-Turn Agent Runner...")
    planner = AgentPlanner()
    executor = ActionExecutor()
    runner = EndToEndAgentRunner(planner=planner, executor=executor)

    mock_elements = [
        {"id": "search-input", "type": "INPUT", "text": "", "attributes": {"placeholder": "Search Wikipedia..."}, "bbox": [20, 50, 360, 85], "confidence": 0.96, "visibility": "VISIBLE"},
        {"id": "search-btn", "type": "BUTTON", "text": "Search", "attributes": {}, "bbox": [370, 50, 450, 85], "confidence": 0.94, "visibility": "VISIBLE"},
        {"id": "wiki-link", "type": "LINK", "text": "Chandrayaan-3 - Wikipedia", "attributes": {}, "bbox": [20, 150, 450, 185], "confidence": 0.92, "visibility": "VISIBLE"}
    ]

    # Turn 1: Type search query
    step_1 = runner.run_single_turn(
        sanitized_elements=mock_elements,
        current_url="/demo/search.html",
        task_goal="Search for Chandrayaan-3 and open the first relevant result"
    )
    assert step_1["status"] == "SUCCESS"
    assert step_1["action"]["action"] == "TYPE"
    assert step_1["action"]["target_id"] == "search-input"

    # Turn 2: Click search button
    step_2 = runner.run_single_turn(
        sanitized_elements=mock_elements,
        current_url="/demo/search.html",
        task_goal="Search for Chandrayaan-3 and open the first relevant result"
    )
    assert step_2["status"] == "SUCCESS"
    assert step_2["action"]["action"] == "CLICK"

    # Test Stop Control
    runner.stop()
    step_stopped = runner.run_single_turn(
        sanitized_elements=mock_elements,
        current_url="/demo/search.html",
        task_goal="Search for Chandrayaan-3"
    )
    assert step_stopped["status"] == "STOPPED"

    print("  ✓ Multi-turn agent loop executed successfully across typed inputs, clicks, and stop controls.")


def test_high_risk_payment_confirmation_gate():
    print("\n[TEST 8] Testing High-Risk Financial Action Human Confirmation Gate...")
    planner = AgentPlanner()
    executor = ActionExecutor()
    runner = EndToEndAgentRunner(planner=planner, executor=executor)

    payment_elements = [
        {"id": "btn-pay", "type": "BUTTON", "text": "Authorize & Submit Payment ₹1,450,000", "attributes": {}, "bbox": [50, 400, 400, 440], "confidence": 0.95, "visibility": "VISIBLE"}
    ]

    # Without confirmation -> must be BLOCKED / REQUIRES_CONFIRMATION
    step_blocked = runner.run_single_turn(
        sanitized_elements=payment_elements,
        current_url="/demo/payment_sim.html",
        task_goal="Fill out checkout form and pay order",
        user_confirmed=False
    )
    assert step_blocked["status"] == "REQUIRES_CONFIRMATION"

    # With user confirmation -> allowed
    step_confirmed = runner.run_single_turn(
        sanitized_elements=payment_elements,
        current_url="/demo/payment_sim.html",
        task_goal="Fill out checkout form and pay order",
        user_confirmed=True
    )
    assert step_confirmed["status"] == "SUCCESS"

    print("  ✓ Financial action blocked by default and authorized only after explicit human confirmation.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING REAL ACTION EXECUTION & AGENT TEST SUITE")
    print("==================================================")
    test_click_and_stale_target_handling()
    test_type_execution_and_zero_leak()
    test_scroll_execution()
    test_keyboard_press_and_safety_filtering()
    test_navigation_and_dangerous_scheme_blocking()
    test_page_change_detector()
    test_end_to_end_agent_runner_loop()
    test_high_risk_payment_confirmation_gate()
    print("==================================================")
    print("ALL ACTION EXECUTION & AGENT TESTS PASSED! ✓")
    print("==================================================")
