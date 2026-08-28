"""
PrivyBrowse AI — Geometry Utilities
Bounding box intersection, overlap, containment, and NMS operations.
"""

from typing import List, Tuple
from backend.perception.core.schemas import BoundingBox


def calculate_iou(a: BoundingBox, b: BoundingBox) -> float:
    """
    Calculate Intersection over Union (IoU) of two bounding boxes.
    Returns a value in [0.0, 1.0].
    """
    x1 = max(a.x, b.x)
    y1 = max(a.y, b.y)
    x2 = min(a.x + a.width, b.x + b.width)
    y2 = min(a.y + a.height, b.y + b.height)

    inter_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if inter_area == 0.0:
        return 0.0

    area_a = a.width * a.height
    area_b = b.width * b.height
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0

    return inter_area / union_area


def calculate_iou_xyxy(box_a: List[float], box_b: List[float]) -> float:
    """IoU using [x1, y1, x2, y2] format."""
    a = BoundingBox.from_xyxy(*box_a[:4])
    b = BoundingBox.from_xyxy(*box_b[:4])
    return calculate_iou(a, b)


def is_contained(inner: BoundingBox, outer: BoundingBox, threshold: float = 0.85) -> bool:
    """Check if inner bbox is substantially contained within outer bbox."""
    x1 = max(inner.x, outer.x)
    y1 = max(inner.y, outer.y)
    x2 = min(inner.x + inner.width, outer.x + outer.width)
    y2 = min(inner.y + inner.height, outer.y + outer.height)

    inter_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    inner_area = inner.width * inner.height
    if inner_area <= 0:
        return False
    return (inter_area / inner_area) >= threshold


def non_max_suppression(
    boxes: List[Tuple[BoundingBox, float, int]],
    iou_threshold: float = 0.50
) -> List[int]:
    """
    Non-maximum suppression on a list of (bbox, confidence, original_index) tuples.
    Returns indices of kept boxes, preferring higher-confidence boxes.
    """
    if not boxes:
        return []

    # Sort by confidence descending
    sorted_items = sorted(boxes, key=lambda x: x[1], reverse=True)
    kept_indices = []

    for bbox, conf, idx in sorted_items:
        suppress = False
        for kept_idx in kept_indices:
            # Find the kept box
            kept_bbox = next(b for b, c, i in sorted_items if i == kept_idx)
            if calculate_iou(bbox, kept_bbox) >= iou_threshold:
                suppress = True
                break
        if not suppress:
            kept_indices.append(idx)

    return kept_indices


def merge_bboxes(boxes: List[BoundingBox]) -> BoundingBox:
    """Merge a list of bounding boxes into a single enclosing bbox."""
    if not boxes:
        return BoundingBox(x=0, y=0, width=0, height=0)

    min_x = min(b.x for b in boxes)
    min_y = min(b.y for b in boxes)
    max_x = max(b.x + b.width for b in boxes)
    max_y = max(b.y + b.height for b in boxes)

    return BoundingBox(
        x=round(min_x, 1),
        y=round(min_y, 1),
        width=round(max_x - min_x, 1),
        height=round(max_y - min_y, 1),
    )


def bbox_distance(a: BoundingBox, b: BoundingBox) -> float:
    """Euclidean distance between the centers of two bounding boxes."""
    cx_a, cy_a = a.center
    cx_b, cy_b = b.center
    return ((cx_a - cx_b) ** 2 + (cy_a - cy_b) ** 2) ** 0.5
