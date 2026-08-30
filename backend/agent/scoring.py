"""
PrivyBrowse AI — Action Scoring & Ranking Engine
Transparent multi-factor scoring for candidate browser actions:
  Score = 0.40*Semantic + 0.25*Confidence + 0.20*TypeMatch + 0.15*Visibility - HistoryPenalty - RiskPenalty
"""

from typing import List, Dict, Any, Tuple
from backend.agent.schemas import CandidateAction, Objective, RiskLevel


class ActionScorer:
    """
    Ranks candidate browser actions using transparent multi-factor scoring.
    """

    def __init__(self):
        # Weights summing to 1.0
        self.w_semantic = 0.40
        self.w_confidence = 0.25
        self.w_type_match = 0.20
        self.w_visibility = 0.15

    def score_candidates(
        self,
        candidates: List[CandidateAction],
        objective: Objective,
        fused_elements: List[Dict[str, Any]],
        history: List[Dict[str, Any]] = None
    ) -> List[CandidateAction]:
        """
        Calculates scores for all candidates and returns them sorted descending.
        """
        element_map = {el["id"]: el for el in fused_elements if "id" in el}
        hist = history or []

        scored_candidates: List[CandidateAction] = []

        for candidate in candidates:
            el = element_map.get(candidate.target_id) if candidate.target_id else None

            # 1. Semantic Match (0.0 to 1.0)
            s_semantic = self._calculate_semantic_match(candidate, objective, el)

            # 2. Perception Confidence (0.0 to 1.0)
            s_conf = candidate.confidence

            # 3. Type Match (0.0 or 1.0)
            s_type = 1.0 if not objective.target_type else (
                1.0 if (el and el.get("type") == objective.target_type) else 0.4
            )

            # 4. Visibility (1.0 for VISIBLE, 0.5 for PARTIALLY_VISIBLE, 0.1 for OFFSCREEN)
            s_vis = 1.0
            if el:
                vis_attr = el.get("visibility", "VISIBLE")
                if vis_attr == "PARTIALLY_VISIBLE":
                    s_vis = 0.6
                elif vis_attr == "OFFSCREEN":
                    s_vis = 0.1

            # 5. History / Repeat Penalty
            history_penalty = 0.0
            if candidate.target_id:
                # Count recent executions of this exact action & target
                recent_clicks = sum(
                    1 for h in hist[-3:]
                    if h.get("action") == candidate.action.value and h.get("targetId") == candidate.target_id
                )
                history_penalty = recent_clicks * 0.15

            # 6. Unconfirmed High-Risk Penalty
            risk_penalty = 0.0
            if candidate.risk_level == RiskLevel.CRITICAL and candidate.requires_confirmation:
                risk_penalty = 0.10

            # Composite Score calculation
            composite_score = (
                self.w_semantic * s_semantic +
                self.w_confidence * s_conf +
                self.w_type_match * s_type +
                self.w_visibility * s_vis -
                history_penalty -
                risk_penalty
            )
            composite_score = max(0.0, min(1.0, composite_score))

            candidate.score = round(composite_score, 3)
            candidate.score_breakdown = {
                "semantic_match": round(s_semantic, 2),
                "perception_confidence": round(s_conf, 2),
                "type_alignment": round(s_type, 2),
                "visibility_factor": round(s_vis, 2),
                "history_penalty": round(history_penalty, 2),
                "risk_penalty": round(risk_penalty, 2),
                "composite_score": round(composite_score, 3)
            }

            scored_candidates.append(candidate)

        # Sort descending by score
        return sorted(scored_candidates, key=lambda c: c.score, reverse=True)

    def _calculate_semantic_match(
        self,
        candidate: CandidateAction,
        objective: Objective,
        element: Dict[str, Any] = None
    ) -> float:
        """Evaluates keyword overlap between candidate and objective."""
        if not element:
            return 0.50

        el_text = (element.get("text", "") or "").lower()
        attrs = element.get("attributes", {})
        el_placeholder = (element.get("placeholder", "") or attrs.get("placeholder", "") or "").lower()
        el_id = (element.get("id", "") or "").lower()
        el_name = (element.get("name", "") or attrs.get("name", "") or "").lower()

        combined = f"{el_text} {el_placeholder} {el_id} {el_name}"

        # Match against target keywords
        matches = sum(1 for kw in objective.target_keywords if kw.lower() in combined)
        if matches >= 2:
            return 0.98
        elif matches == 1:
            return 0.85

        # Generic semantic intent check
        el_type = str(element.get("type") or element.get("tag") or element.get("tag_name") or "").upper()
        if objective.semantic_intent in ("search_input", "search_query") and el_type in ("INPUT", "TEXTAREA"):
            return 0.80
        if objective.semantic_intent in ("submit_search", "submit_login", "submit_payment") and el_type in ("BUTTON", "SUBMIT"):
            return 0.80

        return 0.40
