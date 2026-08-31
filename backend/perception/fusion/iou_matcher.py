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
        if not primary:
            return []
        if not secondary:
            return [(i, None, 0.0) for i in range(len(primary))]

        used_secondary = set()
        matches: List[Tuple[int, Optional[int], float]] = []

        # Precompute secondary bounding box coordinates for fast AABB reject
        sec_coords = [
            (
                s_elem.bbox.x,
                s_elem.bbox.y,
                s_elem.bbox.x + s_elem.bbox.width,
                s_elem.bbox.y + s_elem.bbox.height,
                s_elem.bbox
            )
            for s_elem in secondary
        ]

        for i, p_elem in enumerate(primary):
            best_idx = None
            best_iou = 0.0
            px1, py1 = p_elem.bbox.x, p_elem.bbox.y
            px2, py2 = px1 + p_elem.bbox.width, py1 + p_elem.bbox.height

            for j, (sx1, sy1, sx2, sy2, s_bbox) in enumerate(sec_coords):
                if j in used_secondary:
                    continue
                # Fast AABB disjoint rejection
                if px2 <= sx1 or sx2 <= px1 or py2 <= sy1 or sy2 <= py1:
                    continue
                iou = calculate_iou(p_elem.bbox, s_bbox)
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
