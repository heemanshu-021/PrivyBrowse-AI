"""
PrivyBrowse AI — IoU Matcher
Matches elements across detection sources using Intersection over Union.
"""

from typing import List, Tuple, Optional
from backend.perception.core.schemas import BoundingBox, PerceivedElement
from backend.perception.utils.geometry import calculate_iou


class IoUMatcher:
    """
    Matches elements across different detectors (DOM, Vision, OCR)
    using bounding box IoU overlap.
    """

    def __init__(self, iou_threshold: float = 0.35):
        self.iou_threshold = iou_threshold

    def match_elements(
        self,
        primary: List[PerceivedElement],
        secondary: List[PerceivedElement],
    ) -> List[Tuple[int, Optional[int], float]]:
        """
        For each element in `primary`, find the best-matching element in `secondary`.
        Returns list of (primary_idx, secondary_idx_or_None, iou_score).
        """
        used_secondary = set()
        matches: List[Tuple[int, Optional[int], float]] = []

        for i, p_elem in enumerate(primary):
            best_idx = None
            best_iou = 0.0

            for j, s_elem in enumerate(secondary):
                if j in used_secondary:
                    continue
                iou = calculate_iou(p_elem.bbox, s_elem.bbox)
                if iou >= self.iou_threshold and iou > best_iou:
                    best_iou = iou
                    best_idx = j

            if best_idx is not None:
                used_secondary.add(best_idx)
                matches.append((i, best_idx, best_iou))
            else:
                matches.append((i, None, 0.0))

        return matches

    def find_unmatched(
        self,
        total_count: int,
        matches: List[Tuple[int, Optional[int], float]],
        is_secondary: bool = True,
    ) -> List[int]:
        """Return indices of elements that were not matched."""
        if is_secondary:
            matched = {m[1] for m in matches if m[1] is not None}
            return [i for i in range(total_count) if i not in matched]
        else:
            matched = {m[0] for m in matches}
            return [i for i in range(total_count) if i not in matched]
