# Perception Schema & Coordinate System Specification

## 1. Element Schema (`PerceivedElement`)

Each perceived webpage element conforms to the following schema:

```json
{
  "id": "pb-element-001",
  "type": "BUTTON",
  "label": "Sign In",
  "text": "Sign In",
  "bbox": {
    "x": 40.0,
    "y": 255.0,
    "width": 240.0,
    "height": 40.0,
    "top": 255.0,
    "left": 40.0,
    "right": 280.0,
    "bottom": 295.0
  },
  "confidence": 0.952,
  "visible": true,
  "enabled": true,
  "interactive": true,
  "sources": [
    "DOM",
    "VISION",
    "OCR"
  ],
  "attributes": {
    "tag_name": "BUTTON",
    "type": "submit",
    "placeholder": "",
    "id_attr": "btn-signin",
    "class_attr": "btn btn-primary"
  },
  "visibility": "VISIBLE"
}
```

---

## 2. Supported Element Classifications

| Type | Description | Interactive |
| :--- | :--- | :--- |
| `BUTTON` | Standard `<button>`, `<input type="submit">`, or clickable visual rectangular buttons | Yes |
| `INPUT` | Text fields, email inputs, number fields, search boxes | Yes |
| `TEXTAREA` | Multi-line text entry controls | Yes |
| `CHECKBOX` | Toggleable checkbox controls | Yes |
| `RADIO` | Single-selection radio buttons | Yes |
| `SELECT` | Dropdown select controls | Yes |
| `LINK` | Anchor hyperlinks (`<a>`) or navigational items | Yes |
| `IMAGE` | `<img>` elements or detected visual image contours | No |
| `HEADING` | `<h1>` through `<h6>` tags or prominent header text regions | No |
| `TEXT` | Static text paragraphs, labels, or spans | No |
| `NAV` | Navigation bar containers | No |
| `FORM` | Form containers grouping interactive inputs | No |
| `CARD` | Card/panel visual container components | No |
| `ICON` | Small visual iconography or glyphs | No |
| `ELEMENT` | Generic structural container elements | No |

---

## 3. Multi-Source Confidence Scoring Formula

Confidence represents the composite probability that the detected element is a genuine, actionable UI component:

$$\text{Confidence} = 0.35 \times \text{DOM} + 0.30 \times \text{OCR} + 0.25 \times \text{VISION} + 0.10 \times \text{GEOMETRY}$$

Where:
* **$\text{DOM}$**: $0.92$ if matched from DOM accessibility tree with valid layout coordinates; $0.0$ if vision-only.
* **$\text{OCR}$**: Scaled by OCR engine confidence ($0.50$ to $1.00$) if text content matches the element bbox; $0.0$ if no text.
* **$\text{VISION}$**: OpenCV contour classifier confidence ($0.60$ to $0.90$), adjusted by local Canny edge density.
* **$\text{GEOMETRY}$**: $0.95$ if $\text{IoU} \ge 0.60$; $0.75$ if $\text{IoU} \ge 0.40$; $0.50$ if $\text{IoU} \ge 0.20$; $0.30$ otherwise.

---

## 4. Coordinate System & Normalization

All bounding boxes output by the perception pipeline are normalized to **Viewport CSS Pixels**:

$$\text{Viewport } X = \text{Screenshot } X \times \left( \frac{\text{Viewport Width}}{\text{Screenshot Width}} \right)$$
$$\text{Viewport } Y = \text{Screenshot } Y \times \left( \frac{\text{Viewport Height}}{\text{Screenshot Height}} \right)$$

This ensures that actions dispatched by the agent (e.g. mouse clicks or keystrokes) align with the browser's physical DOM rendering coordinates, irrespective of device pixel ratios (Retina Displays @ 2x/3x) or window scaling.
