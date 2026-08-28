# Action Security & Safety Policies

## 1. Zero-Trust Action Execution Principles
1. **Never Execute Arbitrary Code**: The action execution layer accepts only typed parameter dictionaries (`CLICK`, `TYPE`, `SCROLL`, `PRESS_KEY`, `NAVIGATE`, `WAIT`). No `eval()` or arbitrary JavaScript string execution is ever permitted.
2. **Strict URI Protocol Filtering**: `NAVIGATE` actions validate target URLs against permitted schemes (`http:`, `https:`, `/demo/`). Unsafe schemes (`javascript:`, `data:`, `vbscript:`, `file:`) are blocked.
3. **Zero-Leak Sensitive Payload Masking**: Password strings, payment card numbers, and secret tokens are never written to telemetry, metadata logs, or working memory.
4. **Mandatory Human-in-the-Loop for High-Risk Actions**: Financial payments, account deletions, and purchases cannot be executed autonomously without explicit user confirmation.

---

## 2. Risk Classification Matrix

| Classification | Action Types Included | Execution Gate |
| :--- | :--- | :--- |
| **LOW RISK** | Navigation, search query typing, scrolling, public link clicks | Auto-executable if confidence threshold $\ge 0.50$ |
| **MEDIUM RISK** | Form filling with sanitized contact details | Auto-executable within active task scope |
| **HIGH RISK** | Password submission, settings alteration | Policy check required; sanitized credential tokens only |
| **CRITICAL RISK** | Financial transactions, payments, account deletions | **BLOCKED** until explicit user confirmation |
