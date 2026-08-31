"""
PrivyBrowse AI — Visual Element Detector (OpenCV)
Detects interactive UI elements from screenshot images using contour analysis,
morphological operations, edge detection, and geometric heuristic classification.
No ML model download required.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from backend.perception.core.schemas import BoundingBox, PerceivedElement


import hashlib
from collections import OrderedDict

class VisualDetector:
    """
    Uses OpenCV computer vision to detect visual interactive elements
    (buttons, inputs, checkboxes, etc.) from a raw screenshot image.
    Includes LRU contour memoization for identical visual frames.

    Pipeline:
      1. Grayscale conversion
      2. Adaptive thresholding (handles dark/light mode)
      3. Morphological close (merge fragmented contours)
      4. Contour extraction (RETR_TREE for hierarchy)
      5. Bounding rect extraction + size filtering
      6. Aspect-ratio + size heuristic classification
      7. Canny edge density analysis for confidence adjustment
      8. NMS-like duplicate suppression
    """

    # Size bounds for classification heuristics (in pixels)
    MIN_ELEMENT_SIZE = 8
    MAX_ELEMENT_RATIO = 0.92  # Skip contours larger than 92% of image dimension

    def __init__(self, max_cache_entries: int = 50):
        self._cache: OrderedDict[str, List[PerceivedElement]] = OrderedDict()
        self._max_cache = max_cache_entries

    def clear_cache(self):
        """Invalidates visual contour cache."""
        self._cache.clear()

    def detect(self, img: np.ndarray) -> List[PerceivedElement]:
        """
        Detect UI elements from a BGR or grayscale OpenCV image.
        Returns PerceivedElement objects with source=VISION.
        """
        if img is None:
            return []

        h, w = img.shape[:2]
        if h == 0 or w == 0:
            return []

        # Fast hash check for identical frame
        try:
            frame_hash = hashlib.md5(img.tobytes()[:32768]).hexdigest() + f"_{img.shape}"
            if frame_hash in self._cache:
                self._cache.move_to_end(frame_hash)
                return [PerceivedElement(**e.model_dump()) for e in self._cache[frame_hash]]
        except Exception:
            frame_hash = None

        # Convert to grayscale if needed
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Adaptive thresholding (handles both light and dark backgrounds)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Morphological close to merge fragmented button/input borders
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Find contours with hierarchy
        contours, hierarchy = cv2.findContours(
            closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )

        # Canny edges for density-based confidence adjustment
        edges = cv2.Canny(gray, 50, 150)

        candidates: List[Tuple[BoundingBox, str, float]] = []

        for i, cnt in enumerate(contours):
            x, y, rw, rh = cv2.boundingRect(cnt)

            # Filter by minimum size
            if rw < self.MIN_ELEMENT_SIZE or rh < self.MIN_ELEMENT_SIZE:
                continue

            # Filter out image-spanning containers
            if rw > w * self.MAX_ELEMENT_RATIO and rh > h * self.MAX_ELEMENT_RATIO:
                continue

            # Skip very large containers (more than 60% of image area)
            if (rw * rh) > (w * h * 0.60):
                continue

            # Classify based on aspect ratio, absolute size, and geometry
            aspect_ratio = rw / float(rh) if rh > 0 else 1.0
            el_type, confidence = self._classify_element(rw, rh, aspect_ratio, w, h)

            # Adjust confidence using edge density within the bounding region
            confidence = self._adjust_confidence_by_edges(edges, x, y, rw, rh, confidence)

            bbox = BoundingBox(x=float(x), y=float(y), width=float(rw), height=float(rh))
            candidates.append((bbox, el_type, confidence))

        # NMS-like suppression: remove overlapping duplicates, keep higher confidence
        elements = self._suppress_duplicates(candidates, iou_threshold=0.45)

        # Assign stable IDs
        result: List[PerceivedElement] = []
        for idx, (bbox, el_type, conf) in enumerate(elements):
            interactive = el_type in {"BUTTON", "INPUT", "TEXTAREA", "CHECKBOX", "RADIO", "SELECT", "LINK"}
            result.append(PerceivedElement(
                id=f"vis-{idx:03d}",
                type=el_type,
                label="",  # Visual detector cannot determine text labels
                text="",
                bbox=bbox,
                confidence=round(conf, 3),
                visible=True,
                enabled=True,
                interactive=interactive,
                sources=["VISION"],
                attributes={},
                visibility="VISIBLE",
            ))

        if frame_hash is not None:
            self._cache[frame_hash] = result
            if len(self._cache) > self._max_cache:
                self._cache.popitem(last=False)

        return result

    def _classify_element(
        self, rw: int, rh: int, aspect_ratio: float, img_w: int, img_h: int
    ) -> Tuple[str, float]:
        """
        Heuristic classification based on size and aspect ratio.
        Returns (element_type, base_confidence).
        """
        # Checkboxes / Radio buttons: small squares
        if 10 <= rw <= 32 and 10 <= rh <= 32 and 0.75 <= aspect_ratio <= 1.35:
            return ("CHECKBOX", 0.82)

        # Icons: small-ish squares or near-squares
        if 16 <= rw <= 48 and 16 <= rh <= 48 and 0.7 <= aspect_ratio <= 1.5:
            return ("ICON", 0.70)

        # Input fields: wide horizontal rectangles of moderate height
        if 80 <= rw and 18 <= rh <= 60 and aspect_ratio >= 2.5:
            return ("INPUT", 0.84)

        # Textareas: wider and taller than inputs
        if 120 <= rw and 60 <= rh <= 300 and aspect_ratio >= 1.5:
            return ("TEXTAREA", 0.78)

        # Buttons: moderately wide, short-to-medium height
        if 40 <= rw <= 400 and 20 <= rh <= 70 and 1.2 <= aspect_ratio <= 8.0:
            return ("BUTTON", 0.80)

        # Navigation bars: very wide, thin
        if rw > img_w * 0.5 and rh < 80 and aspect_ratio > 6:
            return ("NAV", 0.72)

        # Images: medium-to-large regions with moderate aspect ratio
        if rw >= 60 and rh >= 60 and 0.3 <= aspect_ratio <= 3.0:
            area_ratio = (rw * rh) / (img_w * img_h)
            if 0.01 <= area_ratio <= 0.40:
                return ("IMAGE", 0.68)

        # Cards/containers: larger rectangular regions
        if rw >= 150 and rh >= 80:
            return ("CARD", 0.65)

        # Headings: wide text blocks with moderate height
        if rw >= 100 and 16 <= rh <= 50 and aspect_ratio >= 3.0:
            return ("HEADING", 0.70)

        # Default
        return ("ELEMENT", 0.60)

    def _adjust_confidence_by_edges(
        self, edges: np.ndarray, x: int, y: int, w: int, h: int, base_confidence: float
    ) -> float:
        """
        Boost or penalize confidence based on edge density within the bounding box.
        A well-defined UI element typically has strong edges at its borders.
        """
        ih, iw = edges.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(iw, x + w), min(ih, y + h)
        if x2 <= x1 or y2 <= y1:
            return base_confidence

        roi = edges[y1:y2, x1:x2]
        edge_density = np.count_nonzero(roi) / max(1, roi.size)

        # Elements with moderate edge density (~5-40%) are likely real UI elements
        if 0.05 <= edge_density <= 0.40:
            return min(1.0, base_confidence + 0.05)
        elif edge_density > 0.50:
            # Too many edges — likely noise or text block, lower confidence
            return max(0.3, base_confidence - 0.10)
        elif edge_density < 0.02:
            # Almost no edges — likely not an interactive element
            return max(0.3, base_confidence - 0.08)

        return base_confidence

    def _suppress_duplicates(
        self,
        candidates: List[Tuple[BoundingBox, str, float]],
        iou_threshold: float = 0.45,
    ) -> List[Tuple[BoundingBox, str, float]]:
        """Remove overlapping detections, keeping higher confidence ones."""
        if not candidates:
            return []

        # Sort by confidence descending
        sorted_c = sorted(candidates, key=lambda x: x[2], reverse=True)
        kept = []

        for bbox, el_type, conf in sorted_c:
            suppress = False
            for kept_bbox, _, _ in kept:
                iou = self._iou(bbox, kept_bbox)
                if iou >= iou_threshold:
                    suppress = True
                    break
            if not suppress:
                kept.append((bbox, el_type, conf))

        return kept

    def _iou(self, a: BoundingBox, b: BoundingBox) -> float:
        """Calculate IoU between two BoundingBox objects."""
        x1 = max(a.x, b.x)
        y1 = max(a.y, b.y)
        x2 = min(a.x + a.width, b.x + b.width)
        y2 = min(a.y + a.height, b.y + b.height)
        inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        if inter == 0:
            return 0.0
        area_a = a.width * a.height
        area_b = b.width * b.height
        return inter / (area_a + area_b - inter)
