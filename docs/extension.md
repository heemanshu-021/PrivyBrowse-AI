# PrivyBrowse AI — Chrome Extension Documentation (Manifest V3)

## 1. Overview
The **PrivyBrowse AI Chrome Extension** serves as the on-device sensory input and actuation layer for the browser agent. It operates locally inside the Chromium browser process under **Manifest V3**.

### Core Architecture
```
┌────────────────────────────────────────────────────────┐
│ USER'S BROWSER (Chromium / Chrome)                     │
│                                                        │
│  ┌───────────────────┐       ┌──────────────────────┐  │
│  │ Webpage Tab       │       │ Extension Popup      │  │
│  │ (Active DOM)      │       │ (User Controls)      │  │
│  └─────────┬─────────┘       └──────────┬───────────┘  │
│            │                             │             │
│            ▼                             ▼             │
│  ┌───────────────────┐       ┌──────────────────────┐  │
│  │ Content Script    │◄─────►│ Background Worker    │  │
│  │ (Safe DOM Parser) │       │ (Service Worker V3)  │  │
│  └───────────────────┘       └──────────┬───────────┘  │
└─────────────────────────────────────────┼──────────────┘
                                          │ Local HTTP (Port 8000)
                                          ▼
┌────────────────────────────────────────────────────────┐
│ LOCAL PRIVYBROWSE ENGINE (On-Device Python Backend)    │
│  - OpenCV Contour Detector                             │
│  - Heuristic PII Regex & Haar Face Classifier          │
│  - Local Visual & DOM Redactor                         │
│  - Safe Action Planner                                 │
└────────────────────────────────────────────────────────┘
```

---

## 2. Installation & Loading Unpacked in Chrome

1. Open Google Chrome, Chromium, or Brave.
2. Navigate to `chrome://extensions`.
3. Enable the **Developer mode** toggle in the top-right corner.
4. Click **Load unpacked**.
5. Select the `/Users/heemanshusingh/Desktop/MY PROJECT/extension` directory.
6. The **PrivyBrowse AI - Browser Intelligence** extension icon (🛡️) will appear in your Chrome toolbar.

---

## 3. Permissions & Least-Privilege Design

The extension strictly requests only necessary permissions:

| Permission | Purpose |
| :--- | :--- |
| `activeTab` | Grants temporary access to inspect the currently active webpage tab when the user clicks the extension action. |
| `scripting` | Allows programmatic injection of the safe content script if a tab was opened prior to extension loading. |
| `storage` | Stores user local preferences (e.g. redaction style, engine endpoint). |
| `tabs` | Captures viewport screenshots of the active tab via `chrome.tabs.captureVisibleTab`. |
| `host_permissions` | Restricted strictly to `http://127.0.0.1:8000/*` and `http://localhost:8000/*` for local daemon communication. |

> [!IMPORTANT]
> The extension **does not** request `history`, `cookies`, `bookmarks`, `downloads`, `webRequest`, or arbitrary background network permissions.

---

## 4. Safe DOM Extraction & Privacy Guarantees

When extracting DOM nodes, the content script:
1. Filters elements strictly to **visible** controls in the current viewport.
2. Generates a temporary stable ID (`pb-element-001`) attached to the element dataset for reliable click/type targeting.
3. **Sensitive Field Protection**: Password fields, credit card inputs, CVVs, and SSN fields are classified with `sensitive: true` and their plaintext values are **never exported** in the page inspection context.

---

## 5. Action Execution Engine

The extension supports safe execution of verified agent actions:
* `CLICK`: Dispatches complete mouse event sequences (`mousedown` -> `mouseup` -> `click`) with automatic fallback for form submissions.
* `TYPE`: Focuses inputs and emits synthetic `input` and `change` events for React/Angular/Vue dynamic form state bindings.
* `PRESS_KEY`: Dispatches keyboard event sequences (`keydown`, `keypress`, `keyup`).
* `SCROLL`: Smoothly scrolls the window viewport by delta coordinates.
* `WAIT`: Pauses execution for the requested duration.

Before executing any action, the content script validates that the element exists, is visible in the viewport, and is enabled. If validation fails, it returns an explicit error (`TARGET_NOT_FOUND`, `TARGET_NOT_VISIBLE`, `TARGET_DISABLED`) rather than clicking arbitrary screen pixels.
