"""
PrivyBrowse AI — Coordinate System Utilities
Handles conversions between screenshot, viewport, and browser coordinates.
Accounts for device pixel ratio, scroll position, and screenshot scaling.
"""

from typing import List, Tuple
from backend.perception.core.schemas import BoundingBox, CoordinateSystem


class CoordinateConverter:
    """
    Converts between coordinate systems:
      - Screenshot coordinates (raw pixel positions in the captured image)
      - Viewport coordinates (CSS pixel positions in the browser viewport)
      - Document coordinates (CSS pixel positions in the full scrollable document)
    """

    def __init__(
        self,
        viewport_width: int = 0,
        viewport_height: int = 0,
        screenshot_width: int = 0,
        screenshot_height: int = 0,
        device_pixel_ratio: float = 1.0,
        scroll_x: float = 0.0,
        scroll_y: float = 0.0,
        document_width: float = 0.0,
        document_height: float = 0.0,
    ):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.screenshot_width = screenshot_width or viewport_width
        self.screenshot_height = screenshot_height or viewport_height
        self.dpr = device_pixel_ratio
        self.scroll_x = scroll_x
        self.scroll_y = scroll_y
        self.document_width = document_width or viewport_width
        self.document_height = document_height or viewport_height

        # Scale factors: screenshot pixel → viewport CSS pixel
        if self.screenshot_width > 0 and self.viewport_width > 0:
            self.scale_x = self.viewport_width / self.screenshot_width
        else:
            self.scale_x = 1.0

        if self.screenshot_height > 0 and self.viewport_height > 0:
            self.scale_y = self.viewport_height / self.screenshot_height
        else:
            self.scale_y = 1.0

    def screenshot_to_viewport(self, bbox: BoundingBox) -> BoundingBox:
        """Convert screenshot-space bbox to viewport-space bbox."""
        return BoundingBox(
            x=round(bbox.x * self.scale_x, 1),
            y=round(bbox.y * self.scale_y, 1),
            width=round(bbox.width * self.scale_x, 1),
            height=round(bbox.height * self.scale_y, 1),
        )

    def viewport_to_screenshot(self, bbox: BoundingBox) -> BoundingBox:
        """Convert viewport-space bbox to screenshot-space bbox."""
        inv_sx = 1.0 / self.scale_x if self.scale_x else 1.0
        inv_sy = 1.0 / self.scale_y if self.scale_y else 1.0
        return BoundingBox(
            x=round(bbox.x * inv_sx, 1),
            y=round(bbox.y * inv_sy, 1),
            width=round(bbox.width * inv_sx, 1),
            height=round(bbox.height * inv_sy, 1),
        )

    def viewport_to_document(self, bbox: BoundingBox) -> BoundingBox:
        """Convert viewport-space bbox to full-document-space bbox (accounts for scroll)."""
        return BoundingBox(
            x=round(bbox.x + self.scroll_x, 1),
            y=round(bbox.y + self.scroll_y, 1),
            width=bbox.width,
            height=bbox.height,
        )

    def document_to_viewport(self, bbox: BoundingBox) -> BoundingBox:
        """Convert full-document-space bbox to viewport-space bbox."""
        return BoundingBox(
            x=round(bbox.x - self.scroll_x, 1),
            y=round(bbox.y - self.scroll_y, 1),
            width=bbox.width,
            height=bbox.height,
        )

    def is_in_viewport(self, bbox: BoundingBox) -> bool:
        """Check whether a viewport-space bbox is within the current viewport."""
        if bbox.x + bbox.width <= 0 or bbox.y + bbox.height <= 0:
            return False
        if bbox.x >= self.viewport_width or bbox.y >= self.viewport_height:
            return False
        return True

    def classify_visibility(self, bbox: BoundingBox) -> str:
        """
        Classify a viewport-space bbox's visibility status.
        Returns one of: VISIBLE, PARTIALLY_VISIBLE, OFFSCREEN
        """
        if not self.viewport_width or not self.viewport_height:
            return "VISIBLE"  # Cannot determine without viewport dimensions

        # Completely outside viewport
        if (bbox.x >= self.viewport_width or bbox.y >= self.viewport_height
                or bbox.x + bbox.width <= 0 or bbox.y + bbox.height <= 0):
            return "OFFSCREEN"

        # Partially clipped by viewport edges
        if (bbox.x < 0 or bbox.y < 0
                or bbox.x + bbox.width > self.viewport_width
                or bbox.y + bbox.height > self.viewport_height):
            return "PARTIALLY_VISIBLE"

        return "VISIBLE"

    def get_coordinate_system(self) -> CoordinateSystem:
        """Return a CoordinateSystem metadata object."""
        return CoordinateSystem(
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            screenshot_width=self.screenshot_width,
            screenshot_height=self.screenshot_height,
            device_pixel_ratio=self.dpr,
            scroll_x=self.scroll_x,
            scroll_y=self.scroll_y,
            document_width=self.document_width,
            document_height=self.document_height,
            scale_x=round(self.scale_x, 4),
            scale_y=round(self.scale_y, 4),
        )


def normalize_bbox_to_viewport(
    xyxy: List[float],
    scale_x: float = 1.0,
    scale_y: float = 1.0
) -> BoundingBox:
    """Convert an [x1, y1, x2, y2] array to a BoundingBox, applying optional scaling."""
    x1, y1, x2, y2 = xyxy[0], xyxy[1], xyxy[2], xyxy[3]
    return BoundingBox(
        x=round(x1 * scale_x, 1),
        y=round(y1 * scale_y, 1),
        width=round((x2 - x1) * scale_x, 1),
        height=round((y2 - y1) * scale_y, 1),
    )
