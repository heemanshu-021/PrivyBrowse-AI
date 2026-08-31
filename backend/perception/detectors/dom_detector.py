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
    "OPTION": "OPTION",
    "IMG": "IMAGE",
    "DIALOG": "DIALOG",
    "FORM": "FORM",
    "NAV": "NAV",
    "LABEL": "TEXT",
    "P": "TEXT",
    "SPAN": "TEXT",
    "H1": "HEADING", "H2": "HEADING", "H3": "HEADING",
    "H4": "HEADING", "H5": "HEADING", "H6": "HEADING",
    "B": "TEXT", "STRONG": "TEXT", "I": "TEXT", "EM": "TEXT",
    "DIV": "ELEMENT", "HEADER": "ELEMENT", "SECTION": "ELEMENT",
    "ARTICLE": "ELEMENT", "MAIN": "ELEMENT", "ASIDE": "ELEMENT"
}

ROLE_TYPE_MAP = {
    "BUTTON": "BUTTON",
    "LINK": "LINK",
    "TEXTBOX": "INPUT",
    "SEARCHBOX": "INPUT",
    "CHECKBOX": "CHECKBOX",
    "RADIO": "RADIO",
    "SWITCH": "CHECKBOX",
    "COMBOBOX": "SELECT",
    "LISTBOX": "SELECT",
    "OPTION": "OPTION",
    "TAB": "TAB",
    "TABPANEL": "ELEMENT",
    "MENU": "MENU",
    "MENUITEM": "BUTTON",
    "DIALOG": "DIALOG",
    "ALERTDIALOG": "DIALOG",
    "ALERT": "ALERT",
    "BANNER": "BANNER",
}

INPUT_TYPE_OVERRIDES = {
    "submit": "BUTTON",
    "button": "BUTTON",
    "reset": "BUTTON",
    "checkbox": "CHECKBOX",
    "radio": "RADIO",
    "image": "IMAGE",
    "select-one": "SELECT",
    "select-multiple": "SELECT",
}

INTERACTIVE_TYPES = {"BUTTON", "LINK", "INPUT", "TEXTAREA", "CHECKBOX", "RADIO", "SELECT", "OPTION", "TAB", "MENU", "DIALOG"}


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

            bbox_raw = node.get("bbox") or node.get("boundingBox") or node.get("rect")
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

            # Role resolution
            raw_role = str(node.get("role", "")).upper()

            # Determine element type
            if node.get("type") and str(node.get("type")).upper() in INTERACTIVE_TYPES:
                el_type = str(node.get("type")).upper()
            elif raw_role in ROLE_TYPE_MAP:
                el_type = ROLE_TYPE_MAP[raw_role]
            elif tag_name == "INPUT" and input_type in INPUT_TYPE_OVERRIDES:
                el_type = INPUT_TYPE_OVERRIDES[input_type]
            else:
                el_type = TAG_TYPE_MAP.get(tag_name, "ELEMENT")

            # Check for modal / cookie banner classification from classes or IDs
            class_str = str(node.get("class_attr") or node.get("className") or node.get("class") or "").lower()
            id_str = str(node.get("id_attr") or node.get("id") or "").lower()
            if "cookie" in class_str or "cookie" in id_str or "consent" in class_str:
                el_type = "COOKIE_BANNER" if el_type in ("ELEMENT", "DIALOG") else el_type
            elif "modal" in class_str or "dialog" in class_str or node.get("aria-modal") is True:
                el_type = "DIALOG" if el_type == "ELEMENT" else el_type

            # Resolve label & accessibility names
            text = str(node.get("text", "")).strip()
            value = str(node.get("value", "")).strip()
            placeholder = str(node.get("placeholder", "")).strip()
            aria_label = str(node.get("aria_label") or node.get("ariaLabel") or node.get("aria-label") or "").strip()
            aria_labelledby = str(node.get("aria_labelledby") or node.get("ariaLabelledBy") or node.get("aria-labelledby") or "").strip()
            form_label = str(node.get("form_label") or node.get("formLabel") or "").strip()
            label = aria_label or form_label or aria_labelledby or text or placeholder or value

            # State properties
            checked = bool(node.get("checked", False)) or str(node.get("aria-checked", "")).lower() == "true"
            selected = bool(node.get("selected", False))
            disabled = bool(node.get("disabled", False)) or str(node.get("aria-disabled", "")).lower() == "true"
            readonly = bool(node.get("readonly", False))
            in_shadow = bool(node.get("in_shadow_dom", False) or node.get("inShadowDom", False))

            # Determine interactivity
            interactive = el_type in INTERACTIVE_TYPES and not disabled

            # Visibility & enabled state
            visible = bool(node.get("visible", True))
            enabled = not disabled
            visibility_str = str(node.get("visibility", "VISIBLE")).upper()

            elements.append(PerceivedElement(
                id=str(node.get("id", "")),
                type=el_type,
                label=label,
                text=text,
                bbox=bbox,
                confidence=0.94 if in_shadow else 0.92,
                visible=visible,
                enabled=enabled,
                interactive=interactive,
                sources=["DOM"],
                attributes={
                    "tag_name": tag_name,
                    "type": input_type,
                    "placeholder": placeholder,
                    "id_attr": id_str,
                    "class_attr": class_str,
                    "name": str(node.get("name", "")),
                    "value": value,
                    "selector": str(node.get("selector", "")),
                    "role": raw_role,
                    "aria_label": aria_label,
                    "aria_labelledby": aria_labelledby,
                    "form_label": form_label,
                    "checked": checked,
                    "selected": selected,
                    "disabled": disabled,
                    "readonly": readonly,
                    "in_shadow_dom": in_shadow,
                    "options": node.get("options", []),
                    "href": str(node.get("href", "")),
                },
                visibility=visibility_str if visibility_str in {"VISIBLE", "HIDDEN", "PARTIALLY_VISIBLE", "OFFSCREEN", "OBSCURED"} else "VISIBLE",
            ))

        return elements
