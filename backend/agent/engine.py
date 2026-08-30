"""
PrivyBrowse AI — Reasoning Engine & Decision Planner
Provides an abstract BaseReasoningEngine interface and a high-precision LocalRuleBasedEngine.
Strictly accepts ONLY sanitized layout context, enforcing that webpage content is UNTRUSTED DATA.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.agent.schemas import CandidateAction, Objective, AgentTask, RiskLevel
from backend.agent.candidate_generator import CandidateGenerator
from backend.agent.scoring import ActionScorer
from backend.security.injection_guard import InjectionGuard
from backend.security.schemas import ThreatLevel


class BaseReasoningEngine(ABC):
    """Abstract interface for browser agent decision makers."""

    @abstractmethod
    def plan_next_action(
        self,
        task: AgentTask,
        objective: Objective,
        sanitized_elements: List[Dict[str, Any]],
        history: List[Dict[str, Any]] = None
    ) -> Optional[CandidateAction]:
        """Plans and returns the top-ranked candidate action."""
        pass


class LocalRuleBasedEngine(BaseReasoningEngine):
    """
    On-device deterministic reasoning engine.
    Consumes sanitized layout elements and produces ranked, explainable actions.
    Maintains a strict boundary: Webpage content is UNTRUSTED DATA, User task is TRUSTED GOAL.
    """

    def __init__(self):
        self.generator = CandidateGenerator()
        self.scorer = ActionScorer()
        self.injection_guard = InjectionGuard()

    def plan_next_action(
        self,
        task: AgentTask,
        objective: Objective,
        sanitized_elements: List[Dict[str, Any]],
        history: List[Dict[str, Any]] = None
    ) -> Optional[CandidateAction]:
        """
        1. Neutralizes adversarial prompt injections from untrusted webpage text
        2. Enforces explicit UNTRUSTED data provenance tags
        3. Generates candidate actions strictly matching the user task
        4. Scores and ranks candidate actions
        5. Returns the highest-scoring candidate
        """
        clean_elements, security_findings = self.injection_guard.sanitize_untrusted_elements(sanitized_elements)

        candidates = self.generator.generate_candidates(
            objective=objective,
            fused_elements=clean_elements,
            goal_text=task.goal,
            history=history
        )

        if not candidates:
            return None

        # Filter out candidates that target purely adversarial directives unless explicitly authorized
        valid_candidates = []
        for cand in candidates:
            target_el = next((e for e in clean_elements if e.get("id") == cand.target_id), None)
            if target_el and target_el.get("adversarial_injection_detected"):
                # Penalize or elevate risk for actions on adversarial elements
                cand.risk_level = RiskLevel.HIGH
                cand.confidence = max(0.1, cand.confidence * 0.5)
            valid_candidates.append(cand)

        scored_candidates = self.scorer.score_candidates(
            candidates=valid_candidates,
            objective=objective,
            fused_elements=clean_elements,
            history=history
        )

        return scored_candidates[0] if scored_candidates else None
