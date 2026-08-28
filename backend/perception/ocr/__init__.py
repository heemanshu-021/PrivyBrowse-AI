# OCR subpackage
from backend.perception.ocr.base import BaseOCREngine, OCRResult
from backend.perception.ocr.tesseract_engine import TesseractOCREngine

__all__ = ["BaseOCREngine", "OCRResult", "TesseractOCREngine"]
