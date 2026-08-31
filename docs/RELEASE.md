# PrivyBrowse-AI — Release & Deployment Specification
**Version:** 1.0.0  
**Problem Statement:** SIH26171 — On-Device Visual Perception for Lightweight Browser Agents  
**Target Environment:** macOS (Verified arm64), Linux (Compatible, Headless), Windows (Compatible)  
**Security Classification:** Privacy-Preserving, Zero External Cloud Dependency for Perception/PII  

---

## 1. Release Overview

PrivyBrowse-AI 1.0.0 is an on-device visual perception and closed-loop web automation agent designed for privacy-preserving browser interactions. The entire perception, OCR, PII redaction, planning, security validation, and verification pipeline executes locally without transmitting raw webpage screenshots or user data to external cloud services.

---

## 2. Core Dependencies & Versions

| Package / Tool | Version | Purpose | Required? |
| :--- | :--- | :--- | :--- |
| **Python** | `>=3.10` (Tested on 3.13.5) | Backend runtime | **Required** |
| **FastAPI** | `0.115.0` | Local API server & SSE bus | **Required** |
| **Uvicorn** | `0.31.0` | ASGI application server | **Required** |
| **Pydantic** | `2.9.2` | Data models & validation | **Required** |
| **OpenCV Headless** | `4.10.0.84` | Contour extraction, Haar cascades, redaction | **Required** |
| **NumPy** | `2.1.2` | Matrix manipulations & coordinate math | **Required** |
| **Pillow** | `>=10.0.0` | Image format conversion & cropping | **Required** |
| **PyTesseract** | `0.3.13` | Tesseract Python wrapper | **Required** |
| **Tesseract Binary** | `>=4.0` | Native pixel OCR extraction | *Optional (Fallback to DOM_TEXT_PROXY)* |
| **Google Chrome / Chromium** | `>=114` | Manifest V3 extension host | **Required for Real Browser** |
| **Node.js** | `>=18` (Tested with npm) | Frontend dashboard build | *Optional (Pre-built in `dist/`)* |

---

## 3. Production vs Simulation vs Test Modes

1. **Production Mode (`PRIVYBROWSE_ENV=production`, `PRIVYBROWSE_SIMULATION_MODE=false`)**:
   - Backend binds to local bridge `BrowserActionBridge`.
   - Real Chrome extension connects via Manifest V3 service worker.
   - Closed-loop actions execute on real browser tabs.
   - PII redaction, prompt-injection defense, and navigation security guards are strictly active.
   - Fail-closed behavior: An unavailable extension or browser triggers `SAFE_STOP` and explicit error reporting—**never** an accidental silent fallback to simulation.

2. **Test / Simulation Mode (`PRIVYBROWSE_SIMULATION_MODE=true`)**:
   - Isolated in-memory action execution without launching live browser processes.
   - Used exclusively by automated CI/CD harnesses and unit test suites.

---

## 4. Local Deployment & Quickstart

### Step 1: Clone and Create Virtual Environment
```bash
git clone https://github.com/heemanshu-021/PrivyBrowse-AI.git
cd PrivyBrowse-AI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Validate Environment
```bash
python scripts/validate_environment.py
```

### Step 3: Run Production Smoke Test
```bash
python scripts/smoke_test.py
```

### Step 4: Start Backend Server
```bash
python scripts/start_backend.py
```
*Backend initializes at `http://127.0.0.1:8000`.*

### Step 5: Load Chrome Extension
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Toggle **Developer mode** (top right).
3. Click **Load unpacked** and select the `/extension` directory.
4. The extension icon will appear in the toolbar and connect to `http://127.0.0.1:8000/api`.

---

## 5. Health & Readiness Probes

- **Liveness Probe**: `GET http://127.0.0.1:8000/api/health/live`
  - Returns `{"status": "ALIVE", "version": "1.0.0", "env": "production"}`
- **Readiness Probe**: `GET http://127.0.0.1:8000/api/health/ready`
  - Evaluates extension connection, browser context, OCR engine, and backend queues.
- **Detailed System Health**: `GET http://127.0.0.1:8000/api/system/health`

---

## 6. Known Environment Limitations

1. **Native Tesseract Pixel OCR**:
   - When native `tesseract` binary is not installed in the operating system's PATH, PrivyBrowse-AI activates the verified `DOM_TEXT_PROXY` fallback.
   - Classification: `ENVIRONMENT LIMITATION (DOM_TEXT_PROXY FALLBACK VERIFIED)`.
2. **Supported Platforms**:
   - Verified on **macOS (Darwin arm64)**.
   - Linux and Windows environments are structurally supported with headless dependencies, but marked as `COMPATIBLE (NOT INDEPENDENTLY VERIFIED ON NATIVE OS)`.
