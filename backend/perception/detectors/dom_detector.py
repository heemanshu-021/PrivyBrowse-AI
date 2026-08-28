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
    "DIV": "ELEMENT",
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
        Expected node format: { id, tag_name, type, text, value, placeholder, bbox, ... }
        """
        elements: List[PerceivedElement] = []

        for node in dom_nodes:
            bbox_raw = node.get("bbox")
            if not bbox_raw:
                continue

            # Parse bbox from [x1, y1, x2, y2] format
            if isinstance(bbox_raw, list) and len(bbox_raw) >= 4:
                x1, y1, x2, y2 = bbox_raw[0], bbox_raw[1], bbox_raw[2], bbox_raw[3]
                w = x2 - x1
                h = y2 - y1
                if w <= 0 or h <= 0:
                    continue
                bbox = BoundingBox(x=x1, y=y1, width=w, height=h)
            else:
                continue

            tag_name = node.get("tag_name", "").upper()
            input_type = node.get("type", "").lower()

            # Determine element type
            el_type = TAG_TYPE_MAP.get(tag_name, "ELEMENT")
            if tag_name == "INPUT" and input_type in INPUT_TYPE_OVERRIDES:
                el_type = INPUT_TYPE_OVERRIDES[input_type]

            # Resolve label
            text = node.get("text", "").strip()
            value = node.get("value", "").strip()
            placeholder = node.get("placeholder", "").strip()
            aria_label = node.get("aria_label", "").strip() or node.get("ariaLabel", "").strip()
            label = text or aria_label or placeholder or value

            # Determine interactivity
            interactive = el_type in INTERACTIVE_TYPES

            # Determine visibility (basic: trust DOM presence as visible since extension filters)
            visible = True
            enabled = True

            elements.append(PerceivedElement(
                id=node.get("id", ""),
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
                    "id_attr": node.get("id_attr", ""),
                    "class_attr": node.get("class_attr", ""),
                    "name": node.get("name", ""),
                    "value": value,
                },
                visibility="VISIBLE",
            ))

        return elements
