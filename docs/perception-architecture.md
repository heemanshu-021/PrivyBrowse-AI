# Perception Pipeline Architecture

## 1. Modular Architecture Overview

The perception pipeline is organized into modular packages located under `backend/perception/`:

```
backend/perception/
├── core/
│   ├── schemas.py            # Strongly typed Pydantic models (BoundingBox, PerceivedElement, PerceptionResult)
│   ├── coordinator.py        # Coordinate conversions (Screenshot ↔ Viewport ↔ Document)
│   └── pipeline.py          # Master perception pipeline orchestrator
├── preprocessing/
│   └── image_processor.py    # CLAHE contrast, grayscale, adaptive resize, and bilinear filtering
├── ocr/
│   ├── base.py               # Abstract BaseOCREngine interface
│   └── tesseract_engine.py   # Tesseract OCR implementation with fallback detection
├── detectors/
│   ├── dom_detector.py       # Browser DOM / accessibility element detector
│   ├── visual_detector.py    # OpenCV contour, aspect ratio, and Canny edge detector
│   └── text_detector.py      # OCR / DOM text region detector
├── fusion/
│   ├── iou_matcher.py        # Geometric IoU cross-matching
│   ├── confidence.py         # Multi-source weighted confidence scoring
│   └── context_fuser.py      # Unified context fuser and stable ID assigner
└── utils/
    └── geometry.py           # IoU, NMS, containment, and bounding box merge utilities
```

---

## 2. Pipeline Execution Flow

```
+-----------------------------------------------------------------------------------+
| 1. OBSERVATION INPUT                                                              |
|   - Viewport Screenshot (Base64 / Bytes)                                          |
|   - DOM Accessibility Elements ([x1, y1, x2, y2], tag, attributes)                |
|   - Viewport Metadata (Width, Height, DevicePixelRatio, ScrollOffset)              |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 2. IMAGE PREPROCESSING (image_processor.py)                                       |
|   - Decode PNG/JPEG stream                                                        |
|   - Adaptive aspect-preserving resize (Max dimension 1920px)                      |
|   - CLAHE contrast enhancement & bilateral edge-preserving smoothing             |
+-----------------------------------------------------------------------------------+
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
+---------------------------------------+ +---------------------------------------+
| 3A. VISUAL CONTOUR DETECTION          | | 3B. OCR TEXT EXTRACTION               |
|  - Adaptive thresholding (dark/light) |  - Tesseract OCR (Local model)          |
|  - Morphological closing (merge gaps) |  - Group word boxes into line regions   |
|  - Contour hierarchy & Canny edges    |  - Fallback: DOM Text Proxy             |
|  - Aspect ratio heuristic typing      |                                         |
+---------------------------------------+ +---------------------------------------+
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 4. DOM ELEMENT MAPPING & VISIBILITY CLASSIFICATION (dom_detector.py)              |
|   - Parse tag names, input types, and aria labels                                 |
|   - Map raw coordinates to viewport coordinate space                              |
|   - Classify visibility: VISIBLE, PARTIALLY_VISIBLE, OFFSCREEN                    |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 5. MULTI-SOURCE CONTEXT FUSION (context_fuser.py)                                 |
|   - IoU overlap matching (Threshold = 0.35)                                       |
|   - DOM anchor matching with visual contour confirmation                          |
|   - Semantic type resolution (BUTTON, INPUT, LINK, SELECT, etc.)                  |
|   - Text / label resolution (DOM text > OCR text > placeholder > ariaLabel)       |
|   - Non-maximum suppression for orphan visual elements                            |
|   - Assign deterministic stable IDs: pb-element-001, pb-element-002...            |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 6. MULTI-SOURCE CONFIDENCE SCORING (confidence.py)                                |
|   - Confidence = 0.35*DOM + 0.30*OCR + 0.25*VISION + 0.10*GEOMETRY                |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 7. STRUCTURED AGENT-READY OUTPUT (PerceptionResult)                               |
|   - Elements array with bounding boxes, types, labels, and sources                |
|   - Summary metrics (interactive count, text regions, latency breakdown)          |
|   - Handed off to downstream PII Redaction & Action Planning layers               |
+-----------------------------------------------------------------------------------+
```
