"""
PrivyBrowse AI — Image Preprocessing
Lightweight operations that preserve coordinate mapping.
"""

import cv2
import numpy as np
from typing import Tuple, Optional


class ImageProcessor:
    """
    Provides lightweight image preprocessing for the perception pipeline.
    All operations track scaling factors so downstream bounding boxes
    can be mapped back to original viewport coordinates.
    """

    def __init__(self):
        self.scale_x: float = 1.0
        self.scale_y: float = 1.0
        self.original_size: Tuple[int, int] = (0, 0)  # (width, height)

    def decode(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Decode raw bytes to an OpenCV BGR image."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            h, w = img.shape[:2]
            self.original_size = (w, h)
            self.scale_x = 1.0
            self.scale_y = 1.0
        return img

    def to_grayscale(self, img: np.ndarray) -> np.ndarray:
        """Convert BGR image to grayscale."""
        if len(img.shape) == 2:
            return img
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def adaptive_resize(self, img: np.ndarray, max_dimension: int = 1920) -> np.ndarray:
        """
        Resize large images to keep max dimension within limit.
        Updates internal scale factors for coordinate mapping.
        """
        h, w = img.shape[:2]
        if max(w, h) <= max_dimension:
            return img

        if w >= h:
            new_w = max_dimension
            new_h = int(h * (max_dimension / w))
        else:
            new_h = max_dimension
            new_w = int(w * (max_dimension / h))

        self.scale_x = w / new_w
        self.scale_y = h / new_h
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def enhance_contrast(self, gray: np.ndarray) -> np.ndarray:
        """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def denoise(self, img: np.ndarray, strength: int = 7) -> np.ndarray:
        """Light bilateral denoising that preserves edges."""
        return cv2.bilateralFilter(img, d=9, sigmaColor=strength * 10, sigmaSpace=strength * 10)

    def preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """
        Prepare image for OCR: grayscale → contrast enhancement → slight denoise.
        Returns a clean grayscale image optimized for text extraction.
        """
        gray = self.to_grayscale(img)
        enhanced = self.enhance_contrast(gray)
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)
        return denoised

    def preprocess_for_detection(self, img: np.ndarray) -> np.ndarray:
        """
        Prepare image for UI element detection: grayscale → blur → adaptive threshold.
        Returns a binary image.
        """
        gray = self.to_grayscale(img)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        return thresh

    def extract_region(self, img: np.ndarray, x: int, y: int, w: int, h: int) -> Optional[np.ndarray]:
        """Extract a sub-region from the image. Returns None if coordinates are invalid."""
        ih, iw = img.shape[:2]
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(iw, x + w)
        y2 = min(ih, y + h)
        if x2 <= x1 or y2 <= y1:
            return None
        return img[y1:y2, x1:x2]

    def map_to_original(self, x: float, y: float, w: float, h: float) -> Tuple[float, float, float, float]:
        """Map processed-image coordinates back to original image coordinates."""
        return (
            round(x * self.scale_x, 1),
            round(y * self.scale_y, 1),
            round(w * self.scale_x, 1),
            round(h * self.scale_y, 1),
        )

    def get_image_dimensions(self, img: np.ndarray) -> Tuple[int, int]:
        """Return (width, height) of an image."""
        h, w = img.shape[:2]
        return (w, h)
