# Browser Data Flow & Unified Context Schemas

## 1. Unified Browser Context Schema (`BrowserContext`)

Transmitted via `POST /api/browser/context` from the Chrome Extension to the local engine:

```json
{
  "page": {
    "url": "https://example.com/login",
    "hostname": "example.com",
    "title": "Secure Login Portal",
    "viewport": {
      "width": 1280,
      "height": 720
    },
    "devicePixelRatio": 2.0,
    "timestamp": "2026-08-28T08:40:00Z"
  },
  "screenshot": {
    "available": true,
    "dataUrl": "data:image/png;base64,iVBORw0KGgo...",
    "timestamp": "2026-08-28T08:40:00Z"
  },
  "elements": [
    {
      "id": "pb-element-001",
      "type": "input",
      "tag": "input",
      "text": "[SENSITIVE FIELD]",
      "ariaLabel": "Account Password",
      "placeholder": "Enter password",
      "role": "textbox",
      "name": "password",
      "inputType": "password",
      "sensitive": true,
      "bbox": {
        "x": 420,
        "y": 280,
        "width": 340,
        "height": 42,
        "top": 280,
        "left": 420,
        "right": 760,
        "bottom": 322
      },
      "visible": true,
      "enabled": true
    },
    {
      "id": "pb-element-002",
      "type": "button",
      "tag": "button",
      "text": "Sign In",
      "ariaLabel": null,
      "placeholder": null,
      "role": "button",
      "name": null,
      "inputType": "submit",
      "bbox": {
        "x": 420,
        "y": 340,
        "width": 340,
        "height": 44,
        "top": 340,
        "left": 420,
        "right": 760,
        "bottom": 384
      },
      "visible": true,
      "enabled": true
    }
  ],
  "capture": {
    "timestamp": "2026-08-28T08:40:00Z",
    "source": "chrome-extension",
    "elementCount": 2
  }
}
```

---

## 2. Agent Action Request Schema (`AgentActionRequest`)

Dispatched to the Content Script to actuate the browser:

```json
{
  "action": "CLICK",
  "target": {
    "elementId": "pb-element-002",
    "selector": "#btn-login",
    "x": 590,
    "y": 362,
    "description": "Sign In Button"
  },
  "confidence": 0.96,
  "requiresConfirmation": false
}
```

---

## 3. Action Result Schema (`ActionResult`)

Returned by the Content Script following safety checks and execution:

```json
{
  "success": true,
  "action": "CLICK",
  "target": "pb-element-002",
  "detail": "Dispatched click event on <button>",
  "timestamp": "2026-08-28T08:40:02Z"
}
```
