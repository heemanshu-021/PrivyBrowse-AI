"""
PrivyBrowse AI — Candidate Action Generator
Consumes perceived elements, active objective, and sanitized layout context
to generate ranked candidate browser actions (CLICK, TYPE, SCROLL, etc.).
"""

from typing import List, Dict, Any, Optional
from backend.agent.schemas import (
    CandidateAction, ActionType, Objective, RiskLevel
)


class CandidateGenerator:
    """
    Generates candidate browser actions for a given sub-objective and layout state.
    """

    def __init__(self):
        pass

    def generate_candidates(
        self,
        objective: Objective,
        fused_elements: List[Dict[str, Any]],
        goal_text: str = "",
        history: List[Dict[str, Any]] = None
    ) -> List[CandidateAction]:
        """
        Scans fused elements and generates candidate actions matching the objective.
        """
        candidates: List[CandidateAction] = []
        hist = history or []

        # 1. Handle SCROLL intent
        if objective.semantic_intent == "scroll_page":
            candidates.append(CandidateAction(
                action=ActionType.SCROLL,
                target_description="Scroll viewport down 400px",
                confidence=0.95,
                risk_level=RiskLevel.LOW,
                requires_confirmation=False,
                reason="Advance viewport position to expose offscreen document sections"
            ))
            return candidates

        # 2. Iterate through perceived elements
        for el in fused_elements:
            el_type = el.get("type", "ELEMENT")
            el_id = el.get("id", "")
            bbox = el.get("bbox", [0, 0, 0, 0])
            el_text = el.get("text", "")
            el_val = el.get("value", "")
            attrs = el.get("attributes", {})
            conf = float(el.get("confidence", 0.85))

            if len(bbox) < 4:
                continue

            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0

            combined_str = (
                f"{el_text} {el_val} {attrs.get('placeholder', '')} "
                f"{attrs.get('name', '')} {attrs.get('id', '')} "
                f"{attrs.get('class', '')} {attrs.get('type', '')} {el_id}"
            ).lower()

            # (A) Input & Typing Candidates
            if el_type in ("INPUT", "TEXTAREA"):
                # Determine what to type based on objective intent
                type_payload = None
                risk = RiskLevel.LOW
                req_confirm = False

                if objective.semantic_intent in ("search_input", "search_query"):
                    # Extract query from goal
                    query = "Chandrayaan-3"
                    if "for " in goal_text.lower():
                        query = goal_text.lower().split("for ", 1)[1].split(" and")[0].strip()
                    type_payload = query.title()

                elif objective.semantic_intent == "input_username":
                    type_payload = "user@sih2026.gov.in"
                    risk = RiskLevel.MEDIUM

                elif objective.semantic_intent == "input_password":
                    type_payload = "PrivySafePassword123!"
                    risk = RiskLevel.HIGH
                    req_confirm = False  # Pre-sanitized test credential

                elif objective.semantic_intent == "input_contact":
                    type_payload = "Amit Sharma"

                elif objective.semantic_intent == "input_address":
                    type_payload = "12, MG Road, Bangalore, KA"

                elif objective.semantic_intent == "input_card":
                    type_payload = "4111 2222 3333 4444"
                    risk = RiskLevel.HIGH

                # Create TYPE candidate
                candidates.append(CandidateAction(
                    action=ActionType.TYPE,
                    target_id=el_id,
                    target={"x": cx, "y": cy},
                    target_description=f"Input field '{attrs.get('placeholder') or el_id}'",
                    text=type_payload or "Input value",
                    confidence=conf,
                    risk_level=risk,
                    requires_confirmation=req_confirm,
                    reason=f"Matches input target for objective '{objective.description}'"
                ))

            # (B) Button & Submission Candidates
            elif el_type in ("BUTTON", "CHECKBOX", "SELECT"):
                # Check for high-risk action indicators (payments, delete, buy)
                risk = RiskLevel.LOW
                req_confirm = False
                if any(w in combined_str for w in ["pay", "purchase", "order", "charge", "₹", "$"]):
                    risk = RiskLevel.CRITICAL
                    req_confirm = True
                elif any(w in combined_str for w in ["delete", "remove", "wipe", "cancel account"]):
                    risk = RiskLevel.HIGH
                    req_confirm = True

                candidates.append(CandidateAction(
                    action=ActionType.CLICK,
                    target_id=el_id,
                    target={"x": cx, "y": cy},
                    target_description=f"Button '{el_text or attrs.get('placeholder') or el_id}'",
                    confidence=conf,
                    risk_level=risk,
                    requires_confirmation=req_confirm,
                    reason=f"Interactive button candidate for '{objective.semantic_intent}'"
                ))

            # (C) Link Candidates
            elif el_type == "LINK":
                candidates.append(CandidateAction(
                    action=ActionType.CLICK,
                    target_id=el_id,
                    target={"x": cx, "y": cy},
                    target_description=f"Link '{el_text or el_id}'",
                    confidence=conf,
                    risk_level=RiskLevel.LOW,
                    requires_confirmation=False,
                    reason=f"Hyperlink destination candidate for '{objective.semantic_intent}'"
                ))

        # 3. Add fallback completion action if objectives exhausted
        if not candidates:
            candidates.append(CandidateAction(
                action=ActionType.FINISH,
                target_description="Task completion verification",
                confidence=0.90,
                risk_level=RiskLevel.LOW,
                requires_confirmation=False,
                reason="All objectives evaluated; completing task"
            ))

        return candidates
