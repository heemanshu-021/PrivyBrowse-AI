# Privacy Gate & Data Flow Architecture

## 1. Architectural Firewall & Data Flow

```
[ BROWSER VIEWPORT / EXTENSION ]
              │
              ▼
[ LOCAL PERCEPTION ENGINE ] (Prompt 4)
  - OpenCV Contours
  - Tesseract OCR
  - DOM Extraction
              │
              ▼ (Raw Perception - Marked LOCAL_UNSANITIZED)
══════════════════════════════════════════════════════════════════════════
               🔒 STRICT LOCAL TRUST BOUNDARY 🔒
══════════════════════════════════════════════════════════════════════════
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRIVACY GATEKEEPER                               │
│                                                                         │
│  1. Multi-Signal PII Detection (Email, Phone, Cards, PAN, Aadhaar...)   │
│  2. Algorithmic Validation (Luhn Checksum, UIDAI format)                │
│  3. Context Boosting & False-Positive Elimination (Years, Prices)       │
│  4. Local Redactor:                                                     │
│     - Pixel Buffer Masking (Opaque, Gaussian Blur, Pixelate)            │
│     - OCR Text Scrubbing (Replace raw strings with [REDACTED_TYPE])     │
│     - DOM Sanitization (Strip input values & passwords)                 │
│  5. Structured RedactionMap Generation                                  │
│  6. Privacy-Safe Audit Logger (Zero-secret invariant)                   │
│  7. Outbound Transmission Guard (Block raw unsanitized egress)          │
└─────────────────────────────────────────────────────────────────────────┘
              │
              ▼ (SanitizedContext - Verified Safe)
══════════════════════════════════════════════════════════════════════════
               🌐 PERMITTED EGRESS (SANITIZED ONLY) 🌐
══════════════════════════════════════════════════════════════════════════
              │
              ▼
[ DOWNSTREAM AGENT PLANNING & REASONING LAYER ] (Prompt 6+)
```

---

## 2. API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/privacy/sanitize` | `POST` | End-to-end privacy gate execution returning `SanitizedContext`, `PIIEntity[]`, `RedactionMap`, and latency. |
| `/api/privacy/detect` | `POST` | Scans OCR and DOM nodes, returning classified PII entities with confidence scores. |
| `/api/privacy/redact` | `POST` | Applies visual screenshot masking and DOM scrubbing, returning the base64 redacted image. |
| `/api/privacy/policy` | `GET` / `PUT` | Queries or updates the machine-readable `PrivacyPolicy` object. |
| `/api/privacy/audit-logs` | `GET` | Returns privacy-safe audit trail entries. |
| `/api/privacy/status` | `GET` | Returns real-time metrics (detected/redacted counts, classifications, guard status). |
