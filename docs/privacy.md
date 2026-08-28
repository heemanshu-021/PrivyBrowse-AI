# PrivyBrowse AI — On-Device Privacy & Trust Boundary

## 1. Executive Summary
PrivyBrowse AI enforces a strict on-device privacy firewall that intercepts observations between local visual perception and downstream agent planning. Sensitive information—including credentials, payment cards, identity numbers, and financial details—is detected and scrubbed locally. Only verified sanitized contexts are permitted to leave the local trust boundary.

---

## 2. Supported PII Categories & Data Classifications

| Category | Description & Signals | Classification | Default Action |
| :--- | :--- | :--- | :--- |
| **PASSWORD** | `<input type="password">`, credentials, secret keys | `HIGHLY_SENSITIVE` | Unconditional Tokenization (`[REDACTED_PASSWORD]`) |
| **CARD** | 13-19 digit PAN cards, Luhn checksum validation, CVV, Expiry | `HIGHLY_SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_CARD]`) |
| **AADHAAR** | 12-digit Indian national identity numbers | `HIGHLY_SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_AADHAAR]`) |
| **PAN** | 10-character Indian Permanent Account Number (`ABCDE1234F`) | `HIGHLY_SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_PAN]`) |
| **OTP** | 4-8 digit one-time verification passcodes in security context | `HIGHLY_SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_OTP]`) |
| **SECRET_TOKEN** | API keys (`ghp_...`, `sk_live_...`), JWTs, Bearer tokens | `HIGHLY_SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_SECRET]`) |
| **BANK_ACCOUNT** | 9-18 digit account numbers, IBANs in banking context | `HIGHLY_SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_BANK_ACCOUNT]`) |
| **EMAIL** | RFC-compliant email addresses | `SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_EMAIL]`) |
| **PHONE** | International & Indian 10-digit mobile numbers | `SENSITIVE` | Visual Mask + Tokenization (`[REDACTED_PHONE]`) |
| **NAME** | Customer names from DOM form inputs | `SENSITIVE` | Tokenization (`[REDACTED_NAME]`) |
| **FACE** | OpenCV Haar Cascade facial detection bounding boxes | `SENSITIVE` | Visual Gaussian Blur / Opaque Mask |
| **ADDRESS** | Physical billing/shipping street address lines | `SENSITIVE` | Tokenization (`[REDACTED_ADDRESS]`) |

---

## 3. Strict Privacy Invariants
1. **Zero-Password Logging**: Raw password strings are stripped unconditionally and never written to telemetry, memory logs, or audit streams.
2. **Outbound Transmission Guard**: The `PrivacyGate` blocks raw perception payloads (`RAW_CONTEXT_BLOCKED_BY_PRIVACY_GATE`) from egressing outside the device.
3. **Privacy-Safe Audit Trails**: Audit records document *events*, *types*, and *confidence scores*, but **never** record sensitive values.
4. **Offline Local Execution**: All regex matching, algorithmic checksums, DOM parsing, and visual masking run 100% offline with zero cloud DLP calls.

---

## 4. Known Limitations & Technical Honesty
* **Context-Free Random Numbers**: A random 10-digit number appearing without phone/card context may not be flagged to avoid high false-positive rates on public datasets.
* **Complex Multi-line Names**: Free-form natural language names in unstructured prose without DOM attribute signals require semantic language model parsing.
* **Canvas-Rendered Passwords**: Custom WebGL/canvas password inputs that bypass standard DOM `<input>` elements rely on visual character OCR rather than DOM semantics.
