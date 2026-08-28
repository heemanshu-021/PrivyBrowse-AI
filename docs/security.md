# Security Hardening & Trust-Boundary Architecture

## 1. Security & Trust Model
PrivyBrowse AI operates under a **Zero-Trust Architecture** where any untrusted input from the web is isolated from privileged execution control:

```
[ UNTRUSTED WEBPAGE ENVIRONMENT ]
   ├── Webpage DOM Text & Structure
   ├── OCR Extracted Text & Layout
   ├── Link, Button, & Form Labels
   └── Injected Adversarial Directives
               │
               ▼
[ INJECTION GUARD & PII SANITIZATION GATE ]
   ├── Neutralizes Prompt Injections & Jailbreaks
   └── Scrubs & Masks Raw PII (PAN, Aadhaar, Cards, Passwords)
               │
═══════════════╪═══════════════════════════════════════════ [ TRUST BOUNDARY ]
               ▼
[ TRUSTED LOCAL AGENT RUNTIME ]
   ├── Master Agent Planner (Intent-driven, User Goal Isolated)
   ├── Action Security Validator (Bounds, Budget, Loop, Risk Policy)
   ├── Human Confirmation Gate (Anti-spoofing modal UI)
   ├── Real Action Executor (Whitelist protocols & key dispatch)
   └── Zero-Leak Audit Logger (Masked logs only)
```

---

## 2. Instruction / Content Separation
To defend against browser-agent prompt injection attacks, PrivyBrowse AI maintains strict structural separation between the user's objective and untrusted layout text:

```json
{
  "user_goal": "Search for Chandrayaan-3 and open first article",
  "security_policy": {
    "allow_financial_actions": false,
    "require_confirmation_for_sensitive": true,
    "max_action_budget": 15
  },
  "observed_layout_context": [
    {
      "id": "btn-01",
      "tag_name": "BUTTON",
      "text": "[NEUTRALIZED_ADVERSARIAL_DIRECTIVE]",
      "threat_level": "HIGH_RISK"
    }
  ]
}
```

Webpage content can **never** alter `user_goal`, modify `security_policy`, or invoke privileged browser actions directly.

---

## 3. Network Egress Audit

| Network Target | Classification | Security Policy |
| :--- | :--- | :--- |
| `127.0.0.1:8000` (Localhost) | **REQUIRED** | Local IPC communication between Frontend, Extension, & FastAPI |
| `api.openai.com` / Cloud LLMs | **BLOCKED BY DEFAULT** | Zero raw image or unredacted context transmission permitted |
| Third-party analytics / trackers | **BLOCKED** | Zero external telemetry or tracking scripts |
