"""
PrivyBrowse AI — Page Change & State Mutation Detector
Evaluates post-action browser state signals (URL change, DOM node delta, scroll offset)
to invalidate stale perception snapshots and trigger fresh observation cycles.
"""

from typing import List, Dict, Any, Optional
from backend.actions.schemas import PageChangeSignal


class PageChangeDetector:
    """
    Analyzes before/after snapshots of the browser environment.
    """

    def __init__(self):
        pass

    def detect_changes(
        self,
        prev_url: str,
        current_url: str,
        prev_elements: List[Dict[str, Any]],
        current_elements: List[Dict[str, Any]],
        action_name: str = ""
    ) -> PageChangeSignal:
        """
        Compares previous and current browser states to evaluate mutation signals.
        """
        url_changed = bool(prev_url and current_url and prev_url != current_url)
        
        # Element set & attribute comparison
        prev_ids = {e.get("id") for e in prev_elements if "id" in e}
        curr_ids = {e.get("id") for e in current_elements if "id" in e}

        id_delta = prev_ids != curr_ids
        count_delta = len(prev_elements) != len(current_elements)
        
        # Check value mutations on existing nodes (e.g. typing)
        value_mutated = False
        if not id_delta and not count_delta:
            prev_val_map = {e.get("id"): e.get("value", "") for e in prev_elements if "id" in e}
            for ce in current_elements:
                cid = ce.get("id")
                if cid in prev_val_map and prev_val_map[cid] != ce.get("value", ""):
                    value_mutated = True
                    break

        dom_mutated = id_delta or count_delta or value_mutated
        scroll_changed = (action_name in ("SCROLL", "SCROLL_UP", "SCROLL_DOWN"))
        
        has_changed = url_changed or dom_mutated or scroll_changed

        summaries = []
        if url_changed:
            summaries.append(f"URL navigated to '{current_url}'")
        if id_delta or count_delta:
            summaries.append(f"DOM tree mutated ({len(prev_elements)} -> {len(current_elements)} elements)")
        if value_mutated:
            summaries.append("Form field value updated")
        if scroll_changed:
            summaries.append("Viewport scroll offset modified")

        change_summary = "; ".join(summaries) if summaries else "No state change detected"

        return PageChangeSignal(
            page_changed=has_changed,
            url_changed=url_changed,
            dom_mutated=dom_mutated,
            scroll_changed=scroll_changed,
            previous_url=prev_url,
            current_url=current_url,
            change_summary=change_summary
        )
