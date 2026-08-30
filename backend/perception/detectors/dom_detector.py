"""
PrivyBrowse AI — DOM Element Detector
Extracts structured elements from browser DOM / accessibility metadata.
"""

from typing import List, Dict, Any
from backend.perception.core.schemas import BoundingBox, PerceivedElement


# Tag → semantic type mapping
TAG_TYPE_MAP = {
    "BUTTON": "BUTTON",
    "A": "LINK",
    "INPUT": "INPUT",
    "TEXTAREA": "TEXTAREA",
    "SELECT": "SELECT",
    "IMG": "IMAGE",
    "H1": "HEADING", "H2": "HEADING", "H3": "HEADING",
    "H4": "HEADING", "H5": "HEADING", "H6": "HEADING",
    "NAV": "NAV",
    "FORM": "FORM",
    "LABEL": "TEXT",
    "P": "TEXT",
    "SPAN": "TEXT",
    "B": "TEXT",
    "STRONG": "TEXT",
    "I": "TEXT",
    "EM": "TEXT",
    "DIV": "ELEMENT",
    "HEADER": "ELEMENT",
    "SECTION": "ELEMENT",
}

INPUT_TYPE_OVERRIDES = {
    "submit": "BUTTON",
    "button": "BUTTON",
    "checkbox": "CHECKBOX",
    "radio": "RADIO",
    "image": "IMAGE",
}

INTERACTIVE_TYPES = {"BUTTON", "LINK", "INPUT", "TEXTAREA", "CHECKBOX", "RADIO", "SELECT"}


class DOMDetector:
    """
    Extracts perception elements from DOM nodes provided by the browser extension.
    Each DOM node with a valid bounding box becomes a PerceivedElement with source=DOM.
    """

    def detect(self, dom_nodes: List[Dict[str, Any]]) -> List[PerceivedElement]:
        """
        Process a list of DOM node dicts and return PerceivedElement objects.
        Supports both Chrome extension format (dict bboxes, tag, ariaLabel)
        and API format (list bboxes, tag_name, aria_label).
        """
        elements: List[PerceivedElement] = []

        for node in dom_nodes:
            if not isinstance(node, dict):
                continue

            bbox_raw = node.get("bbox")
            if not bbox_raw:
                continue

            bbox = None
            # 1. Parse bbox from [x1, y1, x2, y2] format
            if isinstance(bbox_raw, list) and len(bbox_raw) >= 4:
                x1, y1, x2, y2 = float(bbox_raw[0]), float(bbox_raw[1]), float(bbox_raw[2]), float(bbox_raw[3])
                w = x2 - x1
                h = y2 - y1
                if w > 0 and h > 0:
                    bbox = BoundingBox(x=x1, y=y1, width=w, height=h)
            # 2. Parse bbox from dict format: {x, y, width, height} or {left, top, right, bottom}
            elif isinstance(bbox_raw, dict):
                x = float(bbox_raw.get("x", bbox_raw.get("left", 0)))
                y = float(bbox_raw.get("y", bbox_raw.get("top", 0)))
                w = float(bbox_raw.get("width", 0))
                h = float(bbox_raw.get("height", 0))
                if w <= 0 and "right" in bbox_raw:
                    w = float(bbox_raw["right"]) - x
                if h <= 0 and "bottom" in bbox_raw:
                    h = float(bbox_raw["bottom"]) - y
                if w > 0 and h > 0:
                    bbox = BoundingBox(x=x, y=y, width=w, height=h)

            if bbox is None:
                continue

            # Tag resolution with aliases
            raw_tag = node.get("tag_name") or node.get("tag") or node.get("tagName") or ""
            tag_name = str(raw_tag).upper()

            # Type resolution with aliases
            raw_type = node.get("inputType") or node.get("type") or ""
            input_type = str(raw_type).lower()

            # Determine element type
            el_type = node.get("type", "").upper() if node.get("type") and node.get("type").upper() in TAG_TYPE_MAP.values() else TAG_TYPE_MAP.get(tag_name, "ELEMENT")
            if tag_name == "INPUT" and input_type in INPUT_TYPE_OVERRIDES:
                el_type = INPUT_TYPE_OVERRIDES[input_type]
            elif node.get("role"):
                role_upper = str(node.get("role")).upper()
                if role_upper in TAG_TYPE_MAP:
                    el_type = TAG_TYPE_MAP[role_upper]

            # Resolve label
            text = str(node.get("text", "")).strip()
            value = str(node.get("value", "")).strip()
            placeholder = str(node.get("placeholder", "")).strip()
            aria_label = str(node.get("aria_label") or node.get("ariaLabel") or node.get("aria-label") or "").strip()
            label = text or aria_label or placeholder or value

            # Determine interactivity
            interactive = el_type in INTERACTIVE_TYPES

            # Visibility & enabled state
            visible = bool(node.get("visible", True))
            enabled = bool(node.get("enabled", True))
            visibility_str = str(node.get("visibility", "VISIBLE")).upper()

            elements.append(PerceivedElement(
                id=str(node.get("id", "")),
                type=el_type,
                label=label,
                text=text,
                bbox=bbox,
                confidence=0.92,  # DOM elements have high structural confidence
                visible=visible,
                enabled=enabled,
                interactive=interactive,
                sources=["DOM"],
                attributes={
                    "tag_name": tag_name,
                    "type": input_type,
                    "placeholder": placeholder,
                    "id_attr": str(node.get("id_attr") or node.get("id") or ""),
                    "class_attr": str(node.get("class_attr") or node.get("className") or node.get("class") or ""),
                    "name": str(node.get("name", "")),
                    "value": value,
                    "selector": str(node.get("selector", "")),
                    "role": str(node.get("role", "")),
                },
                visibility=visibility_str if visibility_str in {"VISIBLE", "HIDDEN", "PARTIALLY_VISIBLE", "OFFSCREEN", "OBSCURED"} else "VISIBLE",
            ))

        return elements
