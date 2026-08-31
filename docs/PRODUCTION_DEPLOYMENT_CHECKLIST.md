# PrivyBrowse-AI — Production Deployment Checklist
**SIH26171: On-Device Visual Perception for Lightweight Browser Agents**

Use this verification checklist prior to demonstration, staging, or production distribution.

---

## 1. Environment & Dependency Verification

- [x] **Python Environment**: Verified Python 3.10+ (tested on Python 3.13.5 arm64).  
  *Verification*: `python scripts/validate_environment.py`
- [x] **Dependencies Installed**: All pinned requirements in `requirements.txt` installed cleanly.  
  *Verification*: `pip check` (0 broken requirements).
- [x] **OpenCV Headless**: Verified OpenCV 4.10.0 contour detection and morphological algorithms.  
  *Verification*: `python scripts/smoke_test.py`
- [x] **OCR Engine Status**: Probed native Tesseract binary and verified DOM-text proxy fallback.  
  *Verification*: `/api/health/ready` reports `ocr_mode`.
- [x] **Node.js / Frontend**: Dashboard built with `npm run build` into `frontend/dist/`.  
  *Verification*: `ls frontend/dist/index.html`

---

## 2. Configuration & Isolation

- [x] **Configuration Validation**: Loaded via `backend/config.py` with type-safe pydantic settings.  
  *Verification*: Ingestion tested with custom ports and environment flags.
- [x] **Simulation Mode Disabled**: In production (`PRIVYBROWSE_ENV=production`), `simulation_mode` defaults to `False`.  
  *Verification*: No silent fallback on extension disconnection.
- [x] **Network Binding**: Bound strictly to `127.0.0.1` by default to prevent unauthorized network exposure.  
  *Verification*: `PRIVYBROWSE_HOST=127.0.0.1` in `.env.example`.
- [x] **Origin Security (CORS)**: Allowed origins restricted to localhost ports and `chrome-extension://*`.  
  *Verification*: `CORSMiddleware` regex in `backend/main.py`.

---

## 3. Extension & Browser Readiness

- [x] **Manifest V3 Packaging**: `extension/manifest.json` validated with minimal permissions (`activeTab`, `scripting`, `storage`, `tabs`).  
  *Verification*: Validated against Chrome Manifest V3 specification.
- [x] **Service Worker State Machine**: Handles `INITIALIZING`, `CONNECTED`, `DEGRADED`, and `RECONNECTING`.  
  *Verification*: `tests/test_extension_lifecycle.py`
- [x] **Debounced DOM Extraction**: Content script MutationObserver debounces rapid DOM changes (250ms batching).  
  *Verification*: `tests/test_context_sync_real_browser.py`

---

## 4. Security, Privacy & Invariant Validation

- [x] **Prompt-Injection Guard**: Multi-stage text normalizer catches direct overrides and hidden CSS injections.  
  *Verification*: `tests/test_security_production.py`
- [x] **On-Device PII Masking**: Aadhaar, PAN, payment cards, and passwords redacted before logging or UI broadcast.  
  *Verification*: `tests/test_privacy.py`
- [x] **Action Validation & Confirmation Gates**: Financial/destructive operations blocked unless user-confirmed.  
  *Verification*: `tests/test_e2e_production_validation.py` (E2E-10).
- [x] **Navigation Security & SSRF Protection**: AWS metadata (`169.254.169.254`) and dangerous schemes rejected.  
  *Verification*: `tests/test_security_hardening.py`

---

## 5. Operational Health, Shutdown & Git State

- [x] **Liveness & Readiness Probes**: Verified `/api/health/live` and `/api/health/ready`.  
  *Verification*: `curl -s http://127.0.0.1:8000/api/health/live`
- [x] **Graceful Shutdown**: SIGINT / SIGTERM signals stop running tasks and flush bridge queues cleanly.  
  *Verification*: `@app.on_event("shutdown")` in `backend/main.py`.
- [x] **No Secrets Committed**: Static repository scan verifies zero hardcoded tokens or API credentials.  
  *Verification*: `python -c "from backend.security.secret_scanner import StaticSecretScanner; res = StaticSecretScanner().scan_directory('.'); print('Clean:', res.clean)"`
- [x] **Git Status Clean**: All changes committed and synchronized with `origin/main`.
