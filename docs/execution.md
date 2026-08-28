# Real Browser Action Execution Engine

## 1. Execution Architecture
The PrivyBrowse AI Action Execution layer converts abstract agent planning decisions into atomic, verified browser interactions through the extension bridge:

```
[ AGENT PLANNER ]
       │
       ▼
[ ACTION VALIDATOR ] (Pre-execution bounds, budget, confidence, & policy checks)
       │
       ▼
[ ACTION EXECUTOR ]
       ├── CLICK (Target coordinate pointer dispatch & stale element checks)
       ├── TYPE (Keystroke simulation with zero-leak sensitive payload masking)
       ├── SCROLL (Controlled viewport scroll up/down with frame stabilization)
       ├── PRESS_KEY (Permitted whitelist key event dispatch: Enter, Tab, Esc)
       ├── NAVIGATE (Protocol validation: blocks javascript: and data: schemes)
       └── WAIT (Bounded delay for dynamic page stabilization)
       │
       ▼
[ ACTION OUTCOME VERIFIER ] (URL change, DOM mutation, value update signals)
       │
       ▼
[ PAGE CHANGE DETECTOR ] (Flags re-perception requirement if state mutated)
```

---

## 2. Supported Action Capabilities

| Action | Parameters | Safety Validations | Telemetry Returned |
| :--- | :--- | :--- | :--- |
| **CLICK** | `target: {x, y}`, `target_id` | Bounds check ($0 \le x \le W, 0 \le y \le H$), Stale target check | `status`, `duration_ms`, `page_changed` |
| **TYPE** | `target: {x, y}`, `text`, `target_id` | Field classification; masks passwords/secrets in logs | `characters_typed`, `display_payload` |
| **SCROLL** | `direction: UP/DOWN`, `amount: px` | Step bounded (default 400px); frame stabilization wait | `delta_px`, `stabilized` |
| **PRESS_KEY** | `key: Enter/Tab/Esc/Arrows` | Enforces permitted safe key whitelist; rejects code injection | `key_dispatched` |
| **NAVIGATE** | `url: string` | Blocks `javascript:`, `data:`, `vbscript:` | `previous_url`, `result_url` |
| **WAIT** | `duration_ms: float` | Bounded pause ($\le 5000\text{ms}$) | `wait_duration_ms` |

---

## 3. Structured Action Result Specification
Every action execution returns an immutable `ActionResult` record:
```json
{
  "success": true,
  "action_id": "act-48291",
  "action": "CLICK",
  "target_id": "btn-catalog-search",
  "duration_ms": 18.5,
  "timestamp": "2026-08-28T17:45:00.000Z",
  "page_changed": true,
  "status": "SUCCESS",
  "metadata": {
    "coordinates": {"x": 395.0, "y": 70.0},
    "method": "SYNTHETIC_POINTER_DISPATCH"
  }
}
```
