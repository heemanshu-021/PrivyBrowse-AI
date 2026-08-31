"""
PrivyBrowse AI — Tesseract OCR Engine
Real on-device OCR via pytesseract. Falls back gracefully when Tesseract
binary is not installed (the pipeline switches to DOM-text-proxy mode).

Model Info:
  Engine: Tesseract OCR (Apache 2.0 license)
  Model size: ~30 MB (eng.traineddata)
  Runtime: Local binary process, no network required
  Install: `brew install tesseract` (macOS) or `apt install tesseract-ocr` (Linux)
"""

import numpy as np
from typing import List, Dict, Any
from backend.perception.ocr.base import BaseOCREngine, OCRResult

# Try importing pytesseract — it may be installed even if the system binary isn't
_PYTESSERACT_AVAILABLE = False
_TESSERACT_BINARY_OK = False

try:
    import pytesseract
    from PIL import Image
    _PYTESSERACT_AVAILABLE = True

    # Probe the binary
    try:
        pytesseract.get_tesseract_version()
        _TESSERACT_BINARY_OK = True
    except Exception:
        _TESSERACT_BINARY_OK = False
except ImportError:
    _PYTESSERACT_AVAILABLE = False


import hashlib
from collections import OrderedDict

class TesseractOCREngine(BaseOCREngine):
    """
    Real Tesseract-based OCR engine with LRU crop caching and deduplication.
    Extracts text from images with per-word bounding boxes and confidence scores.
    """

    def __init__(self, max_cache_entries: int = 50):
        self._available = _PYTESSERACT_AVAILABLE and _TESSERACT_BINARY_OK
        self._ocr_cache: OrderedDict[str, List[OCRResult]] = OrderedDict()
        self._max_cache = max_cache_entries

    def clear_cache(self):
        """Invalidates all cached OCR results."""
        self._ocr_cache.clear()

    def is_available(self) -> bool:
        return self._available

    def get_engine_name(self) -> str:
        return "TESSERACT"

    def get_model_info(self) -> Dict[str, Any]:
        info = {
            "engine": "Tesseract OCR",
            "available": self._available,
            "pytesseract_installed": _PYTESSERACT_AVAILABLE,
            "binary_found": _TESSERACT_BINARY_OK,
            "model_size_mb": 30,
            "offline": True,
            "license": "Apache-2.0",
            "cache_size": len(self._ocr_cache)
        }
        if self._available:
            try:
                info["version"] = str(pytesseract.get_tesseract_version())
            except Exception:
                info["version"] = "unknown"
        return info

    def extract_text(self, image: np.ndarray) -> List[OCRResult]:
        """
        Run Tesseract OCR on the given image with hash-based LRU memoization.
        Returns word-level text boxes with confidence scores.
        """
        if image is None or image.size == 0:
            return []

        # 1. Compute fast structural hash of image
        try:
            img_hash = hashlib.md5(image.tobytes()[:32768]).hexdigest() + f"_{image.shape}"
            if img_hash in self._ocr_cache:
                self._ocr_cache.move_to_end(img_hash)
                return [OCRResult(**r.model_dump()) for r in self._ocr_cache[img_hash]]
        except Exception:
            img_hash = None

        if not self._available:
            if img_hash is not None:
                self._ocr_cache[img_hash] = []
            return []

        try:
            # Convert numpy array to PIL Image
            if len(image.shape) == 2:
                pil_img = Image.fromarray(image)
            else:
                from cv2 import cvtColor, COLOR_BGR2RGB
                pil_img = Image.fromarray(cvtColor(image, COLOR_BGR2RGB))

            # Get per-word data with bounding boxes and confidence
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)

            results: List[OCRResult] = []
            n_boxes = len(data["text"])

            # Group words into lines by (block_num, par_num, line_num)
            lines: Dict[tuple, List[int]] = {}
            for i in range(n_boxes):
                text = data["text"][i].strip()
                conf = int(data["conf"][i])
                if not text or conf < 0:
                    continue
                key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
                if key not in lines:
                    lines[key] = []
                lines[key].append(i)

            # Emit one OCRResult per text line (not per character)
            for key, indices in lines.items():
                words = []
                confs = []
                min_x, min_y = float("inf"), float("inf")
                max_x, max_y = 0.0, 0.0

                for i in indices:
                    words.append(data["text"][i].strip())
                    confs.append(max(0, int(data["conf"][i])))
                    x = data["left"][i]
                    y = data["top"][i]
                    w = data["width"][i]
                    h = data["height"][i]
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x + w)
                    max_y = max(max_y, y + h)

                line_text = " ".join(words)
                avg_conf = sum(confs) / len(confs) / 100.0 if confs else 0.0

                if not line_text.strip():
                    continue

                results.append(OCRResult(
                    text=line_text,
                    confidence=round(avg_conf, 3),
                    bbox=[min_x, min_y, max_x, max_y],
                    source="TESSERACT",
                ))

            if img_hash is not None:
                self._ocr_cache[img_hash] = results
                if len(self._ocr_cache) > self._max_cache:
                    self._ocr_cache.popitem(last=False)

            return results

        except Exception:
            return []
