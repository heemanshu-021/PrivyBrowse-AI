"""
PrivyBrowse AI — Perception Pipeline
Main orchestrator that chains all perception stages:
  Preprocessing → OCR → Visual Detection → DOM Detection → Text Detection → Fusion → Output

Measures real latency per stage using time.perf_counter().
"""

import time
import base64
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import cv2
import numpy as np

from backend.perception.core.schemas import (
    PerceivedElement, PerceptionResult, PerceptionLatency,
    PerceptionSummary, PageRepresentation, CoordinateSystem,
    BoundingBox,
)
from backend.perception.core.coordinator import CoordinateConverter
from backend.perception.preprocessing.image_processor import ImageProcessor
from backend.perception.ocr.tesseract_engine import TesseractOCREngine
from backend.perception.detectors.visual_detector import VisualDetector
from backend.perception.detectors.dom_detector import DOMDetector
from backend.perception.detectors.text_detector import TextDetector
from backend.perception.fusion.context_fuser import ContextFuser
from backend.observability.publisher import global_event_publisher


class PerceptionPipeline:
    """
    Modular on-device visual perception pipeline.

    Input:
      - screenshot (base64 or raw bytes)
      - viewport dimensions
      - device pixel ratio
      - DOM elements (optional)
      - page metadata (optional)

    Output:
      - PerceptionResult with fused elements, latency breakdown, and page representation.
    """

    def __init__(self):
        self.preprocessor = ImageProcessor()
        self.ocr_engine = TesseractOCREngine()
        self.visual_detector = VisualDetector()
        self.dom_detector = DOMDetector()
        self.text_detector = TextDetector()
        self.fuser = ContextFuser(iou_threshold=0.35)

    def get_status(self) -> Dict[str, Any]:
        """Return engine readiness status."""
        ocr_info = self.ocr_engine.get_model_info()
        return {
            "pipeline_ready": True,
            "ocr_engine": ocr_info.get("engine", "unknown"),
            "ocr_available": ocr_info.get("available", False),
            "ocr_model_size_mb": ocr_info.get("model_size_mb", 0),
            "visual_detector": "OpenCV Contour + Morphological",
            "visual_detector_ready": True,
            "dom_detector_ready": True,
            "fusion_engine": "IoU Multi-Source Weighted Fusion",
            "offline_capable": True,
            "privacy_mode": "LOCAL_ONLY",
        }

    def run(
        self,
        screenshot_b64: str = "",
        screenshot_bytes: Optional[bytes] = None,
        viewport_width: int = 0,
        viewport_height: int = 0,
        device_pixel_ratio: float = 1.0,
        dom_nodes: Optional[List[Dict[str, Any]]] = None,
        page_metadata: Optional[Dict[str, Any]] = None,
        scroll_x: float = 0.0,
        scroll_y: float = 0.0,
        document_width: float = 0.0,
        document_height: float = 0.0,
    ) -> PerceptionResult:
        """
        Run the complete perception pipeline.

        Args:
            screenshot_b64: Base64-encoded screenshot (data URL or raw base64)
            screenshot_bytes: Raw screenshot bytes (alternative to b64)
            viewport_width: Browser viewport width in CSS pixels
            viewport_height: Browser viewport height in CSS pixels
            device_pixel_ratio: Device pixel ratio
            dom_nodes: List of DOM node dicts from the browser extension
            page_metadata: Page info (url, title, hostname)
            scroll_x, scroll_y: Current scroll position
            document_width, document_height: Full document dimensions

        Returns:
            PerceptionResult with all fused elements and metadata.
        """
        latency = PerceptionLatency()
        warnings: List[str] = []
        t_total_start = time.perf_counter()

        # === STAGE 0: Decode screenshot ===
        if screenshot_bytes is None and screenshot_b64:
            try:
                raw = screenshot_b64
                if "," in raw:
                    raw = raw.split(",", 1)[1]
                screenshot_bytes = base64.b64decode(raw)
            except Exception as e:
                return self._error_result(
                    "INVALID_SCREENSHOT",
                    f"Failed to decode base64 screenshot: {e}"
                )

        if screenshot_bytes is None or len(screenshot_bytes) == 0:
            return self._error_result(
                "EMPTY_SCREENSHOT",
                "No screenshot data provided."
            )

        # === STAGE 1: Preprocessing ===
        t_pre_start = time.perf_counter()
        img = self.preprocessor.decode(screenshot_bytes)
        if img is None:
            return self._error_result(
                "INVALID_IMAGE",
                "Failed to decode image bytes. Unsupported format."
            )

        screenshot_h, screenshot_w = img.shape[:2]

        # Adaptive resize if very large
        img = self.preprocessor.adaptive_resize(img, max_dimension=1920)

        latency.preprocessing_ms = round((time.perf_counter() - t_pre_start) * 1000, 2)

        # === Set up coordinate converter ===
        effective_vw = viewport_width if viewport_width > 0 else screenshot_w
        effective_vh = viewport_height if viewport_height > 0 else screenshot_h

        coord_converter = CoordinateConverter(
            viewport_width=effective_vw,
            viewport_height=effective_vh,
            screenshot_width=screenshot_w,
            screenshot_height=screenshot_h,
            device_pixel_ratio=device_pixel_ratio,
            scroll_x=scroll_x,
            scroll_y=scroll_y,
            document_width=document_width,
            document_height=document_height,
        )

        # === STAGE 2: OCR ===
        t_ocr_start = time.perf_counter()
        ocr_results = []
        ocr_engine_name = "UNAVAILABLE"

        if self.ocr_engine.is_available():
            ocr_image = self.preprocessor.preprocess_for_ocr(img)
            ocr_results = self.ocr_engine.extract_text(ocr_image)
            ocr_engine_name = self.ocr_engine.get_engine_name()
        else:
            warnings.append(
                "Tesseract OCR binary not found. Using DOM text proxy. "
                "Install Tesseract for real visual OCR: brew install tesseract (macOS) "
                "or apt install tesseract-ocr (Linux)."
            )
            ocr_engine_name = "DOM_TEXT_PROXY"

        latency.ocr_ms = round((time.perf_counter() - t_ocr_start) * 1000, 2)

        # === STAGE 3: Visual Detection ===
        t_vis_start = time.perf_counter()
        vision_elements = self.visual_detector.detect(img)

        # Convert vision bboxes from screenshot coords to viewport coords
        for vel in vision_elements:
            vel.bbox = coord_converter.screenshot_to_viewport(vel.bbox)
            vel.visibility = coord_converter.classify_visibility(vel.bbox)

        latency.visual_detection_ms = round((time.perf_counter() - t_vis_start) * 1000, 2)

        # === STAGE 4: DOM Detection ===
        t_dom_start = time.perf_counter()
        dom_elements = []
        if dom_nodes:
            dom_elements = self.dom_detector.detect(dom_nodes)
            # Classify visibility
            for del_ in dom_elements:
                del_.visibility = coord_converter.classify_visibility(del_.bbox)

        latency.dom_detection_ms = round((time.perf_counter() - t_dom_start) * 1000, 2)

        # === STAGE 5: Text Detection ===
        t_txt_start = time.perf_counter()
        text_elements = []

        if ocr_results:
            # Convert OCR bboxes from screenshot coords to viewport coords
            for ocr_r in ocr_results:
                ss_bbox = BoundingBox.from_xyxy(*ocr_r.bbox[:4])
                vp_bbox = coord_converter.screenshot_to_viewport(ss_bbox)
                ocr_r.bbox = vp_bbox.to_xyxy()

            text_elements = self.text_detector.detect_from_ocr(ocr_results)
        elif dom_nodes:
            # Fallback to DOM text proxy
            text_elements = self.text_detector.detect_from_dom_text(dom_nodes)

        latency.text_detection_ms = round((time.perf_counter() - t_txt_start) * 1000, 2)

        # === STAGE 6: Fusion ===
        t_fuse_start = time.perf_counter()
        fused_elements = self.fuser.fuse(dom_elements, vision_elements, text_elements)
        latency.fusion_ms = round((time.perf_counter() - t_fuse_start) * 1000, 2)

        # === Total ===
        latency.total_ms = round((time.perf_counter() - t_total_start) * 1000, 2)

        # === Build summary ===
        summary = PerceptionSummary(
            element_count=len(fused_elements),
            interactive_count=sum(1 for e in fused_elements if e.interactive),
            text_regions=sum(1 for e in fused_elements if e.type in ("TEXT", "HEADING")),
            buttons=sum(1 for e in fused_elements if e.type == "BUTTON"),
            inputs=sum(1 for e in fused_elements if e.type == "INPUT"),
            links=sum(1 for e in fused_elements if e.type == "LINK"),
            images=sum(1 for e in fused_elements if e.type == "IMAGE"),
            headings=sum(1 for e in fused_elements if e.type == "HEADING"),
            sources_used=self._collect_sources(fused_elements),
            ocr_engine=ocr_engine_name,
            privacy_status="LOCAL_UNSANITIZED",
        )

        # === Build page representation ===
        page = PageRepresentation(
            title=(page_metadata or {}).get("title", ""),
            url=(page_metadata or {}).get("url", ""),
            hostname=(page_metadata or {}).get("hostname", ""),
            viewport={"width": effective_vw, "height": effective_vh},
            scroll_position={"x": scroll_x, "y": scroll_y},
            document_dimensions={"width": document_width, "height": document_height},
        )

        global_event_publisher.perception_completed(
            element_count=len(fused_elements),
            duration_ms=latency.total_ms,
            ocr_count=len(ocr_results),
            cv_count=len(vision_elements)
        )

        return PerceptionResult(
            success=True,
            page=page,
            elements=fused_elements,
            summary=summary,
            latency=latency,
            coordinate_system=coord_converter.get_coordinate_system(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
            warnings=warnings,
        )

    def _error_result(self, code: str, message: str) -> PerceptionResult:
        """Build an error PerceptionResult."""
        return PerceptionResult(
            success=False,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error={"code": code, "message": message},
        )

    def _collect_sources(self, elements: List[PerceivedElement]) -> List[str]:
        """Collect unique detection sources across all fused elements."""
        sources = set()
        for el in elements:
            sources.update(el.sources)
        return sorted(sources)
