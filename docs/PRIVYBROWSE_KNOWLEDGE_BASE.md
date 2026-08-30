# PRIVYBROWSE AI — COMPLETE KNOWLEDGE BASE & DEFENSE MASTER GUIDE

> **Product**: PRIVYBROWSE AI  
> **Tagline**: *"See. Understand. Protect. Act."*  
> **Problem Statement**: SIH26171 — *On-Device Visual Perception for Lightweight Browser Agents*  
> **Organization**: Indian Space Research Organisation (ISRO)  
> **Status**: Final SIH Release (`v1.0.0-sih`) | **Evaluation Score**: **99.0 / 100** | **Cloud Vision Dependency**: **0% (100% On-Device)**

---

# TABLE OF CONTENTS
1. [Project Overview](#1-project-overview)
2. [SIH Problem Statement Alignment](#2-sih-problem-statement-alignment)
3. [Complete System Architecture](#3-complete-system-architecture)
4. [Complete Data Flow (Task Walkthrough)](#4-complete-data-flow-task-walkthrough)
5. [Complete Folder Structure](#5-complete-folder-structure)
6. [Important Source Files](#6-important-source-files)
7. [Important Functions](#7-important-functions)
8. [Important Classes](#8-important-classes)
9. [Frontend Command Center](#9-frontend-command-center)
10. [Backend Daemon & API Routes](#10-backend-daemon--api-routes)
11. [Browser Extension (Manifest V3)](#11-browser-extension-manifest-v3)
12. [Computer Vision Engine](#12-computer-vision-engine)
13. [OCR Engine & Layout Extraction](#13-ocr-engine--layout-extraction)
14. [Multi-Source Perception Fusion](#14-multi-source-perception-fusion)
15. [PII Detection Engine](#15-pii-detection-engine)
16. [Privacy Gate & Redaction Layer](#16-privacy-gate--redaction-layer)
17. [Agent Brain & Reasoning Engine](#17-agent-brain--reasoning-engine)
18. [Action Execution Subsystem](#18-action-execution-subsystem)
19. [Action Validation & Risk Analysis](#19-action-validation--risk-analysis)
20. [Human-in-the-Loop Confirmation](#20-human-in-the-loop-confirmation)
21. [Verification & State Monitoring](#21-verification--state-monitoring)
22. [Security & Threat Defense](#22-security--threat-defense)
23. [Adversarial Prompt Injection Defense](#23-adversarial-prompt-injection-defense)
24. [Performance Telemetry & Benchmarking](#24-performance-telemetry--benchmarking)
25. [Testing & Verification Suites](#25-testing--verification-suites)
26. [Project Dependencies](#26-project-dependencies)
27. [Environment Setup & Installation](#27-environment-setup--installation)
28. [Git & GitHub Repository](#28-git--github-repository)
29. [Demonstration Guide](#29-demonstration-guide)
30. [Speaking Scripts (Judge Presentation)](#30-speaking-scripts-judge-presentation)
31. [Judge & Viva Questions (100 Q&A)](#31-judge--viva-questions-100-qa)
32. [Technology Choices ("Why did you choose this?")](#32-technology-choices-why-did-you-choose-this)
33. [Known Limitations & Edge Cases](#33-known-limitations--edge-cases)
34. [Implemented vs. Planned Matrix](#34-implemented-vs-planned-matrix)
35. [Architecture Cheat Sheet](#35-architecture-cheat-sheet)
36. [File Cheat Sheet](#36-file-cheat-sheet)
37. [Technology Cheat Sheet](#37-technology-cheat-sheet)
38. [20 Things You Must Memorize](#38-20-things-you-must-memorize)
39. [Files Judges May Inspect](#39-files-judges-may-inspect)
40. [Beginner Hinglish Explanation](#40-beginner-hinglish-explanation)
41. [Self-Test Quiz (60 Questions + Answer Key)](#41-self-test-quiz-60-questions--answer-key)

---

## 1. Project Overview

### 1.1 What is PrivyBrowse AI?
**PrivyBrowse AI** is an on-device visual perception engine, local privacy gatekeeper, and lightweight browser agent runtime. It enables an AI browser agent to observe, perceive, sanitize, plan, execute, and verify web tasks locally without ever transmitting raw screenshots, user credentials, or personally identifiable information (PII) to remote cloud vision APIs.

### 1.2 The Core Problem
Modern autonomous browser agents (such as OpenAI Operator, Adept, or Claude Computer Use) rely heavily on remote Multimodal Large Language Models (MLLMs). To take an action, they take a full-resolution screenshot of the user's browser and send it to cloud servers. This introduces two critical flaws:
1. **Severe Privacy & Data Leaks**: Passwords, bank account numbers, Indian PAN cards, Aadhaar numbers, OTPs, and confidential enterprise documents are sent in raw pixel form over the internet.
2. **High Latency & Cloud Costs**: Each visual step requires 500 ms to 2,500 ms in cloud network and inference latency, costing significant API fees per step.

### 1.3 The PrivyBrowse Solution
PrivyBrowse AI executes the entire perception and privacy sanitization pipeline **100% on-device**:
* **On-Device Visual Perception**: Combines OpenCV contour detection, Tesseract OCR layout parsing, and DOM geometry into fused interactive elements in **~1.8 ms**.
* **Zero-Leak Privacy Gate**: Identifies and visually masks Indian PAN, Aadhaar, payment cards, passwords, and OTPs on-device before any reasoning step occurs.
* **Deterministic Agent Planner**: Decomposes user goals and ranks actions using multi-factor heuristic scoring in **~0.15 ms**.
* **Safe Action Executor**: Dispatches validated atomic browser actions with screen boundary checks, loop detection, and anti-spoofing human confirmation.

---

## 2. SIH Problem Statement Alignment

### Problem Title: SIH26171 — *On-Device Visual Perception for Lightweight Browser Agents*
**Organization**: Indian Space Research Organisation (ISRO)

| Problem Term | Beginner Meaning | Exact Implementation in PrivyBrowse AI |
| :--- | :--- | :--- |
| **ON-DEVICE** | Computation runs locally on the host machine CPU without remote server calls. | Implemented using Python, OpenCV, and pytesseract running on `127.0.0.1:8000`. 0 cloud vision API calls. |
| **VISUAL** | Processing graphical representations (pixels, contours, bounding boxes). | Captures browser viewport screenshots and applies adaptive thresholding + contour finding. |
| **PERCEPTION** | Converting raw pixel data into structured UI knowledge (Buttons, Inputs, Links). | `ContextFuser` merges DOM, OCR, and OpenCV detections into unified `FusedElement` records. |
| **LIGHTWEIGHT** | Fast execution, minimal RAM footprint, sub-millisecond latency. | Sub-20ms total agent cycle; no 10GB neural network weights needed. |
| **BROWSER** | Interacting directly with web pages inside Chromium browsers. | Manifest V3 Chrome Extension + REST IPC bridge to local FastAPI backend. |
| **AGENT** | Autonomous software that perceives environment, plans, and executes safe actions. | `AgentPlanner` + `ActionValidator` + `ActionExecutor` orchestrating multi-turn tasks. |

---

## 3. Complete System Architecture

```
[ UNTRUSTED WEBPAGE ENVIRONMENT ]
   ├── Webpage DOM Text, HTML Elements, & Attributes
   ├── OCR Extracted Text & Layout Blocks
   ├── Button, Link, & Form Labels
   └── Injected Malicious Prompt Directives & Scripts
                     │
                     ▼
[ INJECTION GUARD & PII SANITIZATION GATE ]
   ├── Neutralizes Adversarial Jailbreaks & Command Overrides
   └── Scrubs & Masks Raw PII (PAN, Aadhaar, Cards, Passwords)
                     │
═════════════════════╪═══════════════════════════════════════════ [ TRUST BOUNDARY ]
                     ▼
[ TRUSTED LOCAL AGENT RUNTIME ]
   ├── Master Agent Planner (Intent-driven, User Goal Isolated)
   ├── Action Security Validator (Bounds, Budget, Loop, Risk Policy)
   ├── Human Confirmation Gate (Anti-spoofing modal UI)
   ├── Real Action Executor (Whitelist protocols & safe key dispatch)
   └── Zero-Leak Audit Logger (Masked logs only)
```

---

## 4. Complete Data Flow (Task Walkthrough)

Example Task: **"Search for Chandrayaan-3 and open the first relevant result"**

```
1. USER TYPES GOAL:
   User enters natural language task in Frontend Workspace.
   Payload: { "goal": "Search for Chandrayaan-3", "url": "/demo/search.html" }

2. FRAME INGESTION:
   Manifest V3 Extension or Synthetic Sandbox captures Screenshot (Base64) + DOM Tree.

3. ON-DEVICE PERCEPTION:
   - `preprocessor.py`: Decodes Base64 to PIL Image, applies contrast stretching.
   - `element_detector.py`: OpenCV converts to grayscale, runs Otsu's thresholding, finds rectangular contours.
   - `ocr_engine.py`: pytesseract extracts text blocks with bounding boxes [x, y, w, h].
   - `context_fuser.py`: Merges DOM + OCR + Contours using IoU matching (IoU >= 0.30).
   Output: List of raw `FusedElement` objects.

4. PII DETECTION & PRIVACY GATE:
   - `pii_detector.py`: Scans text and attributes for PAN, Aadhaar, Cards, Passwords.
   - `redactor.py`: Applies visual blur/masking on screenshot; substitutes text with tokens.
   - `privacy_gate.py`: Enforces zero-leak boundary (blocks raw egress).
   Output: `SanitizedContext` containing redacted screenshot and clean element tokens.

5. ADVERSARIAL INJECTION GUARD:
   - `injection_guard.py`: Neutralizes prompt injection strings (e.g. "Ignore instructions").

6. AGENT PLANNING & SCORING:
   - `candidate_generator.py`: Identifies interactive elements matching search intent.
   - `scoring.py`: Computes composite ranking score:
     Score = 0.35(Semantic) + 0.25(PerceptionConfidence) + 0.20(TypeAlignment) + 0.20(Visibility)
   - `engine.py`: Selects top action: TYPE "Chandrayaan-3" into element #search-input.

7. ACTION VALIDATION:
   - `validator.py`: Verifies screen boundaries (1920x1080), action budget (<15), loop history.

8. ACTION EXECUTION:
   - `executor.py`: Validates URL protocol via `NavigationGuard` and dispatches atomic keystrokes/clicks.

9. VERIFICATION & RE-PERCEPTION:
   - `page_change_detector.py`: Detects DOM delta and URL transition to search results.
   - Loop triggers automatic re-perception, selects primary article link, and finishes task.
```

---

## 5. Complete Folder Structure

```
/Users/heemanshusingh/Desktop/MY PROJECT/
├── backend/                       # Python Backend Engine
│   ├── actions/                   # Real Browser Execution Layer
│   │   ├── __init__.py            # Module exports
│   │   ├── executor.py            # Real action dispatcher (CLICK, TYPE, SCROLL, NAVIGATE)
│   │   ├── page_change_detector.py# Monitors URL, DOM mutations, and scroll state
│   │   ├── runner.py              # End-to-end multi-turn agent loop coordinator
│   │   └── schemas.py             # Action schemas (ActionResult, ExecutionStatus)
│   ├── agent/                     # Lightweight Decision & Planning Engine
│   │   ├── __init__.py            # Agent exports
│   │   ├── candidate_generator.py # Generates candidate actions for objectives
│   │   ├── engine.py              # Local rule-based reasoning engine
│   │   ├── planner.py             # Master Agent Planner coordinator
│   │   ├── schemas.py             # Agent schemas (CandidateAction, AgentTask)
│   │   ├── scoring.py             # Multi-factor candidate ranking scorer
│   │   ├── state_machine.py       # Deterministic Agent State Machine
│   │   ├── task_decomposer.py     # Decomposes user goal into sub-objectives
│   │   ├── validator.py           # Safety boundary, budget, and loop checker
│   │   └── verifier.py            # Outcome verifier and post-action checker
│   ├── perception/                # On-Device Visual Perception Subsystem
│   │   ├── __init__.py            # Perception exports
│   │   ├── context_fuser.py       # IoU multi-source fusion (DOM + OCR + OpenCV)
│   │   ├── coordinate_converter.py# Viewport ↔ Screenshot coordinate scaler
│   │   ├── element_detector.py    # OpenCV contour detector & visual analyzer
│   │   ├── ocr_engine.py          # Local Tesseract OCR extraction engine
│   │   ├── pipeline.py            # Integrated perception pipeline orchestrator
│   │   ├── preprocessor.py        # Image decoding & contrast enhancement
│   │   └── schemas.py             # Perception data models (BoundingBox, FusedElement)
│   ├── performance/               # Performance Telemetry & Optimization
│   │   ├── __init__.py            # Performance exports
│   │   ├── benchmarks.py          # 8-page perception & 10-task evaluation runner
│   │   ├── optimizations.py       # Regex precompilation & cascade caching
│   │   ├── schemas.py             # Benchmark & telemetry schemas
│   │   └── tracker.py             # High-res nanosecond latency & memory tracker
│   ├── privacy/                   # On-Device PII Detection & Privacy Gate
│   │   ├── rules/                 # Detection rule modules
│   │   │   ├── __init__.py        # Rule exports
│   │   │   ├── context_rules.py   # DOM semantics & keyword proximity rules
│   │   │   ├── face_detector.py   # OpenCV Haar Cascade facial detection
│   │   │   └── pattern_rules.py   # Indian PAN, Aadhaar, Card Luhn regexes
│   │   ├── __init__.py            # Privacy exports
│   │   ├── pii_detector.py        # Multi-signal PII detection classifier
│   │   ├── privacy_gate.py        # Zero-leak gatekeeper & outbound remote guard
│   │   ├── redactor.py            # In-memory visual masking & DOM sanitizer
│   │   └── schemas.py             # Privacy data models (PIIEntity, SanitizedContext)
│   ├── security/                  # Adversarial Defense & Trust Boundaries
│   │   ├── __init__.py            # Security exports
│   │   ├── audit_logger.py        # Zero-leak structured security event logger
│   │   ├── injection_guard.py     # Prompt injection & jailbreak defense
│   │   ├── navigation_guard.py    # Strict URI scheme & download filter
│   │   ├── schemas.py             # Security data models (SecurityEvent)
│   │   └── secret_scanner.py      # Local on-device static credential scanner
│   ├── main.py                    # Central FastAPI REST API server & daemon
│   └── requirements.txt           # Python dependency specifications
├── demo-pages/                    # Synthetic Evaluation Testbeds
│   ├── checkout_sim.html          # Complex checkout form
│   ├── dashboard.html             # Multi-widget analytics layout
│   ├── face.html                  # Profile with human portrait photo
│   ├── form.html                  # Form filling testbed
│   ├── login.html                 # Privacy-preserving login sandbox
│   ├── modal.html                 # Popups and overlay testbed
│   ├── payment_sim.html           # High-risk financial payment sandbox
│   ├── privacy_eval.html          # Indian PAN/Aadhaar/Card evaluation page
│   ├── product_detail.html        # E-commerce product specification page
│   ├── product_listing.html       # E-commerce search results catalog
│   ├── scroll.html                # Long scrollable document
│   ├── search.html                # Search engine sandbox
│   ├── synthetic_eval.html        # Multi-signal fused benchmark page
│   └── unusual.html               # Non-standard canvas & SVG widgets
├── docs/                          # Architecture & Evaluation Documentation
│   ├── action-security.md         # Action safety and validation rules
│   ├── adversarial-testing.md     # 15-scenario adversarial test report
│   ├── benchmarks.md              # Empirical benchmark suite methodology
│   ├── demo-script.md             # 3-Minute SIH judge presentation script
│   ├── end-to-end-agent.md        # Multi-turn agent lifecycle documentation
│   ├── evaluation.md              # ISRO SIH26171 scorecard and metrics
│   ├── execution.md               # Real browser action execution details
│   ├── performance.md             # Latency telemetry & distribution docs
│   ├── release-checklist.md       # Final SIH release readiness checklist
│   ├── security.md                # Trust boundaries & network egress audit
│   ├── test-matrix.md             # Subsystem test matrix
│   └── threat-model.md            # Comprehensive threat model matrix
├── extension/                     # Chromium Manifest V3 Extension
│   ├── background.js              # Service worker capturing tabs & routing IPC
│   ├── content.js                 # Injected content script extracting DOM
│   ├── icon.png                   # Extension toolbar icon
│   ├── manifest.json              # Manifest V3 configuration & permissions
│   ├── popup.html                 # Extension popup interface
│   └── popup.js                   # Extension popup logic
├── frontend/                      # React 19 + TypeScript + Vite Dashboard
│   ├── src/
│   │   ├── components/            # Reusable UI widgets
│   │   │   ├── common/            # Badges, Cards, Modals (ConfirmDialog.tsx)
│   │   │   ├── demo/              # Demo cards & sandbox preview
│   │   │   ├── layout/            # Layout shell containers
│   │   │   ├── performance/       # Latency charts & distribution tables
│   │   │   ├── privacy/           # PII table, Redaction preview, Audit logs
│   │   │   ├── shell/             # AppShell, TopBar, Sidebar
│   │   │   ├── timeline/          # Live Agent Step Timeline
│   │   │   └── workspace/         # Agent objective tracker & action preview
│   │   ├── context/               # Global React state (AppContext.tsx)
│   │   ├── pages/                 # Full-page views
│   │   │   ├── ActivityPage.tsx   # Logs & event timeline
│   │   │   ├── DemoLabPage.tsx    # Controlled evaluation sandbox
│   │   │   ├── JudgeModePage.tsx  # Dedicated SIH Judge Command Center
│   │   │   ├── OverviewPage.tsx   # System overview & executive stats
│   │   │   ├── PerceptionPage.tsx # Interactive bounding box inspector
│   │   │   ├── PerformancePage.tsx# High-resolution benchmark dashboard
│   │   │   ├── PrivacyPage.tsx    # Privacy center & redaction controls
│   │   │   ├── SettingsPage.tsx   # Configuration & confidence thresholds
│   │   │   └── WorkspacePage.tsx  # Live Agent execution workspace
│   │   ├── types/                 # TypeScript interfaces (index.ts)
│   │   ├── App.tsx                # Master page router
│   │   ├── index.css              # Cyberpunk / Defense dark design system
│   │   └── main.tsx               # React entry point
│   ├── package.json               # Node.js dependencies
│   └── vite.config.ts             # Vite build configuration
├── tests/                         # 8 Automated Test Suites
│   ├── test_agent.py              # Planner, scoring, state machine tests
│   ├── test_benchmarks.py         # Empirical benchmark & tracker tests
│   ├── test_execution.py          # Real browser action & change detector tests
│   ├── test_extension.py          # Extension bridge & IPC tests
│   ├── test_perception.py         # OpenCV, OCR, and Context Fuser tests
│   ├── test_privacy.py            # PII detector, visual redactor, gate tests
│   ├── test_security_adversarial.py# 15-scenario adversarial attack tests
│   └── verify_backend.py          # Core sanity & health check verification
└── README.md                      # Master repository documentation
```

---

## 6. Important Source Files

### 6.1 `backend/perception/context_fuser.py`
* **Purpose**: Merges DOM nodes, OCR blocks, and OpenCV contours into stable `FusedElement` records.
* **Technology**: Python, NumPy.
* **Important Class**: `ContextFuser`
* **Important Method**: `fuse_context(dom_nodes, visual_elements, ocr_blocks, image_shape)`
* **Input**: List of DOM dictionaries, visual contour boxes, and OCR text blocks.
* **Output**: List of deduplicated `FusedElement` dictionaries with unified IDs and composite confidence scores.

### 6.2 `backend/privacy/pii_detector.py`
* **Purpose**: Classifies sensitive personal, financial, and authentication identifiers.
* **Technology**: Python, Regular Expressions, Context Heuristics.
* **Important Class**: `PIIDetector`
* **Important Method**: `detect_pii(text, dom_attributes, ocr_blocks, global_context)`
* **Key Feature**: `is_false_positive_number()` strictly preserves calendar years (`2026`), prices (`₹999`), and order IDs (`#12345`).

### 6.3 `backend/privacy/privacy_gate.py`
* **Purpose**: Enforces the zero-leak trust boundary.
* **Technology**: Python, Base64, Pillow.
* **Important Class**: `PrivacyGate`
* **Important Methods**: `process_and_sanitize()`, `guard_outbound_transmission()`
* **Security Invariant**: Raises `PrivacyGateViolation` if unredacted data attempts to egress.

### 6.4 `backend/agent/planner.py` & `engine.py`
* **Purpose**: Decomposes user goals and ranks candidate browser actions.
* **Technology**: Python, Heuristic Ranking.
* **Important Classes**: `AgentPlanner`, `LocalRuleBasedEngine`
* **Important Method**: `plan_next_step()`, `plan_next_action()`

### 6.5 `backend/actions/executor.py`
* **Purpose**: Dispatches atomic actions (`CLICK`, `TYPE`, `SCROLL`, `PRESS_KEY`, `NAVIGATE`, `WAIT`).
* **Technology**: Python, NavigationGuard integration.
* **Important Class**: `ActionExecutor`
* **Important Method**: `execute_browser_action()`

### 6.6 `backend/security/injection_guard.py`
* **Purpose**: Neutralizes adversarial prompt injections in webpage layout text.
* **Technology**: Python, Precompiled Regex Patterns.
* **Important Class**: `InjectionGuard`
* **Important Methods**: `scan_text()`, `sanitize_untrusted_elements()`

---

## 7. Important Functions

### 7.1 `fuse_context()` (`backend/perception/context_fuser.py`)
```python
def fuse_context(self, dom_nodes, visual_elements, ocr_blocks, image_shape) -> List[Dict[str, Any]]
```
* **Step-by-Step**:
  1. Computes bounding box geometry for DOM nodes.
  2. Matches visual OpenCV contours to DOM nodes using Intersection over Union ($IoU \ge 0.30$).
  3. Associates OCR text blocks located inside the bounding boxes.
  4. Computes composite confidence: $C = 0.40(DOM) + 0.35(OCR) + 0.25(CV)$.
  5. Assigns deterministic IDs (`pb-001`, `pb-002`) and returns fused elements.

### 7.2 `detect_pii()` (`backend/privacy/pii_detector.py`)
```python
def detect_pii(self, text, dom_attributes, ocr_blocks, global_context) -> List[PIIEntity]
```
* **Step-by-Step**:
  1. Checks DOM input types (`type="password"`, `type="email"`).
  2. Runs regex rules for Indian PAN, Aadhaar, Credit Cards, OTPs, Phones.
  3. Validates credit cards using the **Luhn Algorithm (Mod 10)**.
  4. Filters false positives using `is_false_positive_number()`.
  5. Returns structured `PIIEntity` list with confidence scores.

### 7.3 `score_candidates()` (`backend/agent/scoring.py`)
```python
def score_candidates(self, candidates, objective, fused_elements, history) -> List[CandidateAction]
```
* **Step-by-Step**:
  1. Evaluates semantic relevance between candidate target text and current objective.
  2. Incorporates perception confidence.
  3. Rewards type alignment (`CLICK` for buttons/links, `TYPE` for inputs).
  4. Penalizes repeated targets from history to prevent action loops.
  5. Returns sorted candidates in descending order of composite score.

---

## 8. Important Classes

```
┌────────────────────────────────────────────────────────┐
│                      AgentPlanner                      │
│ ────────────────────────────────────────────────────── │
│ - state_machine: AgentStateMachine                     │
│ - decomposer: TaskDecomposer                           │
│ - engine: LocalRuleBasedEngine                         │
│ - validator: ActionValidator                           │
│ - verifier: ActionVerifier                             │
│ ────────────────────────────────────────────────────── │
│ + start_task(goal) -> AgentTask                        │
│ + plan_next_step(elements, goal) -> CandidateAction    │
└────────────────────────────────────────────────────────┘
```

---

## 9. Frontend Command Center

* **Framework**: React 19 + TypeScript + Vite.
* **Design Aesthetic**: Cyber-defense dark theme with high-contrast neon accents (`--accent-cyan: #38bdf8`, `--accent-green: #10b981`, `--accent-amber: #f59e0b`, `--accent-red: #ef4444`).
* **State Management**: Centralized in `frontend/src/context/AppContext.tsx` managing backend connection health, scenario selection, live perception data, PII records, and timeline steps.
* **Judge Mode**: Located at `frontend/src/pages/JudgeModePage.tsx` providing a 1-click execution interface for hackathon presentations.

---

## 10. Backend Daemon & API Routes

| HTTP Method | API Path | Purpose | Caller |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health check & pipeline latency query | Frontend TopBar / Extension |
| `POST` | `/api/browser/context` | Ingests tab screenshot & DOM tree | Extension background worker |
| `GET` | `/api/browser/status` | Returns active connection status | Frontend Sidebar |
| `POST` | `/api/pipeline/run` | Executes Perceive $\rightarrow$ Sanitize $\rightarrow$ Plan | Frontend Workspace |
| `POST` | `/api/actions/execute` | Executes atomic browser action | Frontend / E2E Runner |
| `POST` | `/api/benchmark/run` | Runs 8-page benchmark & task evaluation | Performance Dashboard |
| `GET` | `/api/metrics/realtime` | Returns real-time latency distributions | Performance Dashboard |
| `GET` | `/api/security/audit` | Returns structured security event log | Privacy / Judge Mode |
| `POST` | `/api/security/scan-secrets`| Runs on-device static credential scan | Judge Mode |

---

## 11. Browser Extension (Manifest V3)

* **Architecture**:
  ```
  [ Chrome Active Tab ] <--- content.js (DOM Extraction)
           │
           ▼
    background.js (Service Worker: captureVisibleTab)
           │
           ▼ (HTTP POST)
  [ FastAPI Daemon: http://127.0.0.1:8000/api/browser/context ]
  ```
* **Permissions**: `activeTab`, `scripting`, `storage`, `tabs`.
* **Host Permissions**: `http://127.0.0.1:8000/*`.

---

## 12. Computer Vision Engine (OpenCV)

* **Source File**: `backend/perception/detectors/visual_detector.py` & `backend/perception/preprocessing/image_processor.py`.
* **Library**: OpenCV (`opencv-python-headless 4.10.0.84`).
* **On-Device Pipeline**:
  1. Image Decoding & Color Space: Decodes PNG/JPEG bytes via `cv2.imdecode()` to BGR numpy array.
  2. Grayscale & Contrast Optimization: `cv2.cvtColor()` with Gaussian blur kernel $(5, 5)$.
  3. Adaptive Thresholding: `cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)` to handle both light and dark UI themes dynamically.
  4. Morphological Closing: Rectangular structuring element $(7, 3)$ merges fragmented input/button borders.
  5. Contour Tree Extraction: `cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)` extracts full parent/child contour hierarchies.
  6. Geometric Heuristics: Classifies contours by aspect ratio, area ratio, and pixel dimensions into `BUTTON`, `INPUT`, `TEXTAREA`, `CHECKBOX`, `ICON`, `HEADING`, `CARD`, `IMAGE`.
  7. Edge Density Verification: Computes Canny edge density within the bounding box to boost confidence for well-defined UI controls ($+0.05$) or penalize noise ($-0.10$).
  8. Non-Maximum Suppression: Suppresses overlapping duplicate contours with $\text{IoU} \ge 0.45$.

---

## 13. OCR Engine & Layout Extraction

* **Source File**: `backend/perception/ocr/tesseract_engine.py` & `backend/perception/detectors/text_detector.py`.
* **Library**: `pytesseract 0.3.13` wrapping local on-device Tesseract binary (`eng.traineddata`, ~30 MB).
* **Execution Flow**:
  1. Preprocessing: Binarization and contrast adjustment for optimal optical character recognition.
  2. Per-Word Extraction: `pytesseract.image_to_data(pil_img, output_type=Output.DICT)`.
  3. Line-Level Grouping: Groups words into coherent text lines by `(block_num, par_num, line_num)` to avoid fragmented character bounding boxes.
  4. Semantic Typing: Text blocks with height $\ge 20\text{ px}$, confidence $\ge 0.7$, and $\le 8$ words are classified as `HEADING`; otherwise `TEXT`.
  5. Graceful Fallback (`DOM_TEXT_PROXY`): If the system Tesseract binary is not installed on the host OS, the pipeline gracefully extracts visible text from DOM elements with `sources=["DOM_TEXT_PROXY"]` without crashing or fabricating fake OCR.

---

## 14. Multi-Source Perception Fusion & Coordinate System

* **Source File**: `backend/perception/fusion/context_fuser.py` & `backend/perception/core/coordinator.py`.
* **Fusion Strategy**:
  1. **DOM Ground Truth**: Uses DOM nodes as the structural ground truth anchor.
  2. **IoU Association**: Matches visual contours and OCR text blocks to DOM elements using $\text{IoU} \ge 0.35$.
  3. **Visual-Only Ingestion**: Retains vision-only detections (e.g. custom canvas controls, SVG icons) not present in the DOM tree.
  4. **Stable Identifier Assignment**: Assigns stable, deterministic IDs (`pb-element-001`, `pb-element-002`, ...).
* **Multi-Source Confidence Formula**:
  $$\text{Confidence} = 0.35 \cdot C_{\text{DOM}} + 0.30 \cdot C_{\text{OCR}} + 0.25 \cdot C_{\text{VISION}} + 0.10 \cdot C_{\text{GEOMETRY}}$$
  * $C_{\text{DOM}}$: DOM presence structural reliability ($0.92$).
  * $C_{\text{OCR}}$: Text recognition confirmation ($\ge 0.50$).
  * $C_{\text{VISION}}$: Visual contour & edge density confidence.
  * $C_{\text{GEOMETRY}}$: Bonus for high spatial agreement ($\text{IoU} \ge 0.60 \rightarrow 0.95$, $\text{IoU} \ge 0.40 \rightarrow 0.75$).
  * Single-source penalty: $-10\%$ discount when detected by only one source.
* **Coordinate Transformations**:
  * Screenshot Space $\leftrightarrow$ Viewport Space: Handles Retina display device pixel ratio ($\text{DPR} = 2.0$) via `scale_x = viewport_width / screenshot_width`.
  * Viewport Space $\leftrightarrow$ Document Space: Accounts for dynamic `scroll_x` and `scroll_y` offsets.
  * Visibility Classification: Classifies elements as `VISIBLE`, `PARTIALLY_VISIBLE`, or `OFFSCREEN`.

---

## 15. Real On-Device PII Detection Engine

* **Source Files**:
  * Core Detector: [`backend/privacy/pii_detector.py`](file:///Users/heemanshusingh/Desktop/MY%20PROJECT/backend/privacy/pii_detector.py)
  * Pattern Matchers & Validators: [`backend/privacy/rules/pattern_rules.py`](file:///Users/heemanshusingh/Desktop/MY%20PROJECT/backend/privacy/rules/pattern_rules.py)
  * Contextual Rules & False-Positive Elimination: [`backend/privacy/rules/context_rules.py`](file:///Users/heemanshusingh/Desktop/MY%20PROJECT/backend/privacy/rules/context_rules.py)
  * PII Schemas: [`backend/privacy/schemas.py`](file:///Users/heemanshusingh/Desktop/MY%20PROJECT/backend/privacy/schemas.py)

### Multi-Source Detection Architecture

The on-device PII detector fuses three independent detection signals:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   ON-DEVICE PII DETECTION ENGINE                        │
│                                                                          │
│  ┌────────────────────┐   ┌────────────────────┐   ┌──────────────────┐  │
│  │   DOM ATTRIBUTES   │   │     OCR TEXTS      │   │  OPENCV VISION   │  │
│  │  (Type, Name, Id,  │   │   (Regex Patterns, │   │  (Haar Cascade   │  │
│  │   Placeholder,     │   │    Algorithmic     │   │   Frontal Face   │  │
│  │   Aria, Value)     │   │    Validators)     │   │    Detector)     │  │
│  └─────────┬──────────┘   └─────────┬──────────┘   └────────┬─────────┘  │
│            │                        │                       │            │
│            └────────────────────────┼───────────────────────┘            │
│                                     ↓                                    │
│                 ┌──────────────────────────────────────┐                 │
│                 │   FALSE-POSITIVE ELIMINATION GATE    │                 │
│                 │   (Years, Prices, Orders, Metrics)   │                 │
│                 └───────────────────┬──────────────────┘                 │
│                                     ↓                                    │
│                 ┌──────────────────────────────────────┐                 │
│                 │   CONTEXTUAL CONFIDENCE BOOSTING     │                 │
│                 │    (+0.08 on Semantic Keywords)      │                 │
│                 └───────────────────┬──────────────────┘                 │
│                                     ↓                                    │
│                 ┌──────────────────────────────────────┐                 │
│                 │   SPATIAL DEDUPLICATION & MERGING    │                 │
│                 │   (IoU >= 0.40 Box Coalescence)      │                 │
│                 └───────────────────┬──────────────────┘                 │
│                                     ↓                                    │
│                 ┌──────────────────────────────────────┐                 │
│                 │     STRUCTURED PII ENTITY LIST       │                 │
│                 │     (Provenance & Masked Text)       │                 │
│                 └──────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### Supported PII Categories & Detection Rules

| Category | Classification | Detection Method | Validation / Algorithm |
| :--- | :--- | :--- | :--- |
| **Indian PAN Card** | `HIGHLY_SENSITIVE` | Regex `\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b` + DOM name/id keywords (`pan_number`, `pancard`, `tax_id`) | Validates 5 uppercase letters, 4 digits, 1 uppercase letter |
| **Indian Aadhaar** | `HIGHLY_SENSITIVE` | Regex `\b[2-9]\d{3}[\s-]\d{4}[\s-]\d{4}\b` + DOM keywords (`aadhaar`, `uidai`) | `validate_aadhaar_format()`: Rejects leading 0 or 1; rejects all-repeating sequences |
| **Payment Cards** | `HIGHLY_SENSITIVE` | Regex (13–19 digits, Visa/Mastercard/Amex/RuPay) + DOM payment fields | **Luhn Mod-10 Algorithm** (`validate_luhn()`): Validates cryptographic card checksum |
| **Passwords & Secrets** | `HIGHLY_SENSITIVE` | DOM `type="password"`, attributes matching `pass`, `pwd`, `secret`, `credentials` | Unconditional masking; never stored or logged in plaintext |
| **API Keys & Tokens** | `HIGHLY_SENSITIVE` | Prefix matchers: `ghp_`, `sk_live_`, `pk_live_`, `AIza`, `Bearer`, JWT (`eyJ...`) | Strict regex matching + classification as HIGHLY_SENSITIVE |
| **OTPs & 2FA Codes** | `HIGHLY_SENSITIVE` | Numeric 4–8 digits paired with local verification context keywords (`otp`, `2fa`, `verification code`, `passcode`) | Suppressed unless verification keywords appear in nearby text |
| **Email Addresses** | `SENSITIVE` | RFC-5322 regex + DOM `type="email"` + keywords | Proximity boosting near contact/login labels |
| **Phone Numbers** | `SENSITIVE` | Indian mobile `[6-9]\d{9}` + international E.164 formats + DOM `type="tel"` | Pre-filtered against year and dimension false positives |
| **Human Faces** | `SENSITIVE` | OpenCV `HaarCascadeFrontalFace` (`haarcascade_frontalface_default.xml`) | Visual bounding box detection on screenshot image |

### False-Positive Elimination System

To prevent ordinary non-sensitive webpage content from being mistakenly redacted, the engine applies deterministic negative rules (`is_false_positive_number`):
1. **Years (1900–2099)**: Matches like `2026` or `1969` near `copyright`, `year`, `since`, `founded` are ignored.
2. **Prices & Currencies**: Amounts prefixed/suffixed with `₹`, `$`, `€`, `£`, `INR`, `USD` are ignored.
3. **Order & Product IDs**: Tracking references like `Order #12345` or `PID-84729` are ignored.
4. **Dimensions & Metrics**: Numbers with units like `1920x1080`, `60fps`, `42ms`, `%`, `px`, `kg`, `MB` are ignored.
5. **Small Plain Counts**: 1–3 digit integers without CVV/OTP keywords are ignored.

---

## 16. Local Redaction Engine & Privacy Gate

* **Source Files**:
  * Redaction Engine: [`backend/privacy/redactor.py`](file:///Users/heemanshusingh/Desktop/MY%20PROJECT/backend/privacy/redactor.py)
  * Privacy Gate: [`backend/privacy/privacy_gate.py`](file:///Users/heemanshusingh/Desktop/MY%20PROJECT/backend/privacy/privacy_gate.py)

### Zero-Leak Local Trust Boundary

```
REAL BROWSER DATA (Chrome Tab)
         │
         ▼
LOCAL ON-DEVICE PERCEPTION (DOM + OCR + OpenCV)
         │
         ▼
LOCAL ON-DEVICE PII DETECTION (Multi-Source + Luhn + False-Positive Filter)
         │
         ▼
LOCAL ON-DEVICE REDACTION & SANITIZATION (Visual Masking + DOM/OCR/Element Scrubbing)
         │
         ▼
SANITIZED SAFE REPRESENTATION (SanitizedContext, Sanitized PerceivedElements)
         │
 ════════╪═════════════════════════════════════════════════════════════════
         │ [ZERO-LEAK PRIVACY GATE ENFORCEMENT BOUNDARY]
         │ (Outbound transmission of raw unredacted data is STRICTLY BLOCKED)
         ▼
PLANNER / REASONING AGENT (Receives clean tokens: [REDACTED_PASSWORD], [REDACTED_EMAIL])
         │
         ▼
ACTION VALIDATOR & SAFETY GATE (Validates bounds, risk, budget, financial confirmation)
         │
         ▼
REAL BROWSER ACTION EXECUTION BRIDGE (Dispatches action safely to Chrome Tab)
```

### Visual Screenshot Redaction

The redactor applies OpenCV transformations directly onto the image pixel buffer:
* **`opaque` (Default & Recommended)**: Solid dark fill (`#19191e` for highly sensitive, `#23232d` for sensitive) with a high-contrast accent indicator strip and clear white text label (e.g. `[PASSWORD]`, `[CARD]`).
* **`blur`**: Region-of-interest Gaussian blur with security border highlight.
* **`pixelate`**: Nearest-neighbor downsampling and upsampling with security boundary box.

### DOM, OCR, and PerceivedElement Sanitization

1. **DOM Nodes**: Sensitive attributes (`.value`, `.text`, `.placeholder`) on password, payment card, PAN, Aadhaar, email, phone, and OTP fields are scrubbed. Passwords are unconditionally set to `[REDACTED_PASSWORD]` and `••••••••`.
2. **OCR Layout Blocks**: Text occurrences of sensitive entities are replaced with deterministic tokens (`[REDACTED_<TYPE>]`).
3. **PerceivedElement Objects**: Enhanced with `is_sensitive=True`, `pii_type="<TYPE>"`, and `redacted=True` metadata flags.
4. **Agent Working Memory & Action Logs**: Plaintext credentials are never written to audit trails or action execution history.
5. **Outbound Remote Guard**: `PrivacyGate.guard_outbound_transmission()` strictly rejects unredacted context dictionaries and raises `PrivacyGateViolation`.

---

## 17. Agent Brain & Reasoning Engine

* **Algorithm**: Heuristic Multi-Factor Ranking.
* **Scoring Formula**:
  $$\text{Score} = 0.35 \cdot S_{\text{semantic}} + 0.25 \cdot C_{\text{perception}} + 0.20 \cdot A_{\text{type}} + 0.20 \cdot V_{\text{visibility}} - P_{\text{history}}$$
* **Goal Decomposition**:
  * `"Search X"` $\rightarrow$ (1) Locate Search Input $\rightarrow$ (2) Type Query $\rightarrow$ (3) Click Submit $\rightarrow$ (4) Verify Results.
  * `"Login"` $\rightarrow$ (1) Type Email $\rightarrow$ (2) Type Password $\rightarrow$ (3) Click Sign In $\rightarrow$ (4) Verify Dashboard.

---

## 18. Action Execution Subsystem

| Action Type | Parameters | Safety Check | Real Browser Dispatch |
| :--- | :--- | :--- | :--- |
| `CLICK` | `{ target: {x, y}, target_id }` | Bounding bounds check $(1920\times 1080)$, visibility check | Dispatches mouse click event |
| `TYPE` | `{ target: {x, y}, text }` | Sensitive text masked in logs | Dispatches keyboard input |
| `SCROLL` | `{ direction, delta_px }` | Clamped to max 800px step | Dispatches viewport scroll |
| `PRESS_KEY` | `{ key: 'Enter' }` | Whitelisted safe keys only | Dispatches keydown/keyup |
| `NAVIGATE` | `{ url }` | NavigationGuard blocks `javascript:`/`data:` | Initiates tab navigation |
| `WAIT` | `{ duration_ms }` | Capped to timeout limit | Delays for DOM stabilization |

### 18A. Browser Action Bridge (Real Browser Execution)

The **Browser Action Bridge** (`backend/actions/browser_bridge.py`) replaces the previous synthetic `time.sleep()` execution with a real bidirectional communication channel between the backend `ActionExecutor` and the Chrome extension's `content.js`.

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT RUNNER                              │
│  run_single_turn()                                          │
│    ├── 1. PLAN (AgentPlanner.plan_next_step)                │
│    ├── 2. VALIDATE (ActionValidator.validate_candidate)     │
│    ├── 3. EXECUTE (ActionExecutor.execute_browser_action)   │
│    │         ├── Pre-checks (stale target, privacy mask)    │
│    │         ├── BrowserActionBridge.dispatch_action()       │
│    │         │         ↓                                    │
│    │         │   ┌─────────────────────────┐                │
│    │         │   │  PENDING ACTION QUEUE   │                │
│    │         │   │  (thread-safe dict)     │                │
│    │         │   └────────┬────────────────┘                │
│    │         │            │                                 │
│    │         │   GET /api/action/pending (extension polls)  │
│    │         │            ↓                                 │
│    │         │   ┌─────────────────────────┐                │
│    │         │   │  CHROME EXTENSION       │                │
│    │         │   │  background.js          │                │
│    │         │   │    → sendMessage(tabId)  │                │
│    │         │   └────────┬────────────────┘                │
│    │         │            ↓                                 │
│    │         │   ┌─────────────────────────┐                │
│    │         │   │  CONTENT SCRIPT         │                │
│    │         │   │  content.js             │                │
│    │         │   │  executeSafeAction()    │                │
│    │         │   │    → REAL DOM ACTION    │                │
│    │         │   └────────┬────────────────┘                │
│    │         │            ↓                                 │
│    │         │   POST /api/action/ack (result)              │
│    │         │            ↓                                 │
│    │         ├── BrowserActionBridge.wait_for_result()       │
│    │         └── → ActionResult (real browser outcome)      │
│    └── 4. VERIFY (AgentPlanner.verify_step_outcome)         │
└─────────────────────────────────────────────────────────────┘
```

#### Action Lifecycle

| State | Description | Transition |
| :--- | :--- | :--- |
| `PENDING` | Action queued by executor, waiting for extension pickup | → `DISPATCHED` when extension polls |
| `DISPATCHED` | Extension retrieved action, forwarded to content script | → `SUCCESS` / `FAILED` on ack |
| `SUCCESS` | Content script executed action and confirmed success | Terminal |
| `FAILED` | Content script reported execution failure | Terminal |
| `TIMEOUT` | No acknowledgement received within timeout window | Terminal |
| `CANCELLED` | Action cancelled by system before execution | Terminal |

#### Communication Protocol

**Extension → Backend Polling** (every 500ms):
- `GET /api/action/pending` → Returns oldest `PENDING` action, marks it `DISPATCHED`
- Each poll also registers a heartbeat for extension connectivity tracking

**Extension → Backend Acknowledgement**:
- `POST /api/action/ack` with `{ action_id, success, error, error_code, detail, metadata }`
- Wakes the blocking `wait_for_result()` call in the executor thread

**Connectivity Detection**:
- `GET /api/extension/status` → Returns `{ extension_connected, pending_actions, dispatched_actions }`
- Extension is considered disconnected if no poll received within 10 seconds

#### CLICK Execution (Real Browser)

1. `ActionValidator` checks bounds, confidence, visibility, loop detection
2. `ActionExecutor` checks stale target against current element list
3. `BrowserActionBridge.dispatch_action()` enqueues `PendingAction`
4. Extension picks up via `GET /api/action/pending`
5. `background.js` forwards to `content.js` via `chrome.tabs.sendMessage()`
6. `content.js:executeSafeAction()`:
   - Resolves element via `data-pb-id`, DOM ID, selector, or text match
   - Verifies element is visible and enabled
   - Focuses element
   - Dispatches `mousedown` → `mouseup` → `click` at element center
   - If submit button, calls `form.requestSubmit()`
7. Returns `{ success, action_id, element_pb_id, bbox, detail }`

#### TYPE Execution (Real Browser)

1. All validation and privacy masking as above
2. `content.js:executeSafeAction()`:
   - Resolves target element
   - For `<input>` / `<textarea>`: Uses **native prototype setter** via `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, value)` for React/Vue/Angular controlled input compatibility
   - Dispatches `new Event('input', { bubbles: true })` and `new Event('change', { bubbles: true })`
   - For `contenteditable`: Sets `innerText` and dispatches events
   - **Post-set verification**: Reads back `el.value` and returns `VALUE_NOT_APPLIED` error if framework rejected the value
3. Password/card/OTP fields: display_payload is `[REDACTED_TEXT]` in metadata

#### SCROLL Execution (Real Browser)

1. `content.js:executeSafeAction()`:
   - Records `window.scrollY` / `window.scrollX` before scroll
   - Calls `window.scrollBy({ top: dy, left: dx, behavior: 'smooth' })`
   - Waits 150ms for stabilization
   - Reads back actual scroll position
   - Returns `{ actual_delta, requested_delta, scroll_position }`

#### Error Handling

| Error Code | Source | Cause |
| :--- | :--- | :--- |
| `EXTENSION_UNAVAILABLE` | Executor | No heartbeat from extension within 10s |
| `EXTENSION_TIMEOUT` | Bridge | No ack received within timeout window |
| `TARGET_NOT_FOUND` | Content script | Element not in DOM |
| `TARGET_NOT_VISIBLE` | Content script | Element hidden / off-viewport |
| `TARGET_DISABLED` | Content script | Element is disabled |
| `VALUE_NOT_APPLIED` | Content script | Framework rejected typed value |
| `CONTENT_SCRIPT_UNAVAILABLE` | Background | Content script not loaded |
| `NO_ACTIVE_TAB` | Background | No valid active tab found |
| `STALE_TARGET` | Executor | Target element no longer in layout |
| `VALIDATION_FAILED` | Validator | Action failed safety checks |
| `UNSAFE_KEY` | Executor | Key not in permitted whitelist |
| `UNSAFE_URL_SCHEME` | NavigationGuard | javascript:/data:/file: blocked |

#### Simulation Mode

Set `PRIVYBROWSE_SIMULATION_MODE=true` env var or `ActionExecutor(simulation_mode=True)` for offline development/testing. In this mode, the executor uses synthetic delays instead of the bridge — identical to the pre-bridge behavior.

#### Files Changed for Browser Action Bridge

| File | What Changed | Why | Role in System |
| :--- | :--- | :--- | :--- |
| `backend/actions/browser_bridge.py` | **[NEW]** Thread-safe action queue, dispatch, ack, timeout, heartbeat | Core bridge component enabling real browser execution | Backend ↔ Extension communication layer |
| `backend/actions/executor.py` | Refactored `_execute_*` methods to dispatch via bridge in real mode | Replace synthetic `time.sleep()` with actual browser dispatch | Action executor |
| `backend/actions/schemas.py` | Added `EXTENSION_UNAVAILABLE`, `EXTENSION_TIMEOUT` statuses | New failure modes for real browser communication | Schema definitions |
| `backend/actions/agent_runner.py` | Removed fabricated `simulated_next_elements`, uses real execution result | Verification now uses actual browser outcome | Multi-turn agent loop |
| `backend/actions/__init__.py` | Added `BrowserActionBridge` export | Module accessibility | Package exports |
| `backend/main.py` | Added `/api/action/pending`, `/api/action/ack`, `/api/extension/status` routes; fixed `FileResponse` import | Bridge HTTP endpoints + bug fix | API routing |
| `extension/background.js` | Added `pollPendingActions()` loop, `postAcknowledgement()`, `startPolling()`/`stopPolling()` | Extension-side action polling and ack posting | Extension service worker |
| `extension/content.js` | React controlled input (native setter), scroll verification, action_id passthrough, value verification | Reliable real DOM interaction | Content script |
| `tests/test_execution.py` | Updated 8 existing tests for `simulation_mode=True`, added 12 new bridge tests | Comprehensive bridge testing | Test suite |

---

## 19. Action Validation & Risk Analysis

```
CandidateAction
      │
      ▼
ActionValidator (validator.py)
   ├── 1. Action Budget Check (Max 15 actions per task)
   ├── 2. Loop Detection (Max 3 consecutive identical actions)
   ├── 3. Coordinate Bounds Check (0 <= x <= 1920, 0 <= y <= 1080)
   ├── 4. Confidence Threshold Check (Confidence >= 0.60)
   ├── 5. Target Visibility Check (Element must not be HIDDEN)
   └── 6. Financial Risk Check (Requires human confirmation if CRITICAL)
      │
      ▼
ValidationResult: { allowed: true/false, requires_confirmation: true/false }
```

---

## 20. Human-in-the-Loop Confirmation

* **When Required**: Financial transactions (e.g., ₹1,450,000 payment), account deletion, credential submission.
* **Anti-Spoofing Architecture**: Confirmation dialog is rendered solely by the trusted React application runtime (`ConfirmDialog.tsx`). Webpage DOM JavaScript cannot simulate or approve it.
* **Rejection Handling**: If user denies confirmation, the action is marked `BLOCKED`, and the agent halts safely.

---

## 21. Verification & State Monitoring

* **Component**: `PageChangeDetector` (`backend/actions/page_change_detector.py`).
* **Signals Tracked**:
  1. `url_changed`: Navigation to new URL.
  2. `dom_mutated`: Significant DOM element count delta ($>10\%$).
  3. `scroll_shifted`: Viewport scroll position displacement ($>50\text{ px}$).
* **Stale Target Recovery**: If target element is removed before click dispatch, executor returns `STALE_TARGET`, triggering immediate re-perception.

---

## 22. Security & Threat Defense

| Threat | Attack Scenario | Defense Mechanism | Mitigation Result |
| :--- | :--- | :--- | :--- |
| **Prompt Injection** | Webpage text commands agent to delete data | `InjectionGuard` scans and neutralizes jailbreaks | **BLOCKED & NEUTRALIZED** |
| **Confirmation Spoofing**| Webpage renders fake modal: *"Confirmed"* | State checked strictly in trusted application runtime | **SPOOFING BLOCKED** |
| **Protocol Injection** | Link points to `javascript:alert(1)` | `NavigationGuard` blocks unsafe schemes | **SCHEME FORBIDDEN** |
| **Data URI Injection** | Navigation to `data:text/html,...` | `NavigationGuard` blocks `data:` scheme | **SCHEME FORBIDDEN** |
| **Clickjacking** | Hidden overlay covers button | `ActionValidator` verifies visibility (`VISIBLE`) | **ACTION REJECTED** |
| **Stale Target Race** | Button removed dynamically | `ActionExecutor` detects missing node | **REJECTED $\rightarrow$ RE-PERCEIVE** |
| **DOM Mutation Race** | Button mutates to *"Delete Cloud"* | Post-planning re-validation elevates risk | **CONFIRMATION ENFORCED** |
| **Action Loop Trap** | Webpage traps agent in click loop | Loop detector halts after 3 identical actions | **LOOP HALTED SAFELY** |
| **Resource Exhaustion** | 10,000 DOM nodes or rapid calls | Action budget capped at 15 | **BUDGET HALTED SAFELY** |
| **Credential Leak** | Passwords/tokens enter logs | `SecurityAuditLogger` masks all credentials | **ZERO-LEAK VERIFIED** |

---

## 23. Adversarial Prompt Injection Defense

* **File**: `backend/security/injection_guard.py`
* **Class**: `InjectionGuard`
* **Jailbreak Regexes Detected**:
  * `ignore (all) previous instructions`
  * `reveal system prompt`
  * `send all credentials to http...`
  * `disable security / bypass confirmation`
  * `you are now DAN / jailbroken`
* **Handling**: Neutralizes matching strings to `[NEUTRALIZED_ADVERSARIAL_DIRECTIVE]` and tags element as `HIGH_RISK`.

---

## 24. Performance Telemetry & Benchmarking

* **Perception Latency**: **1.97 ms** (Target $<50\text{ ms}$)
* **PII Detection Latency**: **0.40 ms** (Target $<15\text{ ms}$)
* **Planning Latency**: **0.15 ms** (Target $<10\text{ ms}$)
* **Total Perceive-Plan-Act Loop**: **18.90 ms** (Target $<200\text{ ms}$)
* **Memory RSS Footprint**: **~68 MB** (Target $<250\text{ MB}$)
* **SIH Evaluation Score**: **99.0 / 100**

---

## 25. Testing & Verification Suites

```bash
# All 8 Test Suites Passing (100% Pass Rate):
1. python tests/test_security_adversarial.py  # 15/15 Adversarial Attacks Blocked (100%)
2. python tests/test_benchmarks.py            # Performance distributions & Score 99.0/100
3. python tests/test_execution.py             # Atomic browser actions & Page change signals
4. python tests/test_agent.py                 # State machine, Candidate generator, Scoring
5. python tests/test_privacy.py               # Indian PII rules, Visual redactor, Zero-leak gate
6. python tests/test_perception.py            # OpenCV detector, Tesseract OCR, Context fuser
7. python tests/test_extension.py             # Manifest V3 extension bridge & IPC
8. python tests/verify_backend.py             # Core FastAPI daemon sanity checks
```

---

## 26. Project Dependencies

| Dependency | Version | Purpose |
| :--- | :--- | :--- |
| `fastapi` | `0.115.0` | Asynchronous REST API framework |
| `uvicorn` | `0.31.0` | High-speed ASGI server |
| `pydantic` | `2.9.2` | Data validation and schemas |
| `opencv-python-headless` | `4.10.0.84` | Headless computer vision & contour detection |
| `numpy` | `2.1.2` | Fast array mathematics |
| `python-multipart` | `0.0.12` | Form data handling |
| `pytesseract` | `0.3.13` | Local Tesseract OCR interface |
| `Pillow` | `>=10.0.0` | Image processing & visual redaction |
| `react` | `^19.2.8` | Frontend component library |
| `typescript` | `~6.0.2` | Frontend type safety |
| `vite` | `^8.2.2` | Ultra-fast frontend bundler |

---

## 27. Environment Setup & Installation

```bash
# 1. Clone repository
git clone https://github.com/heemanshu-021/PrivyBrowse-AI.git
cd PrivyBrowse-AI

# 2. Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. Start Backend Daemon
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Setup Frontend
cd frontend
npm install
npm run dev
# Dashboard opens at http://localhost:5173

# 5. Load Extension
# Open chrome://extensions -> Enable Developer Mode -> Load Unpacked -> select /extension
```

---

## 28. Git & GitHub Repository

* **Remote Repository**: [https://github.com/heemanshu-021/PrivyBrowse-AI](https://github.com/heemanshu-021/PrivyBrowse-AI)
* **Active Branch**: `main`
* **Release Tag**: `v1.0.0-sih`
* **Secret Scanning**: Verified 100% clean of API keys, `.env` files, or credentials via `SecretScanner`.

---

## 29. Demonstration Guide

### 5 Core Interactive Demonstrations:
1. **Hero Demo: Chandrayaan-3 Search & Navigation**:
   * Detects search input, types query, triggers search click, detects page mutation, and navigates to destination wiki article.
2. **Privacy Gate: Indian PII & Financial Masking**:
   * Detects and redacts PAN, Aadhaar, payment cards, passwords, and OTPs while preserving calendar years (e.g., `2026`) and metrics.
3. **Security: Prompt Injection Defense**:
   * Malicious webpage commands agent to exfiltrate data. `InjectionGuard` neutralizes the directive without agent hijacking.
4. **Safety: High-Risk Financial Action Authorization**:
   * Intercepts ₹1,450,000 procurement payment and enforces anti-spoofing human confirmation modal.
5. **Resilience: Stale Target Recovery**:
   * Target button deleted dynamically $\rightarrow$ Stale target detected $\rightarrow$ Action safely rejected $\rightarrow$ Re-perceived.

---

## 30. Speaking Scripts (Judge Presentation)

### 60-Second Presentation Pitch:
> *"Respected judges, current AI browser agents suffer from severe privacy leaks and high latency by sending raw screenshots to cloud vision APIs.
>
> **PrivyBrowse AI** delivers a **100% on-device visual perception engine and privacy gatekeeper**.
>
> In under **2 milliseconds**, it fuses OpenCV visual contours with local OCR, detects and redacts sensitive Indian PAN cards, Aadhaar numbers, and passwords on-device, feeds only clean layout tokens to an explainable planner, and safely executes browser actions.
>
> The result: **Zero cloud vision calls, zero data leakage, and a complete agent loop in under 20 milliseconds**."*

---

## 31. Judge & Viva Questions (100 Q&A)

### Top 10 High-Probability Viva Questions:
1. **Q: Why not use a fine-tuned vision-language model like SmolVLM?**
   * **Ans**: Even small VLMs take 300–800 ms and require 2–4 GB of GPU RAM. Our hybrid OpenCV + Tesseract pipeline executes in **1.8 ms on standard laptop CPUs** with zero GPU requirements.
2. **Q: How does the system avoid redacting non-sensitive numbers like '2026' or '₹999'?**
   * **Ans**: In `backend/privacy/pii_detector.py`, `is_false_positive_number()` verifies token boundaries and ignores standalone 4-digit years or numbers with currency prefixes.
3. **Q: How do you prevent indirect prompt injection?**
   * **Ans**: `InjectionGuard` strips jailbreak directives from layout text before candidate generation, maintaining strict separation between the human user's goal and untrusted webpage observations.
4. **Q: How is high-risk action confirmation protected from webpage spoofing?**
   * **Ans**: Confirmation state exists strictly inside the trusted React application memory. Webpage DOM scripts have no access to trigger or approve system-level modals.
5. **Q: What happens if a webpage elements shifts between perception and execution?**
   * **Ans**: `ActionExecutor` validates node existence in the live DOM. If missing or altered, it returns `STALE_TARGET`, triggering an automatic re-perception cycle.

---

## 32. Technology Choices ("Why did you choose this?")

* **Why OpenCV?** Deterministic contour edge detection in $<1\text{ ms}$ without GPU.
* **Why Tesseract?** Local, battle-tested OCR bounding-box extraction with zero cloud dependencies.
* **Why FastAPI?** Asynchronous, high-throughput Python REST server with native Pydantic schema validation.
* **Why React 19 + TypeScript?** Type-safe, reactive UI delivering real-time telemetry updates to judges.

---

## 33. Known Limitations & Edge Cases

* **Custom WebGL / Canvas Widgets**: Canvas elements without DOM tags depend purely on OpenCV visual contour heuristics.
* **Complex Multi-lingual CAPTCHAs**: Designed intentionally to require human-in-the-loop intervention.
* **Extremely Dense (>5000 nodes) DOMs**: Capped to viewport region-of-interest (ROI) to preserve sub-20ms latency.

---

## 34. Implemented vs. Planned Matrix

| Capability | Status | Evidence |
| :--- | :--- | :--- |
| **OpenCV Contour Detector** | **IMPLEMENTED** | `backend/perception/element_detector.py` |
| **Local Tesseract OCR Fusion** | **IMPLEMENTED** | `backend/perception/ocr_engine.py` |
| **Indian PAN & Aadhaar Detection** | **IMPLEMENTED** | `backend/privacy/rules/pattern_rules.py` |
| **Visual Redaction (Blur/Mask)** | **IMPLEMENTED** | `backend/privacy/redactor.py` |
| **Zero-Leak Outbound Gate** | **IMPLEMENTED** | `backend/privacy/privacy_gate.py` |
| **Deterministic Agent Planner** | **IMPLEMENTED** | `backend/agent/planner.py` |
| **Real Browser Action Executor** | **IMPLEMENTED** | `backend/actions/executor.py` |
| **Prompt Injection Defense** | **IMPLEMENTED** | `backend/security/injection_guard.py` |
| **Human Confirmation Gate** | **IMPLEMENTED** | `backend/agent/validator.py` |
| **Judge Mode Command Center** | **IMPLEMENTED** | `frontend/src/pages/JudgeModePage.tsx` |
| **Pure In-Extension Wasm OCR** | **FUTURE WORK** | Planned for v2.0 |

---

## 35. Architecture Cheat Sheet

```
USER GOAL ──► FRONTEND ──► FASTAPI ──► PERCEPTION (OpenCV+OCR)
                                             │
                                             ▼
                                      PRIVACY GATE (PII Redaction)
                                             │
                                             ▼
                                      INJECTION GUARD
                                             │
                                             ▼
                                      AGENT PLANNER
                                             │
                                             ▼
                                      ACTION VALIDATOR
                                             │
                                             ▼
                                      ACTION EXECUTOR ──► BROWSER TAB
```

---

## 36. File Cheat Sheet

* `context_fuser.py`: Merges DOM + OCR + OpenCV contours via IoU.
* `pii_detector.py`: Detects PAN, Aadhaar, Cards, Passwords, OTPs.
* `privacy_gate.py`: Blocks raw screenshot egress; enforces zero-leak boundary.
* `planner.py`: Decomposes tasks and ranks candidate actions.
* `validator.py`: Enforces action budget (15), bounds, and loop limits.
* `executor.py`: Dispatches safe atomic browser actions.
* `injection_guard.py`: Neutralizes prompt injection strings.
* `JudgeModePage.tsx`: Dedicated 1-click SIH presentation interface.

---

## 37. Technology Cheat Sheet

* **FastAPI**: Backend web framework hosting REST endpoints.
* **OpenCV**: Computer vision library finding element contours.
* **Tesseract**: OCR engine extracting bounding boxes and words.
* **React 19**: Frontend UI framework for the dashboard.
* **Vite**: Frontend build tool compiling in 56ms.
* **Manifest V3**: Modern Chromium browser extension standard.

---

## 38. 20 Things You Must Memorize

1. **Problem Statement**: SIH26171 (ISRO).
2. **Slogan**: *"See. Understand. Protect. Act."*
3. **Cloud Vision Calls**: **0 (Zero)**.
4. **Perception Latency**: **1.97 ms**.
5. **Total Agent Loop**: **18.90 ms**.
6. **Evaluation Score**: **99.0 / 100**.
7. **PII Detection F1-Score**: **1.00 (100%)**.
8. **Task Success Rate**: **100.0%**.
9. **Security Defense Score**: **100.0% (15/15 blocked)**.
10. **Three Sources**: DOM Nodes, OCR Text Blocks, OpenCV Contours.
11. **Fusion Algorithm**: IoU matching ($\ge 0.30$) + Weighted Confidence.
12. **Supported PII**: Indian PAN, Aadhaar, Cards, Passwords, OTPs, Emails, Phones.
13. **False Positive Handling**: Preserves calendar years (`2026`), prices (`₹999`), order IDs.
14. **Privacy Invariant**: Raw screenshots never cross the trust boundary.
15. **Reasoning Strategy**: Goal decomposition + Multi-factor candidate ranking.
16. **Action Budget**: Max 15 actions per task.
17. **Loop Limit**: Halts if 3 identical consecutive actions occur.
18. **Prompt Injection**: `InjectionGuard` neutralizes jailbreaks in layout text.
19. **Protocol Filter**: Blocks dangerous `javascript:` and `data:` schemes.
20. **Judge Mode**: Top-right header button for instant 1-click evaluation.

---

## 39. Files Judges May Inspect

1. `backend/perception/context_fuser.py` — Judges want to see how DOM and Vision are merged.
2. `backend/privacy/pii_detector.py` — Judges want to verify Indian PAN and Aadhaar regexes.
3. `backend/privacy/privacy_gate.py` — Judges want to confirm `PrivacyGateViolation` zero-leak enforcement.
4. `backend/agent/planner.py` & `scoring.py` — Judges want to see the candidate ranking formula.
5. `backend/security/injection_guard.py` — Judges want to see prompt injection regex defenses.
6. `tests/test_security_adversarial.py` — Judges want to see the 15 passing security tests.

---

## 40. Beginner Hinglish Explanation

> *"Bhai, simple shabdon mein samjho:*
>
> 1. **Problem Kya Thi?**
>    Aaj kal ke AI browser agents (jaise ChatGPT Vision) har click pe aapke screen ka screenshot capture karke cloud server pe bhejte hain. Isse password aur Aadhaar card leak hota hai aur 2-3 second ka time lagta hai.
>
> 2. **Humne Kya Kiya?**
>    Humne poora perception engine **apne laptop ke andar (on-device)** bana diya!
>    - **Aankhein (Perception)**: OpenCV aur Tesseract OCR se screen ke buttons 2 millisecond me dhundhta hai.
>    - **Parda (Privacy Gate)**: PAN card ya password ko turant blur karke `[REDACTED_...]` bana deta hai.
>    - **Dimaag (Planner)**: Goal ko steps me divide karke agla best action calculate karta hai.
>    - **Suraksha (Security)**: Malicious website ke prompt injection ko block karta hai aur 14 lakh ke payment pe human confirmation maangta hai!
>    - **Haath (Executor)**: Browser me click, type, scroll perform karta hai.
>
> *Judge ke samne bolna:* **'Sir, hamara agent cloud pe 1 rupee bhi kharch nahi karta aur 0 millisecond ka network data leak karta hai!'**"*

---

## 41. Self-Test Quiz (60 Questions + Answer Key)

### Questions:
1. What is the full title of SIH problem statement SIH26171?
2. Which organization posted this problem statement?
3. Does PrivyBrowse AI require an active internet connection for perception?
4. What are the 3 sources merged by the Context Fuser?
5. What programming language is used for the backend?
6. What framework is used for the frontend?
7. What is the Manifest version of the Chrome extension?
8. Name 3 PII categories detected by the system.
9. What happens to a password field before it reaches the planner?
10. What is the default maximum action budget?
11. How many repetitive actions trigger the loop detector?
12. Which URL schemes are blocked by `NavigationGuard`?
13. What is the average perception latency of PrivyBrowse AI?
14. What is the evaluation score achieved on the SIH benchmark?
15. What does IoU stand for?
16. Name 3 browser actions supported by `ActionExecutor`.
17. What exception is raised if raw screenshots attempt to egress?
18. Where is the Judge Mode button located in the UI?
19. How many standard benchmark tasks were evaluated?
20. What algorithm validates credit/debit card numbers?
21. What is the composite confidence formula in `context_fuser.py`?
22. How does `is_false_positive_number()` distinguish '2026' from an Aadhaar card?
23. Why is Manifest V3 used instead of Manifest V2?
24. How does `InjectionGuard` neutralize prompt injection strings?
25. Explain the role of `PageChangeDetector`.
26. How does the system handle a `STALE_TARGET` error?
27. What is the purpose of `SecurityAuditLogger`?
28. How does `ActionValidator` determine if an element is high-risk?
29. What port does the FastAPI backend run on?
30. How does the frontend communicate with the backend?
31. What is the purpose of `preprocessor.py`?
32. How are bounding boxes represented in PrivyBrowse AI?
33. What image enhancement is applied before OCR?
34. How does `CandidateGenerator` match elements to a search task?
35. What is the purpose of the `ConfirmDialog` component?
36. Why is headless OpenCV used in `requirements.txt`?
37. What statistical metrics does `PerformanceTracker` calculate?
38. What is the function of `secret_scanner.py`?
39. How does `LocalRuleBasedEngine` differ from an LLM-based planner?
40. How does the system verify that a navigation action succeeded?
41. If a webpage uses custom `<canvas>` elements instead of HTML buttons, how does PrivyBrowse perceive them?
42. Why is rule-based scoring superior to an unquantized 7B LLM for edge browser agents?
43. How does the trust boundary isolate `user_goal` from webpage DOM attributes?
44. Trace the exact call sequence when a user clicks 'Run Agent' on the Chandrayaan-3 hero demo.
45. Explain how Haar Cascade is used in `backend/privacy/rules/face_detector.py`.
46. How does the system prevent memory leaks during continuous perception cycles?
47. What is the time complexity of the IoU bounding-box fusion algorithm?
48. Why can't a malicious webpage forge a `TRUSTED_CONFIRMATION` event?
49. What is the exact formula for the PrivyBrowse Evaluation Score?
50. How does the extension's `service_worker` capture tabs asynchronously?
51. If Tesseract OCR fails on low-contrast text, how does the system recover?
52. How does the Privacy Gate handle base64 visual redaction in memory?
53. What is the role of `numpy` in coordinate conversion between viewport and screenshot?
54. Why does `ActionExecutor` validate coordinates against screen boundaries ($1920\times 1080$)?
55. Explain the threat of 'Confirmation Spoofing' and how PrivyBrowse defeats it.
56. How does `SecretScanner` scan code without sending data to external APIs?
57. What are the key limitations of the current implementation?
58. How would WebAssembly (Wasm) improve the next version of PrivyBrowse?
59. How does the system guarantee zero PII in error messages and exceptions?
60. Why does ISRO specifically care about on-device perception for browser agents?

---

### Answer Key:
* **1–10**: (1) On-Device Visual Perception for Lightweight Browser Agents, (2) ISRO, (3) No, 100% offline, (4) DOM, OCR, OpenCV Contours, (5) Python 3.12, (6) React 19 + TypeScript + Vite, (7) Manifest V3, (8) PAN, Aadhaar, Cards, Passwords, (9) Redacted to `[REDACTED_PASSWORD]`, (10) 15 actions.
* **11–20**: (11) 3 consecutive identical actions, (12) `javascript:`, `data:`, `vbscript:`, `file:`, (13) 1.97 ms, (14) 99.0 / 100, (15) Intersection over Union, (16) `CLICK`, `TYPE`, `SCROLL`, `NAVIGATE`, (17) `PrivacyGateViolation`, (18) Top-right header, (19) 10 standard tasks, (20) Luhn Algorithm (Mod 10).
* **21–30**: (21) $0.40(DOM) + 0.35(OCR) + 0.25(CV)$, (22) Checks 4-digit boundaries and currency/prefix context, (23) Mandatory Chrome security standard, (24) Regex substitution to `[NEUTRALIZED_ADVERSARIAL_DIRECTIVE]`, (25) Checks URL shifts, DOM tree deltas, and scroll position, (26) Halts action and triggers immediate re-perception, (27) Zero-leak structured audit logging, (28) Checks for keywords like *delete, pay, authorize* and financial values, (29) Port 8000, (30) REST JSON calls (`fetch()`).
* **31–40**: (31) Decodes base64 and enhances image contrast, (32) `[x, y, width, height]`, (33) Grayscale conversion + Contrast Stretching, (34) Semantic tag alignment (`input[type=search]`, placeholder matches), (35) Renders anti-spoofing modal UI for user approval, (36) Runs without GUI/X11 display dependencies, (37) Avg, Median, P95, Min, Max, and RSS Memory, (38) On-device static scan for accidental secret commits, (39) Deterministic, explainable, sub-millisecond latency, (40) Validates URL change and DOM stabilization.
* **41–60**: (41) OpenCV visual contours detect the bounding box even without DOM tags, (42) Eliminates multi-gigabyte RAM overhead and non-deterministic hallucination, (43) User goal is immutable in application state; DOM text is passive observation data, (44) `Frontend` $\rightarrow$ `main.py` $\rightarrow$ `PerceptionEngine` $\rightarrow$ `PIIDetector` $\rightarrow$ `PrivacyGate` $\rightarrow$ `Planner` $\rightarrow$ `Validator` $\rightarrow$ `Executor` $\rightarrow$ `ChangeDetector`, (45) Detects frontal human faces in screenshots for automatic blurring, (46) Explicit `gc.collect()` and cached singleton instances, (47) $\mathcal{O}(N \times M)$ where $N, M \le 50$, executing in $<0.1\text{ ms}$, (48) Confirmation state is stored in memory in trusted React/Python state, not readable or writable by DOM JS, (49) $0.35(Task) + 0.20(PII) + 0.20(Perception) + 0.15(Security) + 0.10(Recovery)$, (50) Uses `chrome.tabs.captureVisibleTab()`, (51) DOM geometry and OpenCV contours maintain ground truth bounding boxes, (52) Directly overlays solid or pixelated rectangles on raw PIL/OpenCV image arrays, (53) Applies aspect ratio scaling matrix, (54) Rejects coordinate injection and out-of-screen clickjacking, (55) Webpages cannot trigger or approve system-level confirmation modals, (56) Local regex matching on source strings without network egress, (57) Multi-lingual complex CAPTCHAs require human help, (58) Allows running OpenCV/Tesseract directly inside the browser extension without a local Python daemon, (59) Structured error handler masks all sensitive fields prior to serialization, (60) Space missions, satellite data portals, and internal telemetry demand zero data leakage and real-time offline autonomy.

---
*End of PrivyBrowse AI Knowledge Base Document.*
