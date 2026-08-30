# PrivyBrowse-AI — Comprehensive Productionization & Engineering Audit

**Problem Statement:** SIH26171 — *On-Device Visual Perception for Lightweight Browser Agents*  
**Organization:** Indian Space Research Organisation (ISRO)  
**Project:** PrivyBrowse-AI  
**Audit Date:** August 30, 2026  
**Status:** Audit Completed (Pre-Implementation Baseline)

---

## 1. Executive Summary & Current Architecture

### 1.1 High-Level Architecture Overview
The current PrivyBrowse-AI codebase was architected around the SIH26171 vision of a privacy-preserving, on-device browser agent. It consists of four main layers:
1. **Frontend Dashboard (`frontend/`)**: React 19 + TypeScript + Vite web interface providing an overview, live browser preview canvas, perception overlay, telemetry charts, activity logs, scenario lab, and a judge presentation center.
2. **Browser Extension (`extension/`)**: Manifest V3 Chrome extension intended to capture tab screenshots via `chrome.tabs.captureVisibleTab`, scrape DOM interactive elements via content scripts, and execute actions on live web pages.
3. **Local Perception & Privacy Backend (`backend/`)**: FastAPI server containing computer vision detectors (OpenCV morphological contours + edge analysis), Tesseract OCR wrapper / DOM text proxy, multi-source IoU fusion, multi-signal PII detection (Indian PAN/Aadhaar, credit cards, passwords, OTPs, Haar Cascade face detection), visual and DOM redactors, prompt-injection guards, a heuristic rule-based planner, and action validator.
4. **Evaluation & Test Harness (`tests/`, `demo-pages/`, `benchmark-results.json`)**: Static HTML scenario pages, unit/adversarial verification scripts, and synthetic benchmark runners.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BROWSER & EXTENSION LAYER                                │
│  ┌────────────────────────┐         ┌─────────────────────────────────────────────────┐ │
│  │ Target Webpage (DOM)   │ ◄────── │ Extension Content Script (content.js)           │ │
│  │ (e.g. login, checkout) │         │ - extractNormalizedDOM()                        │ │
│  └──────────┬─────────────┘         │ - executeSafeAction() [Simulated Pointer Events]│ │
│             │                       └────────────────────────┬────────────────────────┘ │
│             │                                                │ chrome.runtime.sendMessage│
│             ▼                                                ▼                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Extension Background Service Worker (background.js)                                │ │
│  │ - captureActiveTab() -> base64 PNG                                                 │ │
│  │ - orchestrateAnalysis() -> POST /api/browser/context                               │ │
│  └──────────────────────────────────────────┬─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┼───────────────────────────────────────────┘
                                              │ HTTP JSON (Port 8000)
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL FASTAPI BACKEND DAEMON                               │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Perception Pipeline (PerceptionPipeline in backend/perception/core/pipeline.py)    │ │
│  │  1. ImageProcessor (cv2 decode/resize)                                             │ │
│  │  2. VisualDetector (cv2 contours, morphological close, edge density)               │ │
│  │  3. TesseractOCREngine (pytesseract if installed; else DOM_TEXT_PROXY fallback)    │ │
│  │  4. DOMDetector (Maps tag names and types to structural bounding boxes)            │ │
│  │  5. ContextFuser (IoU matching + source confidence calculation)                    │ │
│  └──────────────────────────────────────────┬─────────────────────────────────────────┘ │
│                                             │ PerceivedElement[]
│                                             ▼
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Privacy Gate & Redactor (PrivacyGate in backend/privacy/privacy_gate.py)           │ │
│  │  1. PIIDetector (Regex PAN, Aadhaar, Cards, Luhn, CV Haar Faces, DOM attributes)   │ │
│  │  2. Redactor (cv2 visual opaque/blur/pixelate + DOM text/value scrub)              │ │
│  │  3. PrivacyGateViolation guard (Blocks outbound transmission of unredacted data)   │ │
│  └──────────────────────────────────────────┬─────────────────────────────────────────┘ │
│                                             │ SanitizedContext (Zero raw secrets)
│                                             ▼
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Agent Decision & Security Layer (AgentPlanner in backend/agent/planner.py)         │ │
│  │  1. InjectionGuard (Neutralizes jailbreaks & prompt injection attacks)             │ │
│  │  2. GoalDecomposer (Regex / keyword task decomposition into sub-objectives)        │ │
│  │  3. CandidateGenerator + ActionScorer (Multi-factor heuristic candidate ranking)   │ │
│  │  4. ActionValidator (Safety gatekeeper: bounds, loops, action budgets, confirm)   │ │
│  │  5. ActionExecutor (backend/actions/executor.py - sleep-based simulated execution) │ │
│  │  6. ActionVerifier (Evaluates simulated post-action DOM delta)                     │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Real Data Flow Trace (Current Source Code Walkthrough)

Below is the step-by-step trace of a user requesting an action (e.g. `"Search for Chandrayaan-3"`):

```
User Task ("Search for Chandrayaan-3")
  │
  ├── [1] FRONTEND TRIGGER:
  │   - File: `frontend/src/context/AppContext.tsx` -> Function: `runPipeline()`
  │   - State: Reads `currentScenario` ('search') and `taskText`.
  │   - Real vs Mock Divergence:
  │       * Instead of triggering the extension to capture the actual active tab, `runPipeline()`
  │         invokes `getScenarioDOMNodes('search')` (hardcoded simulated coordinate array) and
  │         `getMockScreenshotB64()` (a static 1x1 black pixel base64 PNG).
  │
  ├── [2] INGESTION & PERCEPTION:
  │   - Endpoint: `POST /api/perception/full` -> `backend/main.py:run_full_perception()`
  │   - Pipeline: `backend/perception/core/pipeline.py:PerceptionPipeline.run()`
  │       * `ImageProcessor.decode()` decodes the base64 PNG into a numpy OpenCV array.
  │       * `TesseractOCREngine.extract_text()` checks `pytesseract` and system binary.
  │         (If `tesseract` binary is missing, logs warning and falls back to `DOM_TEXT_PROXY`).
  │       * `VisualDetector.detect()` runs `cv2.adaptiveThreshold`, `cv2.findContours`, and
  │         `cv2.Canny` edge filtering.
  │       * `DOMDetector.detect()` converts provided DOM dicts into `PerceivedElement` instances.
  │       * `TextDetector.detect_from_dom_text()` creates text proxy elements.
  │       * `ContextFuser.fuse()` performs IoU matching between DOM boxes and OpenCV contours,
  │         assigning stable IDs (`pb-element-001`).
  │
  ├── [3] PRIVACY GATING & REDACTION:
  │   - Endpoint: `POST /api/privacy/detect` & `POST /api/privacy/redact` (or `POST /api/privacy/sanitize`)
  │   - Handler: `backend/privacy/privacy_gate.py:PrivacyGate.process_and_sanitize()`
  │       * `PIIDetector.detect()` scans text against `pattern_rules.py` (Luhn algorithm, PAN,
  │         Aadhaar, emails, phones, API tokens) and runs OpenCV Haar Cascade face detection.
  │       * `Redactor.redact_screenshot()` paints opaque black bounding boxes or applies Gaussian
  │         blur / pixelation on screenshot image bytes.
  │       * `Redactor.redact_dom_nodes()` sanitizes values/placeholders in DOM dicts.
  │       * Constructs `SanitizedContext` and appends privacy-safe audit logs.
  │
  ├── [4] AGENT PLANNING & VALIDATION:
  │   - Endpoint: `POST /api/agent/plan` -> `backend/main.py:plan_agent_action()`
  │   - Handler: `backend/agent/planner.py:AgentPlanner.plan_next_step()`
  │       * `GoalDecomposer.decompose()` identifies task category ("search") and yields sub-objectives.
  │       * `LocalRuleBasedEngine.plan_next_action()`:
  │           - `InjectionGuard.sanitize_untrusted_elements()` strips malicious directives.
  │           - `CandidateGenerator.generate_candidates()` finds matching `INPUT` / `BUTTON` nodes.
  │             (Note: Hardcoded template strings like `"Chandrayaan-3"` or extracted keywords are assigned).
  │           - `ActionScorer.score_candidates()` computes composite score:
  │             `0.40*Semantic + 0.25*Confidence + 0.20*TypeMatch + 0.15*Visibility - HistoryPenalty - RiskPenalty`.
  │       * `ActionValidator.validate_candidate()` checks screen coordinate bounds, action budget (max 15),
  │         repeated action loops (>=3), and checks if target element has critical risk (requiring human confirmation).
  │
  ├── [5] ACTION DISPATCH & EXECUTION:
  │   - File: `frontend/src/context/AppContext.tsx` -> `executePlannedAction()` -> `proceedExecution()`
  │   - Endpoint: `POST /api/action/execute` -> `backend/actions/executor.py:ActionExecutor.execute_browser_action()`
  │   - REALITY GAP:
  │       * `ActionExecutor` logs the action, checks boundaries, and runs `time.sleep(0.015)`.
  │       * It returns `ActionResult(success=True, status="SUCCESS", metadata={"method": "SYNTHETIC_POINTER_DISPATCH"})`.
  │       * NO message is dispatched back to `content.js` or Chrome DevTools Protocol (CDP) to actually click/type
  │         on the live browser tab.
  │
  ├── [6] VERIFICATION & STATE UPDATE:
  │   - Handler: `backend/actions/agent_runner.py` / `frontend/src/context/AppContext.tsx`
  │   - REALITY GAP:
  │       * Verification evaluates against simulated in-memory DOM mutations (`simulated_next_elements`)
  │         rather than capturing a fresh screenshot and live DOM tree from the browser.
  │
  └── [7] DASHBOARD TELEMETRY & VIEW:
      - Frontend updates timeline step icons (`OBSERVE`, `PERCEIVE`, `DETECT`, `REDACT`, `FUSION`, `PLAN`, `ACT`, `VERIFY`).
      - Renders simulated JSX mockup inside `BrowserPreview.tsx` with overlay boxes in `PerceptionOverlay.tsx`.
```

---

## 3. Comprehensive Component Status Matrix

| Component / Subsystem | Location | Classification | Detailed Rationale & Evidence |
| :--- | :--- | :--- | :--- |
| **OpenCV Visual Contour Detector** | `backend/perception/detectors/visual_detector.py` | **REAL / WORKING** | Real OpenCV image processing: converts image to grayscale, applies Gaussian blur, adaptive thresholding, morphological closing, finds contours with hierarchy, filters bounding boxes, and calculates Canny edge density to adjust confidence. |
| **Image Preprocessing** | `backend/perception/preprocessing/image_processor.py` | **REAL / WORKING** | Real OpenCV image decoders, contrast enhancement (CLAHE), adaptive scaling (downsamples >1920px), and grayscale conversion. |
| **Coordinate System & Geometry** | `backend/perception/core/coordinator.py`, `geometry.py` | **REAL / WORKING** | Real geometric coordinate transformations (viewport scaling, devicePixelRatio scaling, scroll offset, IoU math, NMS deduplication, visibility categorization). |
| **Tesseract OCR Engine** | `backend/perception/ocr/tesseract_engine.py` | **PARTIALLY IMPLEMENTED** | Real code utilizing `pytesseract.image_to_data` and grouping words into line-level bounding boxes. However, if the system binary `tesseract` is not installed on host OS, it silently degrades to DOM text proxy fallback. |
| **DOM Element Detector** | `backend/perception/detectors/dom_detector.py` | **REAL / WORKING** | Parses incoming DOM node dictionaries, maps tags/types to semantic types (`BUTTON`, `INPUT`, `LINK`), extracts labels, and generates structured `PerceivedElement` objects. |
| **Multi-Source Context Fusion** | `backend/perception/fusion/context_fuser.py`, `iou_matcher.py` | **REAL / WORKING** | Real multi-source fusion algorithm: anchors on DOM elements, matches OpenCV vision boxes via IoU >= 0.35, matches OCR text regions, appends unmatched vision/text elements, and calculates multi-source weighted confidence. |
| **PII Pattern Detector** | `backend/privacy/pii_detector.py`, `rules/pattern_rules.py` | **REAL / WORKING** | Real regex and algorithmic checksum validators: Luhn algorithm for credit cards, Indian PAN format regex (`[A-Z]{5}[0-9]{4}[A-Z]`), Verhoeff/format checks for Aadhaar, phone numbers, email addresses, API tokens/JWTs, and password DOM semantic inspections. |
| **Visual Face Detector** | `backend/privacy/pii_detector.py` | **REAL / WORKING** | Real OpenCV `cv2.CascadeClassifier` using Haar Cascade (`haarcascade_frontalface_default.xml`) on decoded screenshot buffers to locate facial bounding boxes. |
| **False Positive Context Rules** | `backend/privacy/rules/context_rules.py` | **REAL / WORKING** | Real algorithmic filters suppressing false-positive detections for calendar years (2020-2035), monetary currencies (₹, $), order/SKU numbers, and image dimensions. |
| **Visual & DOM Redactor** | `backend/privacy/redactor.py` | **REAL / WORKING** | Real pixel manipulation: paints solid dark boxes with text labels in `opaque` mode, applies OpenCV Gaussian blur on ROIs in `blur` mode, and pixelates ROIs in `pixelate` mode. Scrubs DOM attributes (`value`, `placeholder`, `text`). |
| **Privacy Gatekeeper & Policy** | `backend/privacy/privacy_gate.py` | **REAL / WORKING** | Real security gate: strictly checks outbound context, raises `PrivacyGateViolation` if unredacted data is passed, enforces local policy, and records sanitized audit logs. |
| **Prompt Injection Guard** | `backend/security/injection_guard.py` | **REAL / WORKING** | Real security scanner: detects prompt injection directives (`"ignore previous instructions"`, `"act as DAN"`, exfiltration commands) in untrusted webpage text, sanitizes input, and assigns threat levels. |
| **Navigation Guard** | `backend/security/navigation_guard.py` | **REAL / WORKING** | Real protocol validator: blocks dangerous URL schemes (`javascript:`, `data:`, `file:`, `vbscript:`) and prevents navigation to binary executable file downloads (`.exe`, `.sh`, `.apk`, etc.). |
| **Secret Scanner** | `backend/security/secret_scanner.py` | **REAL / WORKING** | Real static file scanner: scans local workspace directory for leaked API keys (AWS, OpenAI, GitHub tokens, JWTs, `.env` files). |
| **Goal Decomposer** | `backend/agent/decomposer.py` | **PARTIALLY IMPLEMENTED** | Decomposes goals into structured objectives using hardcoded regex/keyword branches (`search`, `login`, `checkout`, `scroll`). Lacks LLM or generalised semantic parsing for arbitrary dynamic web tasks. |
| **Candidate Action Generator** | `backend/agent/candidate_generator.py` | **PARTIALLY IMPLEMENTED** | Generates `CLICK`, `TYPE`, `SCROLL` candidates from layout elements. However, text payloads for input fields are hardcoded strings (e.g. `'user@sih2026.gov.in'`, `'Chandrayaan-3'`, `'Amit Sharma'`). |
| **Action Scorer & Ranking** | `backend/agent/scoring.py` | **REAL / WORKING** | Real multi-factor mathematical scoring: weighted combination of semantic keyword overlap, perception confidence, type match, visibility factor, history repeat penalties, and risk penalties. |
| **Action Safety Validator** | `backend/agent/validator.py` | **REAL / WORKING** | Real pre-execution safety gate: validates bounding coordinates against viewport dimensions, checks action limits, detects 3-cycle action loops, inspects hidden/zero-opacity elements, and flags high-risk/financial actions for human confirmation. |
| **Action Verifier** | `backend/agent/verifier.py` | **PARTIALLY IMPLEMENTED** | Real verification logic comparing before/after state diffs (URL changes, element disappearance, value changes). However, when called from `agent_runner.py`, it receives synthetic mocked state dicts instead of live browser observations. |
| **Action Executor** | `backend/actions/executor.py` | **MOCK / SIMULATION** | The backend executor does NOT interact with the browser tab or extension. It performs safety validation, sleeps for 15-40ms, and returns a synthetic `ActionResult(success=True)`. |
| **Continuous Agent Runner** | `backend/actions/agent_runner.py` | **PARTIALLY IMPLEMENTED** | Implements the state machine multi-turn loop, but simulates post-action element mutations in memory (`simulated_next_elements = [dict(e) for e in sanitized_elements]`) instead of capturing live browser feedback. |
| **Browser Extension Manifest & Background** | `extension/manifest.json`, `background.js` | **REAL / WORKING** | Real Manifest V3 extension: queries active tabs, captures visible tabs as base64 PNGs via `chrome.tabs.captureVisibleTab`, injects content scripts, and syncs context to `http://127.0.0.1:8000/api/browser/context`. |
| **Extension DOM Scraper** | `extension/content.js` | **REAL / WORKING** | Real DOM extraction: traverses document interactive elements (`button`, `input`, `a`, etc.), checks visibility (`getComputedStyle`, bounding rectangles), extracts text/attributes, and assigns `data-pb-id` attributes. |
| **Extension Action Dispatcher** | `extension/content.js` | **PARTIALLY IMPLEMENTED** | Contains real DOM event dispatchers (`dispatchEvent(new MouseEvent('click'))`, `element.value = ...`, `dispatchEvent(new Event('input'))`, `scrollBy`). However, it is never called by the backend or dashboard during autonomous runs. |
| **Extension Popup UI** | `extension/popup.js`, `popup.html` | **PARTIALLY IMPLEMENTED** | Checks backend health and triggers page analysis. But "Start", "Pause", and "Stop" buttons only display UI text messages without sending commands to the agent control API. |
| **Extension TypeScript Source** | `extension/src/*` | **PLACEHOLDER / UNUSED** | Contains TypeScript source files (`index.ts`, `dom.ts`, `browserContextService.ts`) which are completely separate from the plain JS files loaded by `manifest.json`. No build tool (esbuild/webpack) compiles `src/`. |
| **Frontend Live Browser Preview** | `frontend/src/components/workspace/BrowserPreview.tsx` | **MOCK / SIMULATION** | Does not render an actual live browser frame or iframe. Renders hardcoded React JSX mockup divs representing fake pages (`login`, `search`, `checkout`, `profile`). |
| **Frontend Pipeline Trigger** | `frontend/src/context/AppContext.tsx` | **MOCK / SIMULATION** | In `runPipeline()`, it passes `getScenarioDOMNodes()` (hardcoded mock coordinates) and a 1x1 black PNG instead of fetching live screenshots and DOM from the extension or backend browser status. |
| **Benchmark Runner & Metrics** | `backend/performance/benchmarks.py`, `tracker.py` | **REAL / WORKING** | Real statistical latency distributions (mean, median, P95, min, max, memory RSS via `psutil`), and empirical PII evaluation logic. (Uses synthetic page models for standardized testing). |
| **Benchmark Export Endpoint** | `backend/main.py:export_benchmark_results` | **BROKEN** | **Bug:** Uses `FileResponse` without importing it from `fastapi.responses` or `starlette.responses`, causing an unhandled `NameError` 500 server crash when `/api/benchmark/export` is requested. |
| **Test Suite** | `tests/test_*.py`, `tests/verify_backend.py` | **REAL / WORKING** | All 8 test scripts execute successfully in standalone Python environment, verifying in-memory perception, PII detection, security rules, adversarial attacks, and benchmark calculations. |

---

## 4. Real vs. Mock Subsystem Matrix

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                                REAL VS MOCK BREAKDOWN                                 │
├──────────────────────────────────────┬────────────────────────────────────────────────┤
│ REAL & FUNCTIONING                   │ MOCK / SIMULATED / SYNTHETIC                   │
├──────────────────────────────────────┼────────────────────────────────────────────────┤
│ • OpenCV Contour & Edge Perception   │ • Browser Action Execution in Backend          │
│ • OpenCV Haar Cascade Face Detection │   (ActionExecutor sleeps and returns True)     │
│ • Indian PAN & Aadhaar Validation    │ • Live Browser Preview in Frontend UI          │
│ • Luhn Algorithm Credit Card Check   │   (Hardcoded JSX divs, not live iframe/tab)    │
│ • Regex & DOM Password Detection     │ • Frontend DOM Input to Pipeline               │
│ • Visual Image Redaction (cv2 mask)  │   (Sends hardcoded node dicts + 1x1 pixel PNG) │
│ • Outbound Privacy Gatekeeper Guard  │ • Continuous Agent State Mutation              │
│ • Prompt Injection Defense           │   (Simulates DOM changes in RAM)               │
│ • Navigation & Scheme Guard          │ • Goal Intent Extraction                       │
│ • Multi-Factor Action Scoring        │   (Hardcoded scenario branching & payloads)    │
│ • Pre-Execution Safety Bounds        │ • Extension Popup Buttons                      │
│ • Statistical Telemetry & Tracker    │   (Start/Stop buttons just change string)      │
│ • Extension DOM Extractor & Shooter  │ • Extension TypeScript source files            │
│ • Standalone Adversarial Test Suite  │   (Unused in runtime; plain JS loaded)         │
└──────────────────────────────────────┴────────────────────────────────────────────────┘
```

---

## 5. Missing Functionality for a Genuinely Working System

1. **Bidirectional Extension-Backend Execution Channel**:
   - The extension currently captures screenshots and posts DOM to `/api/browser/context`. However, there is no bidirectional bridge (WebSocket, Long-Polling, or Native Messaging) allowing the backend agent to send planned actions (`CLICK`, `TYPE`, `SCROLL`) back to the browser tab for live execution.
2. **Dynamic Live Tab Perception in Dashboard**:
   - The frontend dashboard does not visualize the live browser context received from the extension. Instead, it relies on static scenario arrays.
3. **Adaptive / Generalized Semantic Planner**:
   - The agent relies entirely on fixed keywords (`"Chandrayaan-3"`, `"user@sih2026.gov.in"`, `"Amit Sharma"`) and hardcoded goal branches. It cannot parse or execute an arbitrary user instruction on an unknown website.
4. **Real Re-Perception Loop**:
   - In autonomous mode, after executing an action, the agent must wait for page mutation, capture a fresh screenshot and DOM from the browser, re-perceive and re-sanitize the page, and verify the real state change rather than fabricating state in memory.
5. **OCR Binary Packaging & Fallback Enhancement**:
   - If Tesseract is not installed on the host machine, visual text on canvas, buttons without text tags, and image banners cannot be recognized visually. A bundled OCR solution or clear binary runtime verification is required.
6. **Iframe / Live Sandbox Bridge in Frontend**:
   - The Demo Lab iframe should be interactable by the agent via direct script injection or extension active-tab tracking.
7. **Extension Build & TypeScript Unification**:
   - The extension repository has an orphaned `src/` TypeScript directory that does not compile into the active extension scripts.

---

## 6. Prioritized Gaps & Issues (P0 / P1 / P2)

### P0 — Must Fix (Core System Functionality)
1. **P0.1: Fix `FileResponse` NameError in `backend/main.py`**:
   - `export_benchmark_results()` crashes with `NameError: name 'FileResponse' is not defined` because `FileResponse` was not imported from `fastapi.responses`.
2. **P0.2: Implement Live Action Execution Bridge**:
   - Replace the simulated `time.sleep` in `ActionExecutor` with real action dispatching to the active browser tab via the extension (`chrome.tabs.sendMessage` / action queue polling or WebSocket).
3. **P0.3: Connect Live Extension Context to Frontend Dashboard**:
   - Allow the user to toggle between "Demo Sandbox Scenarios" and "Live Active Browser Tab". When in Live Tab mode, send real viewport screenshots and real DOM trees from the extension into the perception and privacy pipeline.
4. **P0.4: Eliminate 1x1 Pixel Mock Screenshot Fallback in Pipeline**:
   - Replace the static 1x1 black PNG in `AppContext.tsx` with actual rendered canvas / iframe screenshots or live tab captures.
5. **P0.5: Implement True Re-Perception in Multi-Turn Agent Loop**:
   - `agent_runner.py` must request a real re-perception pass after every executed action to observe actual DOM and visual changes before planning the next step.

### P1 — Important (Production Quality & Robustness)
6. **P1.1: Generalized Parameter Extraction in Planner**:
   - Extract search queries, form values, and target selectors dynamically from user prompts instead of hardcoding fallback strings.
7. **P1.2: Extension Action Execution Hardening**:
   - Enhance `content.js` execution to support synthetic keyboard events for React/Vue/Angular controlled inputs (`Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set`), key combinations, and scroll stabilization.
8. **P1.3: Extension Popup Controller Wiring**:
   - Connect the extension popup's Start, Pause, and Stop buttons to the backend `/api/agent/control` and `/api/agent/task/create` endpoints.
9. **P1.4: Real Iframe Controller in Demo Lab**:
   - Allow direct agent interaction with the iframe sandbox in DemoLabPage, capturing its canvas and driving actions inside the framed document.
10. **P1.5: Tesseract OCR Environment Verification & Fallback Logging**:
    - Provide clear diagnostic health checks in `/api/perception/status` detailing Tesseract availability and OCR confidence.

### P2 — Improvement (Polish, Developer Experience & Compliance)
11. **P2.1: Extension Build Pipeline Integration**:
    - Add a Vite/esbuild build script to compile `extension/src/` into `dist/` or sync with root `extension/` scripts.
    - Add a comprehensive developer guide.
12. **P2.2: Comprehensive Pytest Integration**:
    - Package standalone test scripts into standard `pytest` fixtures with CI configuration.
13. **P2.3: Video / Animated Step Recording**:
    - Record perception bounding box overlays and action markers as exportable visual artifacts.

---

## 7. Technical Risks & Constraints

1. **Browser Security & Cross-Origin Restrictions**:
   - Extension content scripts cannot inspect cross-origin iframes without appropriate manifest permissions or debugger API.
   - `chrome.tabs.captureVisibleTab` requires `activeTab` or `<all_urls>` permission and user focus on the window.
2. **React Controlled Input State Synchronization**:
   - Simply setting `input.value = "text"` often fails in modern frameworks (React/Vue) because internal state listeners are bypassed. Must dispatch `InputEvent` and call native prototype value setters.
3. **High-DPI / Retina Coordinate Mismatches**:
   - Screenshots captured on macOS Retina displays have a `devicePixelRatio` of 2.0 (e.g. 2560x1600 physical pixels for a 1280x800 CSS viewport). The coordinate coordinator must accurately map OpenCV contour coordinates back to CSS viewport coordinates for extension click dispatch.
4. **Local OCR Latency vs Accuracy**:
   - Running full-page Tesseract OCR on large 4K screenshots can take 200-500ms. Morphological ROI filtering and adaptive resizing must be preserved to maintain sub-100ms perception times.

---

## 8. Recommended Implementation Order (Step-by-Step Roadmap)

```
Phase 1: Critical Bug Fix & Core Infrastructure
  ├── Fix FileResponse import in backend/main.py
  ├── Establish Extension <-> Backend Action Queue / WebSocket channel
  └── Unify Extension build artifacts

Phase 2: Live Browser Perception & Action Bridge
  ├── Enable real screenshot & DOM ingestion from Extension to Backend
  ├── Connect Frontend Workspace to Live Tab stream (real screenshots + overlay)
  └── Implement native input & click dispatching in extension content.js

Phase 3: Autonomous Agent Loop & Dynamic Re-Perception
  ├── Update AgentRunner to perform real re-perception between turns
  ├── Generalize Decomposer & Candidate Generator for dynamic user instructions
  └── Wire Extension popup controls to Backend Agent State Machine

Phase 4: Verification, Benchmarking & Polish
  ├── Validate all 6 Demo Scenarios on live HTML demo pages
  ├── Run end-to-end multi-turn tasks on real live web pages (e.g. Wikipedia search)
  └── Update automated benchmark suite and documentation
```

---

## 9. Final Definition of DONE

The PrivyBrowse-AI project will be considered **DONE** and production-ready for SIH judging when:
1. **Live Browser Automation**: The user can open any live web page (or local demo page), issue a task in the frontend or extension popup, and watch the agent autonomously perceive the page, redact PII locally, plan the step, click/type in the real browser tab, observe the real page update, and complete the goal.
2. **Zero Cloud Vision Calls**: All visual contour detection, OCR layout mapping, face detection, and PII masking operate 100% locally on-device without making external vision API requests.
3. **Zero-Leak Trust Boundary**: In all modes, raw passwords, credit card numbers, PAN/Aadhaar IDs, OTPs, and face regions are masked before being passed to reasoning modules or telemetry logs.
4. **Safety & Confirmation Enforcement**: High-risk financial payments and destructive actions reliably trigger human confirmation dialogs that cannot be spoofed by webpage prompt injections.
5. **Zero 500 Errors & Clean Build**: All API endpoints (including benchmark export) return valid responses with no unhandled exceptions, and frontend/extension builds compile with zero errors.
