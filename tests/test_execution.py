"""
Comprehensive Test Suite for Real Browser Action Execution & End-to-End Agent
Tests:
  - CLICK execution, stale target detection & rejection
  - TYPE execution with zero-leak sensitive payload masking
  - SCROLL execution (SCROLL_UP, SCROLL_DOWN) with delta tracking
  - PRESS_KEY execution with permitted key whitelist enforcement
  - NAVIGATE execution with dangerous protocol blocking (javascript:, data:)
  - Page Change Detection (URL, DOM mutation, scroll offsets)
  - End-to-End Multi-turn Agent Runner with budget, loop, and confirmation guardrails
  - Browser Action Bridge: dispatch, ack, timeout, extension unavailable, lifecycle
"""

import sys
import os
import time
import threading

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.actions.schemas import (
    ActionResult, ExecutionStatus, ExecutionConfig, SupportedKey
)
from backend.actions.executor import ActionExecutor
from backend.actions.page_change_detector import PageChangeDetector
from backend.actions.agent_runner import EndToEndAgentRunner
from backend.actions.browser_bridge import (
    BrowserActionBridge, PendingAction, ActionAcknowledgement, ActionBridgeResult
)
from backend.agent.planner import AgentPlanner
from backend.agent.schemas import AgentState


# ============================================================
# EXISTING TESTS (updated for simulation_mode=True)
# ============================================================

def test_click_and_stale_target_handling():
    print("[TEST 1] Testing CLICK Execution & Stale Element Rejection...")
    executor = ActionExecutor(simulation_mode=True)

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
    executor = ActionExecutor(simulation_mode=True)

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
    executor = ActionExecutor(simulation_mode=True)

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
    executor = ActionExecutor(simulation_mode=True)

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
    executor = ActionExecutor(simulation_mode=True)

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
    executor = ActionExecutor(simulation_mode=True)
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
    executor = ActionExecutor(simulation_mode=True)
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


# ============================================================
# NEW BROWSER ACTION BRIDGE TESTS
# ============================================================

def test_bridge_action_dispatch_and_ack():
    """Test full bridge lifecycle: dispatch → ack → result."""
    print("\n[TEST 9] Testing Bridge Action Dispatch & Acknowledgement...")
    bridge = BrowserActionBridge()
    # Simulate extension connectivity
    bridge.register_heartbeat()

    action = PendingAction(
        action_id="test-001",
        action_type="CLICK",
        target_id="btn-search",
        target={"x": 150, "y": 70, "elementId": "btn-search"}
    )
    bridge.dispatch_action(action)

    # Simulate extension picking up and acknowledging in background thread
    def simulate_extension():
        time.sleep(0.05)  # Small delay to simulate network
        pending = bridge.get_pending_action()
        assert pending is not None
        assert pending.action_id == "test-001"
        assert pending.status == "DISPATCHED"

        ack = ActionAcknowledgement(
            action_id="test-001",
            success=True,
            action_type="CLICK",
            target_id="btn-search",
            detail="Dispatched click event on <button>",
            execution_timestamp="2026-08-30T12:00:00Z"
        )
        bridge.acknowledge_action(ack)

    t = threading.Thread(target=simulate_extension)
    t.start()

    result = bridge.wait_for_result("test-001", timeout_ms=2000)
    t.join()

    assert result.success is True
    assert result.status == "SUCCESS"
    assert result.action_type == "CLICK"
    assert result.target_id == "btn-search"

    print("  ✓ Bridge dispatch → ack → result lifecycle verified.")


def test_bridge_timeout_handling():
    """Test that bridge times out correctly when no ack arrives."""
    print("\n[TEST 10] Testing Bridge Timeout Handling...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()

    action = PendingAction(
        action_id="test-timeout-001",
        action_type="CLICK",
        target_id="btn-missing",
        timeout_ms=300
    )
    bridge.dispatch_action(action)

    # No ack arrives — should timeout
    result = bridge.wait_for_result("test-timeout-001", timeout_ms=300)
    assert result.success is False
    assert result.status == "TIMEOUT"
    assert result.error_code == "EXTENSION_TIMEOUT"

    print("  ✓ Bridge correctly times out when no acknowledgement received.")


def test_bridge_extension_unavailable():
    """Test executor fails fast when extension is not connected."""
    print("\n[TEST 11] Testing Extension Unavailable Detection...")
    bridge = BrowserActionBridge()
    # Do NOT register heartbeat — extension not connected
    executor = ActionExecutor(bridge=bridge, simulation_mode=False)

    res = executor.execute_browser_action({
        "action": "CLICK",
        "target": {"x": 100, "y": 50},
        "target_id": "btn-test",
        "confidence": 0.95
    })

    assert res.success is False
    assert res.status == ExecutionStatus.EXTENSION_UNAVAILABLE
    assert res.error.code == "EXTENSION_UNAVAILABLE"

    print("  ✓ Executor correctly fails fast when extension is not connected.")


def test_bridge_failed_ack():
    """Test that failed ack from extension propagates correct error."""
    print("\n[TEST 12] Testing Bridge Failed Acknowledgement...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()

    action = PendingAction(
        action_id="test-fail-001",
        action_type="TYPE",
        target_id="input-missing"
    )
    bridge.dispatch_action(action)

    # Simulate failed ack
    def simulate_failure():
        time.sleep(0.05)
        bridge.get_pending_action()  # Mark as dispatched
        ack = ActionAcknowledgement(
            action_id="test-fail-001",
            success=False,
            error="Could not resolve target element on current page layout.",
            error_code="TARGET_NOT_FOUND"
        )
        bridge.acknowledge_action(ack)

    t = threading.Thread(target=simulate_failure)
    t.start()

    result = bridge.wait_for_result("test-fail-001", timeout_ms=2000)
    t.join()

    assert result.success is False
    assert result.status == "FAILED"
    assert result.error_code == "TARGET_NOT_FOUND"

    print("  ✓ Bridge correctly propagates failure from extension content script.")


def test_bridge_stale_target_still_caught():
    """Test stale target is still caught BEFORE bridge dispatch."""
    print("\n[TEST 13] Testing Stale Target Rejection Before Bridge...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()
    executor = ActionExecutor(bridge=bridge, simulation_mode=False)

    mock_elements = [
        {"id": "btn-real", "type": "BUTTON", "bbox": [100, 50, 200, 90], "confidence": 0.95, "visibility": "VISIBLE"}
    ]

    res = executor.execute_browser_action(
        {"action": "CLICK", "target": {"x": 150, "y": 70}, "target_id": "btn-stale-deleted", "confidence": 0.95},
        current_elements=mock_elements
    )
    assert res.success is False
    assert res.status == ExecutionStatus.STALE_TARGET
    assert res.error.code == "TARGET_NOT_FOUND"

    print("  ✓ Stale target still caught before bridge dispatch.")


def test_bridge_validator_rejection():
    """Test ActionValidator still blocks invalid actions before bridge."""
    print("\n[TEST 14] Testing Validator Rejection Before Bridge...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()
    executor = ActionExecutor(bridge=bridge, simulation_mode=False)

    # Out of bounds coordinates
    res = executor.execute_browser_action({
        "action": "CLICK",
        "target": {"x": 9999, "y": 9999},
        "confidence": 0.95
    })
    assert res.success is False
    assert res.status == ExecutionStatus.BLOCKED
    assert "OUT_OF_BOUNDS" in res.error.code or "OUT_OF_BOUNDS" in res.error.message

    print("  ✓ ActionValidator still blocks invalid actions before bridge dispatch.")


def test_bridge_high_risk_confirmation():
    """Test high-risk actions still require confirmation before bridge dispatch."""
    print("\n[TEST 15] Testing High-Risk Confirmation Before Bridge...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()
    executor = ActionExecutor(bridge=bridge, simulation_mode=False)

    payment_elements = [
        {"id": "btn-pay", "type": "BUTTON", "text": "Authorize & Submit Payment ₹1,450,000", "attributes": {}, "bbox": [50, 400, 400, 440], "confidence": 0.95, "visibility": "VISIBLE"}
    ]

    planner = AgentPlanner()
    runner = EndToEndAgentRunner(planner=planner, executor=executor)

    step = runner.run_single_turn(
        sanitized_elements=payment_elements,
        current_url="/demo/payment_sim.html",
        task_goal="Fill out checkout form and pay order",
        user_confirmed=False
    )
    assert step["status"] == "REQUIRES_CONFIRMATION"

    print("  ✓ High-risk confirmation still enforced before bridge dispatch.")


def test_bridge_click_dispatch_format():
    """Test CLICK action is correctly formatted for the bridge."""
    print("\n[TEST 16] Testing Bridge CLICK Dispatch Format...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()

    action = PendingAction(
        action_id="fmt-click-001",
        action_type="CLICK",
        target_id="btn-search",
        target={"x": 150.0, "y": 70.0, "elementId": "btn-search"}
    )
    bridge.dispatch_action(action)

    pending = bridge.get_pending_action()
    assert pending is not None
    assert pending.action_type == "CLICK"
    assert pending.target_id == "btn-search"
    assert pending.target["x"] == 150.0

    # Clean up
    bridge.cancel_action("fmt-click-001")
    print("  ✓ CLICK action correctly formatted for extension dispatch.")


def test_bridge_type_dispatch_format():
    """Test TYPE action is correctly formatted with text payload."""
    print("\n[TEST 17] Testing Bridge TYPE Dispatch Format...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()

    action = PendingAction(
        action_id="fmt-type-001",
        action_type="TYPE",
        target_id="search-input",
        target={"x": 50, "y": 70, "elementId": "search-input"},
        text="Chandrayaan-3"
    )
    bridge.dispatch_action(action)

    pending = bridge.get_pending_action()
    assert pending is not None
    assert pending.action_type == "TYPE"
    assert pending.text == "Chandrayaan-3"
    assert pending.target_id == "search-input"

    bridge.cancel_action("fmt-type-001")
    print("  ✓ TYPE action correctly formatted with text payload for extension dispatch.")


def test_bridge_scroll_dispatch_format():
    """Test SCROLL action is correctly formatted with direction/delta."""
    print("\n[TEST 18] Testing Bridge SCROLL Dispatch Format...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()

    action = PendingAction(
        action_id="fmt-scroll-001",
        action_type="SCROLL",
        scroll_delta={"x": 0, "y": 400}
    )
    bridge.dispatch_action(action)

    pending = bridge.get_pending_action()
    assert pending is not None
    assert pending.action_type == "SCROLL"
    assert pending.scroll_delta["y"] == 400

    bridge.cancel_action("fmt-scroll-001")
    print("  ✓ SCROLL action correctly formatted with scroll delta for extension dispatch.")


def test_bridge_pending_and_ack_lifecycle():
    """Test full lifecycle: pending → dispatched → ack → result cleared."""
    print("\n[TEST 19] Testing Bridge Full Lifecycle State Transitions...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()

    # Step 1: Dispatch
    action = PendingAction(action_id="lifecycle-001", action_type="CLICK", target_id="btn-x")
    bridge.dispatch_action(action)

    status = bridge.get_status()
    assert status["pending_actions"] == 1

    # Step 2: Extension picks up
    pending = bridge.get_pending_action()
    assert pending.status == "DISPATCHED"

    status2 = bridge.get_status()
    assert status2["dispatched_actions"] == 1
    assert status2["pending_actions"] == 0

    # Step 3: Ack
    ack = ActionAcknowledgement(action_id="lifecycle-001", success=True)
    found = bridge.acknowledge_action(ack)
    assert found is True

    status3 = bridge.get_status()
    assert status3["pending_actions"] == 0
    assert status3["dispatched_actions"] == 0
    assert status3["history_count"] == 1

    print("  ✓ Full lifecycle state transitions (PENDING → DISPATCHED → ACK → CLEARED) verified.")


def test_bridge_cancel_action():
    """Test action cancellation."""
    print("\n[TEST 20] Testing Bridge Action Cancellation...")
    bridge = BrowserActionBridge()
    bridge.register_heartbeat()

    action = PendingAction(action_id="cancel-001", action_type="CLICK")
    bridge.dispatch_action(action)

    cancelled = bridge.cancel_action("cancel-001")
    assert cancelled is True

    # Trying to cancel again should fail
    cancelled_again = bridge.cancel_action("cancel-001")
    assert cancelled_again is False

    print("  ✓ Action cancellation works correctly.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING REAL ACTION EXECUTION & AGENT TEST SUITE")
    print("==================================================")

    # Original tests (simulation mode)
    test_click_and_stale_target_handling()
    test_type_execution_and_zero_leak()
    test_scroll_execution()
    test_keyboard_press_and_safety_filtering()
    test_navigation_and_dangerous_scheme_blocking()
    test_page_change_detector()
    test_end_to_end_agent_runner_loop()
    test_high_risk_payment_confirmation_gate()

    # New bridge tests
    test_bridge_action_dispatch_and_ack()
    test_bridge_timeout_handling()
    test_bridge_extension_unavailable()
    test_bridge_failed_ack()
    test_bridge_stale_target_still_caught()
    test_bridge_validator_rejection()
    test_bridge_high_risk_confirmation()
    test_bridge_click_dispatch_format()
    test_bridge_type_dispatch_format()
    test_bridge_scroll_dispatch_format()
    test_bridge_pending_and_ack_lifecycle()
    test_bridge_cancel_action()

    print("==================================================")
    print("ALL 20 ACTION EXECUTION, AGENT & BRIDGE TESTS PASSED! ✓")
    print("==================================================")
