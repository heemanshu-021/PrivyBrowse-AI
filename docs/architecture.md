# PrivyBrowse AI — System Architecture & Trust Boundary

## 1. High-Level Architecture
PrivyBrowse AI implements an on-device visual perception and privacy firewall for autonomous browser agents.

```
+--------------------------------------------------------------------------------+
| TRUSTED LOCAL DEVICE ZONE (Strict Zero-Leak Boundary)                           |
|                                                                                |
|  +---------------------------+       +--------------------------------------+  |
|  | Webpage DOM & Viewport    |       | Chrome Extension (Manifest V3)       |  |
|  | - Raw HTML Elements       | ----> | - Visible DOM Extractor              |  |
|  | - Viewport Pixel Buffer   |       | - CaptureVisibleTab Stream           |  |
|  +---------------------------+       +------------------+-------------------+  |
|                                                         |                      |
|                                                         v                      |
|  +--------------------------------------------------------------------------+  |
|  | Local Perception Daemon (FastAPI localhost:8000)                         |  |
|  |                                                                          |  |
|  |   [OpenCV Contour Engine] ---------> Detects visual buttons & inputs     |  |
|  |   [OCR Layout Engine] -------------> Maps text coordinates to visual box |  |
|  |   [PII & Face Classifier] ---------> Identifies sensitive data & faces   |  |
|  |   [On-Device Redactor] ------------> Blurs/masks raw pixels & DOM values |  |
|  |   [IoU Context Fuser] -------------> Fuses DOM + CV contours safely      |  |
|  +--------------------------------------------------------------------------+  |
|                                       |                                        |
+---------------------------------------|----------------------------------------+
                                        | (SANITIZED CONTEXT ONLY)
                                        v
+--------------------------------------------------------------------------------+
| UNTRUSTED / REASONING LAYER                                                    |
|                                                                                |
|  +--------------------------------------------------------------------------+  |
|  | Autonomous Agent Planner                                                 |  |
|  | - Inspects sanitized visual frame ([CARD REDACTED], [EMAIL REDACTED])     |  |
|  | - Reasons over structured element metadata (pb-element-001)              |  |
|  | - Generates deterministic action payload (CLICK, TYPE, SCROLL)           |  |
|  +------------------------------------+-------------------------------------+  |
|                                       |                                        |
+---------------------------------------|----------------------------------------+
                                        | (Action Dispatch with Safety Gate)
                                        v
+--------------------------------------------------------------------------------+
| SAFETY GATEKEEPER & ACTION DISPATCH                                            |
|                                                                                |
|  - Verifies target element exists, is visible, and is enabled                  |
|  - Prompts user confirmation if high-impact action (Payment/Deletion)          |
|  - Actuates Chromium tab natively via Content Script                           |
+--------------------------------------------------------------------------------+
```

---

## 2. Core Security & Privacy Invariants

1. **Zero Raw PII WAN Egress**: Plaintext passwords, credit cards, CVVs, phone numbers, and raw facial images are processed strictly on the user's physical machine.
2. **Safe Token Substitution**: Sensitive inputs are substituted with anonymized tokens (e.g. `[PASSWORD REDACTED]`) before being processed by the reasoning layer.
3. **Least-Privilege Extension**: The Chrome extension operates strictly with `activeTab`, `scripting`, `storage`, and `tabs` permissions, without requesting persistent web browsing history or cookies.
4. **Deterministic Action Target Resolution**: Action execution prioritizes temporary stable identifiers (`pb-element-xxx`) over raw screen coordinates, preventing unintended misclicks caused by layout reflows.
