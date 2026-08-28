"""
PrivyBrowse AI — Reasoning Engine & Decision Planner
Provides an abstract BaseReasoningEngine interface and a high-precision LocalRuleBasedEngine.
Strictly accepts ONLY sanitized layout context.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.agent.schemas import CandidateAction, Objective, AgentTask
from backend.agent.candidate_generator import CandidateGenerator
from backend.agent.scoring import ActionScorer


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
    """

    def __init__(self):
        from backend.security.injection_guard import InjectionGuard
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
        2. Generates candidate actions for active objective
        3. Scores and ranks candidate actions
        4. Returns the highest-scoring candidate
        """
        clean_elements, _ = self.injection_guard.sanitize_untrusted_elements(sanitized_elements)

        candidates = self.generator.generate_candidates(
            objective=objective,
            fused_elements=clean_elements,
            goal_text=task.goal,
            history=history
        )


        if not candidates:
            return None

        scored_candidates = self.scorer.score_candidates(
            candidates=candidates,
            objective=objective,
            fused_elements=sanitized_elements,
            history=history
        )

        return scored_candidates[0] if scored_candidates else None
