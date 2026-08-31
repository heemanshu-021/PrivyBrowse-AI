"""
PrivyBrowse AI — Observation Differencer
Lightweight, privacy-preserving observation state diffing between pre-action and post-action snapshots.
Measures structural, topological, URL, scroll, and element-level state transitions.
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field


class StateDiff(BaseModel):
    """Structured delta between pre-action and post-action browser states."""
    url_changed: bool = False
    prev_url: str = ""
    curr_url: str = ""
    
    title_changed: bool = False
    prev_title: str = ""
    curr_title: str = ""
    
    dom_mutated: bool = False
    elements_added_count: int = 0
    elements_removed_count: int = 0
    added_element_ids: List[str] = Field(default_factory=list)
    removed_element_ids: List[str] = Field(default_factory=list)
    
    target_found: bool = False
    target_value_changed: bool = False
    target_value_populated: bool = False
    target_state_changed: bool = False
    
    scroll_delta_x: float = 0.0
    scroll_delta_y: float = 0.0
    scroll_changed: bool = False
    is_at_scroll_boundary: bool = False
    
    modal_appeared: bool = False
    modal_disappeared: bool = False
    
    evidence: List[str] = Field(default_factory=list)


class ObservationDifferencer:
    """
    Computes deterministic, privacy-safe state diffs to evaluate whether an action
    actually changed the browser state.
    """

    @classmethod
    def compute_diff(
        cls,
        prev_elements: List[Dict[str, Any]],
        curr_elements: List[Dict[str, Any]],
        prev_url: str = "",
        curr_url: str = "",
        prev_title: str = "",
        curr_title: str = "",
        target_id: Optional[str] = None,
        prev_scroll: Optional[Dict[str, float]] = None,
        curr_scroll: Optional[Dict[str, float]] = None,
        is_sensitive: bool = False
    ) -> StateDiff:
        """
        Computes StateDiff between two snapshots.
        """
        diff = StateDiff()
        evidence = []

        # 1. URL change
        diff.prev_url = prev_url
        diff.curr_url = curr_url
        if prev_url and curr_url:
            norm_prev = prev_url.rstrip("/")
            norm_curr = curr_url.rstrip("/")
            if norm_prev != norm_curr:
                diff.url_changed = True
                evidence.append(f"URL changed: '{prev_url}' -> '{curr_url}'")

        # 2. Title change
        diff.prev_title = prev_title
        diff.curr_title = curr_title
        if prev_title and curr_title and prev_title != curr_title:
            diff.title_changed = True
            evidence.append(f"Page title changed: '{prev_title}' -> '{curr_title}'")

        # 3. DOM element set diff
        prev_id_map = {e.get("id"): e for e in prev_elements if e.get("id")}
        curr_id_map = {e.get("id"): e for e in curr_elements if e.get("id")}

        prev_ids = set(prev_id_map.keys())
        curr_ids = set(curr_id_map.keys())

        added_ids = list(curr_ids - prev_ids)
        removed_ids = list(prev_ids - curr_ids)

        diff.added_element_ids = added_ids
        diff.removed_element_ids = removed_ids
        diff.elements_added_count = len(added_ids)
        diff.elements_removed_count = len(removed_ids)

        if added_ids or removed_ids:
            diff.dom_mutated = True
            evidence.append(f"DOM mutated: +{len(added_ids)} nodes, -{len(removed_ids)} nodes")

        # 4. Target element specific analysis
        if target_id:
            curr_target = curr_id_map.get(target_id)
            prev_target = prev_id_map.get(target_id)

            if curr_target:
                diff.target_found = True
                # Check value change
                curr_val = str(curr_target.get("value") or curr_target.get("text") or "")
                prev_val = str(prev_target.get("value") or prev_target.get("text") or "") if prev_target else ""

                if is_sensitive:
                    # Privacy-Safe Check: verify field is populated without exposing raw value
                    if len(curr_val) > 0 or curr_target.get("sensitive") or "REDACTED" in curr_val:
                        diff.target_value_populated = True
                        diff.target_value_changed = True
                        evidence.append(f"Target '{target_id}' populated with secure masked value")
                else:
                    if curr_val != prev_val:
                        diff.target_value_changed = True
                        diff.target_value_populated = len(curr_val.strip()) > 0
                        evidence.append(f"Target '{target_id}' value updated")

                # Check state attribute changes (disabled, checked, aria-expanded, state_clicked, value, selectedIndex)
                if prev_target:
                    for attr in ("disabled", "checked", "aria-expanded", "hidden", "selected", "state_clicked", "value", "selectedIndex"):
                        p_attr = prev_target.get(attr) or prev_target.get("attributes", {}).get(attr)
                        c_attr = curr_target.get(attr) or curr_target.get("attributes", {}).get(attr)
                        if p_attr != c_attr:
                            diff.target_state_changed = True
                            if is_sensitive and attr == "value":
                                evidence.append(f"Target '{target_id}' attribute '{attr}' changed [SENSITIVE VALUE MASKED]")
                            else:
                                evidence.append(f"Target '{target_id}' attribute '{attr}' changed: {p_attr} -> {c_attr}")

        # 5. Scroll Geometry Diff
        if prev_scroll and curr_scroll:
            p_x = prev_scroll.get("x", prev_scroll.get("scrollX", 0.0))
            p_y = prev_scroll.get("y", prev_scroll.get("scrollY", 0.0))
            c_x = curr_scroll.get("x", curr_scroll.get("scrollX", 0.0))
            c_y = curr_scroll.get("y", curr_scroll.get("scrollY", 0.0))

            diff.scroll_delta_x = c_x - p_x
            diff.scroll_delta_y = c_y - p_y

            if abs(diff.scroll_delta_x) > 1.0 or abs(diff.scroll_delta_y) > 1.0:
                diff.scroll_changed = True
                evidence.append(f"Scroll position shifted by ({diff.scroll_delta_x:.0f}, {diff.scroll_delta_y:.0f}) px")

            # Check boundary condition
            doc_h = curr_scroll.get("documentHeight", 1080.0)
            vp_h = curr_scroll.get("viewportHeight", 1080.0)
            max_y = curr_scroll.get("maxScrollY", max(0.0, doc_h - vp_h))
            if (c_y >= max_y - 5.0 and max_y > 0) or (c_y <= 5.0 and diff.scroll_delta_y < 0):
                diff.is_at_scroll_boundary = True
                evidence.append("Viewport reached scroll boundary")

        # 6. Modal / Dialog detection
        modal_keywords = {"modal", "dialog", "backdrop", "popup", "confirm-delete", "overlay"}
        for el_id in added_ids:
            el = curr_id_map.get(el_id, {})
            tag = str(el.get("tag", "")).lower()
            role = str(el.get("role", "")).lower()
            text = str(el.get("text", "")).lower()
            if tag in ("dialog", "modal") or role in ("dialog", "alertdialog") or any(k in el_id.lower() or k in text for k in modal_keywords):
                diff.modal_appeared = True
                evidence.append(f"Modal dialog element '{el_id}' appeared")
                break

        for el_id in removed_ids:
            if any(k in el_id.lower() for k in modal_keywords):
                diff.modal_disappeared = True
                evidence.append(f"Modal dialog element '{el_id}' disappeared")
                break

        diff.evidence = evidence
        return diff
