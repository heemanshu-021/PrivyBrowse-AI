"""
PrivyBrowse AI — Candidate Action Generator
Consumes perceived elements, active objective, and sanitized layout context
to generate ranked candidate browser actions (CLICK, TYPE, SCROLL, etc.).
Derives typing payloads and element associations dynamically.
"""

import re
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

    def _extract_query_payload(self, objective: Objective, goal_text: str) -> str:
        """Extracts dynamic query string from objective description or goal."""
        m = re.search(r"'(.*?)'", objective.description)
        if m and m.group(1).strip():
            return m.group(1).strip()
        
        # Fallback to goal text extraction
        query_m = re.search(r'(?:search\s+for|find|lookup)\s+["\']?([^"\',.;\n]+?)["\']?(?:\s+on|\s+and|$|\.)', goal_text, re.IGNORECASE)
        if query_m:
            return query_m.group(1).strip()
            
        return goal_text.strip()

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
            raw_type = str(el.get("type") or el.get("tag") or el.get("tag_name") or el.get("tagName") or "ELEMENT").upper()
            attrs = el.get("attributes", {})
            input_type_attr = str(el.get("inputType") or attrs.get("type", "") or el.get("type", "")).lower()
            tag_name = str(el.get("tag") or el.get("tag_name") or "").lower()

            is_input = (
                raw_type in ("INPUT", "TEXTAREA") or
                tag_name in ("input", "textarea") or
                input_type_attr in ("text", "search", "email", "password", "tel", "number", "url", "textarea")
            )
            is_button = (
                raw_type in ("BUTTON", "CHECKBOX", "SELECT") or
                tag_name in ("button", "select") or
                input_type_attr in ("button", "submit", "reset") or
                attrs.get("role") in ("button", "tab", "menuitem")
            )
            is_link = (
                raw_type in ("LINK", "A") or
                tag_name in ("a", "link") or
                attrs.get("role") == "link"
            )

            el_id = el.get("id", "")
            bbox_raw = el.get("bbox", [0, 0, 0, 0])
            if isinstance(bbox_raw, list) and len(bbox_raw) >= 4:
                bbox = [float(bbox_raw[0]), float(bbox_raw[1]), float(bbox_raw[2]), float(bbox_raw[3])]
            elif isinstance(bbox_raw, dict):
                x = float(bbox_raw.get("x", bbox_raw.get("left", 0)))
                y = float(bbox_raw.get("y", bbox_raw.get("top", 0)))
                w = float(bbox_raw.get("width", 0))
                h = float(bbox_raw.get("height", 0))
                if w <= 0 and "right" in bbox_raw:
                    w = float(bbox_raw["right"]) - x
                if h <= 0 and "bottom" in bbox_raw:
                    h = float(bbox_raw["bottom"]) - y
                bbox = [x, y, x + w, y + h]
            elif hasattr(bbox_raw, "to_xyxy"):
                bbox = [float(c) for c in bbox_raw.to_xyxy()]
            else:
                bbox = [0.0, 0.0, 0.0, 0.0]

            el_text = el.get("text", "")
            el_val = el.get("value", "")
            conf = float(el.get("confidence", 0.85))

            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0

            combined_str = (
                f"{el_text} {el_val} {el.get('placeholder', '')} {attrs.get('placeholder', '')} "
                f"{el.get('name', '')} {attrs.get('name', '')} {attrs.get('id', '')} "
                f"{attrs.get('class', '')} {attrs.get('type', '')} {el_id}"
            ).lower()

            # (A) Input & Typing Candidates
            if is_input:
                type_payload = None
                risk = RiskLevel.LOW
                req_confirm = False

                if objective.semantic_intent in ("search_input", "search_query"):
                    type_payload = self._extract_query_payload(objective, goal_text)

                elif objective.semantic_intent == "input_username":
                    m_email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', goal_text)
                    type_payload = m_email.group(0) if m_email else "user@sih2026.gov.in"
                    risk = RiskLevel.MEDIUM

                elif objective.semantic_intent == "input_password":
                    type_payload = "••••••••"
                    risk = RiskLevel.HIGH
                    req_confirm = False

                elif objective.semantic_intent == "input_contact":
                    type_payload = "User Contact"

                elif objective.semantic_intent == "input_address":
                    type_payload = "123 Innovation Boulevard"

                elif objective.semantic_intent == "input_card":
                    type_payload = "•••• •••• •••• 4444"
                    risk = RiskLevel.HIGH

                candidates.append(CandidateAction(
                    action=ActionType.TYPE,
                    target_id=el_id,
                    target={"x": cx, "y": cy},
                    target_description=f"Input field '{el.get('placeholder') or attrs.get('placeholder') or el.get('name') or attrs.get('name') or el_id}'",
                    text=type_payload or "Input value",
                    confidence=conf,
                    risk_level=risk,
                    requires_confirmation=req_confirm,
                    reason=f"Matches input target for objective '{objective.description}'"
                ))

            # (B) Button & Submission Candidates
            elif is_button:
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
                    target_description=f"Button '{el_text or el.get('placeholder') or attrs.get('placeholder') or attrs.get('name') or el_id}'",
                    confidence=conf,
                    risk_level=risk,
                    requires_confirmation=req_confirm,
                    reason=f"Interactive button candidate for '{objective.semantic_intent}'"
                ))

            # (C) Link Candidates
            elif is_link:
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
