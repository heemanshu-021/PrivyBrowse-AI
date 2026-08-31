# PrivyBrowse-AI — Final System Integration & Contract Matrix
**SIH26171: On-Device Visual Perception for Lightweight Browser Agents**

This document establishes the verified contracts, data transfer formats, pre/post validations, and fail-closed behaviors across all component boundaries in the PrivyBrowse-AI closed loop.

---

## 1. System Integration Boundary Contracts

| Boundary ID | Component A | Component B | Data / Contract | Validation & Rules | Failure Behavior | Verification Test | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **INT-01** | Frontend / User | Backend API | HTTP REST / SSE Event Stream (`/api/task`, `/api/events/stream`) | JSON schema validation via Pydantic; sanitized query string | Returns HTTP 400/422 with structured error payload | `tests/test_observability.py` | `REAL / WORKING` |
| **INT-02** | Backend Bridge | Chrome Extension | Manifest V3 HTTP Polling & Long-lived SSE (`/api/action/pending`, `/api/action/ack`) | 10MB payload size limit; 10s heartbeat timeout; deduplication UUID | `is_extension_connected() == False` $\to$ Executor fails fast | `tests/test_extension_lifecycle.py` | `REAL / WORKING` |
| **INT-03** | Chrome Extension | Active Browser Tab | DOM MutationObserver & Chrome Scripting API (`chrome.scripting.executeScript`) | 250ms debounced event batching; restricted URI scheme filtering | Malicious scripts blocked; unmounted nodes skipped | `tests/test_context_sync_real_browser.py` | `REAL / WORKING` |
| **INT-04** | Browser Context | Perception Pipeline | Unified Context Payload (`screenshot_bytes`, `dom_nodes`, `viewport`, `scroll`) | SHA-256 structural fingerprint check; DPR coordinate scaling | Empty screenshot returns `INVALID_IMAGE` gracefully | `tests/test_perception.py` | `REAL / WORKING` |
| **INT-05** | Perception | Privacy Gate | Raw DOM nodes, OCR bounding boxes, screenshot buffers | Regex PII scanning (Aadhaar, PAN, Card), Verhoeff/Luhn checksums | Sensitive text masked to `[REDACTED_...]` before downstream consumption | `tests/test_privacy.py` | `REAL / WORKING` |
| **INT-06** | Privacy Gate | Agent Planner | Sanitized Layout Elements (`fused_elements`), active URL, task goal | Guarantees zero raw passwords, cards, or identification numbers reach planner | Unsanitized payloads blocked fail-closed | `tests/test_production_smoke_suite.py` (SMOKE-04) | `REAL / WORKING` |
| **INT-07** | Agent Planner | Security Guards | Candidate Action JSON (`action`, `target_id`, `target_coords`, `text`) | PromptInjectionGuard normalizes text; NavigationGuard inspects target URI | Injection flagged $\to$ threat neutralized; SSRF/malware blocked | `tests/test_security_production.py` | `REAL / WORKING` |
| **INT-08** | Security Guards | Action Validator | Authorized Candidate Action JSON, Task Constraints, History | Bounds check: coordinates within screen $(1920\times 1080)$; loop count $<3$; action budget | `allowed=False` $\to$ Executor is **strictly never called** | `tests/test_production_smoke_suite.py` (SMOKE-06) | `REAL / WORKING` |
| **INT-09** | Action Validator | Action Executor | Validated Action Record with Risk Level & Target Coordinates | Server-side user confirmation required for `HIGH`/`CRITICAL` financial operations | Unconfirmed high-risk actions rejected fail-closed | `tests/test_production_smoke_suite.py` (SMOKE-06) | `REAL / WORKING` |
| **INT-10** | Action Executor | Browser Verifier | Dispatched Action Type, Target ID, Pre-action DOM State | FIFO dispatch to extension; wait for acknowledgement with 5000ms timeout | Extension timeout $\to$ returns `status="TIMEOUT"` without claiming success | `tests/test_production_smoke_suite.py` (SMOKE-08) | `REAL / WORKING` |
| **INT-11** | Browser Verifier | Recovery Engine | Post-action DOM state, URL transition, input values, scroll deltas | Verifies real state mutation (DOM attribute, URL change, or input value update) | No mutation detected $\to$ returns `VerificationResult(success=False)` | `tests/test_production_smoke_suite.py` (SMOKE-09) | `REAL / WORKING` |
| **INT-12** | Recovery Engine | Task Planner | Classified Failure Category, Recovery Recommendation (`REPERCEIVE`, `RETRY`, `SAFE_STOP`) | Retry count bounded at 2 per objective; 4 stagnant turns trigger loop stop | Max retries exceeded $\to$ triggers `SAFE_STOP` and halts task | `tests/test_verification_recovery.py` | `REAL / WORKING` |
| **INT-13** | Task Planner | Observability Bus | Structured Event Objects (`AgentTraceEntry`, `TaskCheckpoint`, `SystemHealth`) | Sensitive values scrubbed; bounded 500-event ring buffer capacity | Ring buffer evicts oldest events to prevent memory leaks | `tests/test_observability.py` | `REAL / WORKING` |

---

## 2. End-to-End Task State Machine Invariants

```
               ┌──────────┐
               │ PLANNED  │
               └────┬─────┘
                    │ (task initiated)
                    ▼
               ┌──────────┐
      ┌───────►│ PLANNING │◄──────┐
      │        └────┬─────┘       │
      │             │             │ (re-plan / retry)
      │             ▼             │
      │        ┌──────────┐       │
      │        │VALIDATING│       │
      │        └────┬─────┘       │
      │             │ (allowed)   │
      │             ▼             │
      │        ┌──────────┐       │
      │        │EXECUTING │       │
      │        └────┬─────┘       │
      │             │             │
      │             ▼             │
      │        ┌──────────┐       │
      │        │VERIFYING ├───────┘
      │        └────┬─────┘
      │             │ (all objectives verified)
      │             ▼
      │        ┌───────────┐
      │        │ COMPLETED │ ◄── [TERMINAL & IMMUTABLE]
      │        └───────────┘
      │
      │ (user halt / critical failure)
      ▼
┌───────────┐ / ┌───────────┐
│ CANCELLED │   │  BLOCKED  │
└───────────┘   └───────────┘
```

- **Invariant 1**: `COMPLETED -> EXECUTING` transition is **strictly rejected**.
- **Invariant 2**: `BLOCKED` actions require verified server-side human confirmation before execution.
- **Invariant 3**: Disconnected extensions trigger `SAFE_STOP` without fabricating completion.
