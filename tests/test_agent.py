"""
Comprehensive Unit & Integration Test Suite for Lightweight Browser Agent Planning Engine
Tests:
  - Agent State Machine transitions & invalid transition guards
  - Goal Decomposition across distinct task types
  - Candidate Action Generation & transparent Multi-factor Scoring
  - Action Validation (bounds, confidence, budget, loops, financial confirmation)
  - Outcome Verification (URL change, DOM mutation, value update)
  - Privacy-safe Working Memory & Explainable Planning Traces
  - End-to-End Multi-Step Task Execution Scenarios
"""

import sys
import os
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agent.schemas import (
    AgentState, ActionType, ObjectiveStatus, RiskLevel,
    TaskConstraints, AgentTask
)
from backend.agent.state_machine import AgentStateMachine, InvalidStateTransitionError
from backend.agent.decomposer import GoalDecomposer
from backend.agent.candidate_generator import CandidateGenerator
from backend.agent.scoring import ActionScorer
from backend.agent.validator import ActionValidator
from backend.agent.verifier import ActionVerifier
from backend.agent.memory import AgentMemory
from backend.agent.planner import AgentPlanner


def test_agent_state_machine():
    print("[TEST 1] Testing Agent State Machine & Transition Rules...")
    sm = AgentStateMachine()
    assert sm.current_state == AgentState.IDLE

    # Valid transition path: IDLE -> OBSERVING -> PERCEIVING -> UNDERSTANDING -> PLANNING -> VALIDATING -> ACTING -> VERIFYING -> COMPLETED
    sm.transition_to(AgentState.OBSERVING)
    assert sm.current_state == AgentState.OBSERVING
    sm.transition_to(AgentState.PERCEIVING)
    sm.transition_to(AgentState.UNDERSTANDING)
    sm.transition_to(AgentState.PLANNING)
    sm.transition_to(AgentState.VALIDATING)
    sm.transition_to(AgentState.ACTING)
    sm.transition_to(AgentState.VERIFYING)
    sm.transition_to(AgentState.COMPLETED)
    assert sm.current_state == AgentState.COMPLETED

    # Reset
    sm.reset()
    assert sm.current_state == AgentState.IDLE

    # Invalid transition check (IDLE directly to ACTING is forbidden)
    try:
        sm.transition_to(AgentState.ACTING)
        assert False, "Should have raised InvalidStateTransitionError"
    except InvalidStateTransitionError as e:
        assert "INVALID_STATE_TRANSITION" in str(e)

    # Pause and resume
    sm.transition_to(AgentState.PLANNING)
    sm.transition_to(AgentState.PAUSED)
    assert sm.current_state == AgentState.PAUSED
    sm.transition_to(AgentState.PLANNING)
    assert sm.current_state == AgentState.PLANNING

    print(f"  ✓ State machine verified with {len(sm.get_history())} tracked transitions.")


def test_goal_decomposition():
    print("\n[TEST 2] Testing Goal Decomposition Across Task Types...")
    decomposer = GoalDecomposer()

    # 1. Search Task
    search_task = "Search for Chandrayaan-3 and open the first relevant result."
    search_objs = decomposer.decompose(search_task)
    assert len(search_objs) == 4
    assert search_objs[0].semantic_intent == "search_input"
    assert search_objs[1].semantic_intent == "submit_search"
    assert search_objs[2].semantic_intent == "select_result"
    assert search_objs[3].semantic_intent == "verify_navigation"

    # 2. Login Task
    login_task = "Login to the portal with user@sih2026.gov.in and password."
    login_objs = decomposer.decompose(login_task)
    assert len(login_objs) == 4
    assert login_objs[0].semantic_intent == "input_username"
    assert login_objs[1].semantic_intent == "input_password"
    assert login_objs[2].semantic_intent == "submit_login"

    # 3. Checkout Task
    checkout_task = "Fill out checkout billing form and pay order"
    checkout_objs = decomposer.decompose(checkout_task)
    assert len(checkout_objs) == 4
    assert checkout_objs[0].semantic_intent == "input_contact"
    assert checkout_objs[2].semantic_intent == "input_card"
    assert checkout_objs[3].semantic_intent == "submit_payment"

    # 4. Scroll Task
    scroll_task = "Scroll down and find the specifications section"
    scroll_objs = decomposer.decompose(scroll_task)
    assert len(scroll_objs) == 2
    assert scroll_objs[0].semantic_intent == "scroll_page"

    print(f"  ✓ Goal decomposition verified across Search (4 objs), Login (4 objs), Checkout (4 objs), Scroll (2 objs).")


def test_candidate_generation_and_scoring():
    print("\n[TEST 3] Testing Candidate Action Generation & Multi-factor Scoring...")
    decomposer = GoalDecomposer()
    generator = CandidateGenerator()
    scorer = ActionScorer()

    search_objs = decomposer.decompose("Search for Chandrayaan-3")
    obj_1 = search_objs[0]  # search_input

    mock_elements = [
        {"id": "pb-001", "type": "INPUT", "text": "", "attributes": {"placeholder": "Search Wikipedia...", "name": "search"}, "bbox": [20, 50, 360, 85], "confidence": 0.96, "visibility": "VISIBLE"},
        {"id": "pb-002", "type": "BUTTON", "text": "Search", "attributes": {}, "bbox": [370, 50, 450, 85], "confidence": 0.94, "visibility": "VISIBLE"},
        {"id": "pb-003", "type": "INPUT", "text": "", "attributes": {"placeholder": "Newsletter Email"}, "bbox": [20, 500, 300, 535], "confidence": 0.80, "visibility": "VISIBLE"},
    ]

    candidates = generator.generate_candidates(obj_1, mock_elements, goal_text="Search for Chandrayaan-3")
    assert len(candidates) >= 2

    scored = scorer.score_candidates(candidates, obj_1, mock_elements)
    assert len(scored) == len(candidates)
    top_action = scored[0]

    # Top action must be the search input (pb-001)
    assert top_action.target_id == "pb-001"
    assert top_action.action == ActionType.TYPE
    assert top_action.score > scored[1].score
    assert "semantic_match" in top_action.score_breakdown
    assert top_action.score >= 0.85

    print(f"  ✓ Ranked {len(scored)} candidate actions. Top score: {top_action.score:.3f} on target '{top_action.target_id}'.")


def test_action_validation_and_safety():
    print("\n[TEST 4] Testing Action Validation & Safety Constraints...")
    validator = ActionValidator(min_confidence=0.50)

    # 1. Valid Action
    valid_act = {
        "action": "CLICK",
        "target": {"x": 100, "y": 200},
        "confidence": 0.95
    }
    v_res = validator.validate_candidate(valid_act)
    assert v_res.allowed is True
    assert v_res.reason == "VALIDATION_PASSED"

    # 2. Out of bounds coordinates
    oob_act = {
        "action": "CLICK",
        "target": {"x": 2500, "y": 500},
        "confidence": 0.95
    }
    v_oob = validator.validate_candidate(oob_act, screen_width=1920, screen_height=1080)
    assert v_oob.allowed is False
    assert "COORDINATES_OUT_OF_BOUNDS" in v_oob.reason

    # 3. Low confidence
    low_conf_act = {
        "action": "CLICK",
        "target": {"x": 100, "y": 200},
        "confidence": 0.35
    }
    v_low = validator.validate_candidate(low_conf_act)
    assert v_low.allowed is False
    assert "LOW_TARGET_CONFIDENCE" in v_low.reason

    # 4. Action budget exceeded
    constraints = TaskConstraints(max_actions=5)
    v_budget = validator.validate_candidate(valid_act, constraints=constraints, actions_executed_so_far=5)
    assert v_budget.allowed is False
    assert "ACTION_BUDGET_EXCEEDED" in v_budget.reason

    # 5. Loop detection (3 repeated attempts)
    mock_history = [
        {"action": "CLICK", "targetId": "pb-001"},
        {"action": "CLICK", "targetId": "pb-001"},
        {"action": "CLICK", "targetId": "pb-001"}
    ]
    repeated_act = {
        "action": "CLICK",
        "target_id": "pb-001",
        "target": {"x": 100, "y": 200},
        "confidence": 0.95
    }
    v_loop = validator.validate_candidate(repeated_act, history=mock_history)
    assert v_loop.allowed is False
    assert "POSSIBLE_AGENT_LOOP" in v_loop.reason

    # 6. Financial confirmation required
    payment_act = {
        "action": "CLICK",
        "target": {"x": 100, "y": 200},
        "confidence": 0.95,
        "risk_level": RiskLevel.CRITICAL,
        "requires_confirmation": True
    }
    v_pay = validator.validate_candidate(payment_act)
    assert v_pay.allowed is False
    assert v_pay.requires_confirmation is True
    assert "REQUIRES_HUMAN_CONFIRMATION" in v_pay.reason

    print("  ✓ Action validation verified (Bounds, Confidence, Budget, Loop Detection, Financial Confirmation).")


def test_outcome_verification():
    print("\n[TEST 5] Testing Action Outcome Verification...")
    verifier = ActionVerifier()

    # 1. URL change verification
    v_url = verifier.verify_action_outcome(
        action={"action": "CLICK"},
        prev_elements=[{"id": "1"}],
        current_elements=[{"id": "2"}],
        prev_url="http://localhost:8000/demo/search.html",
        current_url="http://localhost:8000/demo/results.html"
    )
    assert v_url.success is True
    assert v_url.signal == "PAGE_NAVIGATED"
    assert v_url.re_perception_required is True

    # 2. DOM mutation verification
    v_dom = verifier.verify_action_outcome(
        action={"action": "CLICK", "target_id": "btn-1"},
        prev_elements=[{"id": "btn-1"}],
        current_elements=[{"id": "btn-1"}, {"id": "modal-1"}],
        prev_url="http://localhost:8000/demo/page.html",
        current_url="http://localhost:8000/demo/page.html"
    )
    assert v_dom.success is True
    assert v_dom.signal == "DOM_MUTATION_DETECTED"

    # 3. Input value update verification
    v_type = verifier.verify_action_outcome(
        action={"action": "TYPE", "target_id": "input-1", "text": "Chandrayaan-3"},
        prev_elements=[{"id": "input-1", "value": ""}],
        current_elements=[{"id": "input-1", "value": "Chandrayaan-3"}],
        prev_url="http://localhost:8000/demo/search.html",
        current_url="http://localhost:8000/demo/search.html"
    )
    assert v_type.success is True
    assert v_type.signal == "INPUT_VALUE_UPDATED"

    print("  ✓ Outcome verification verified across URL navigation, DOM mutations, and input updates.")


def test_end_to_end_planner_orchestration():
    print("\n[TEST 6] Testing Master Agent Planner End-to-End Orchestration...")
    planner = AgentPlanner()

    # Create task
    task = planner.create_task("Search for Chandrayaan-3 and open the wiki result")
    assert task.goal == "Search for Chandrayaan-3 and open the wiki result"
    assert len(task.objectives) >= 3

    mock_elements = [
        {"id": "pb-search-in", "type": "INPUT", "text": "", "attributes": {"placeholder": "Search query...", "name": "q"}, "bbox": [20, 50, 360, 85], "confidence": 0.97, "visibility": "VISIBLE"},
        {"id": "pb-search-btn", "type": "BUTTON", "text": "Search", "attributes": {}, "bbox": [370, 50, 450, 85], "confidence": 0.95, "visibility": "VISIBLE"},
        {"id": "pb-result-link", "type": "LINK", "text": "Chandrayaan-3 - ISRO Wiki", "attributes": {}, "bbox": [20, 150, 450, 185], "confidence": 0.93, "visibility": "VISIBLE"},
    ]

    # Step 1: Plan search input typing
    candidate_1, validation_1, state_1 = planner.plan_next_step(sanitized_elements=mock_elements)
    assert candidate_1 is not None
    assert candidate_1.action == ActionType.TYPE
    assert candidate_1.target_id == "pb-search-in"
    assert validation_1.allowed is True

    # Legacy plan_action compatibility test
    legacy_action = planner.plan_action("Search for Chandrayaan-3", mock_elements, [])
    assert legacy_action["action"] in ("TYPE", "CLICK")
    assert "confidence" in legacy_action

    # Check status telemetry
    status = planner.get_agent_status()
    assert status["task"] is not None
    assert status["trace_count"] >= 1

    # Pause and resume
    assert planner.pause() == AgentState.PAUSED
    assert planner.resume() == AgentState.PLANNING
    assert planner.stop() == AgentState.IDLE

    print("  ✓ Full planning lifecycle (Task Creation -> Planning -> Scoring -> Verification -> State Control) passed.")


def test_privacy_safe_memory_invariants():
    print("\n[TEST 7] Testing Privacy-Safe Agent Working Memory Invariants...")
    memory = AgentMemory()

    # Attempt to record action with sensitive password
    secret_pass = "SuperSecretAdminPassword123!"
    memory.record_action({
        "action": "TYPE",
        "target_description": "Password field (pb-002)",
        "text": secret_pass
    })

    # Assert secret password NEVER appears in recorded memory
    mem_str = str(memory.recent_actions)
    assert secret_pass not in mem_str, "CRITICAL: Raw password stored in agent working memory!"
    assert "[REDACTED_PASSWORD]" in mem_str

    print("  ✓ Privacy invariant passed: working memory guarantees zero password retention.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING LIGHTWEIGHT BROWSER AGENT TEST SUITE")
    print("==================================================")
    test_agent_state_machine()
    test_goal_decomposition()
    test_candidate_generation_and_scoring()
    test_action_validation_and_safety()
    test_outcome_verification()
    test_end_to_end_planner_orchestration()
    test_privacy_safe_memory_invariants()
    print("==================================================")
    print("ALL AGENT PLANNING ENGINE TESTS PASSED! ✓")
    print("==================================================")
