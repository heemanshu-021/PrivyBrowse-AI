# End-to-End Autonomous Browser Agent Loop

## 1. The Autonomous Loop
The `EndToEndAgentRunner` orchestrates multi-step goal execution across live web applications:

```
                  ┌──────────────────────────────┐
                  │       USER GOAL INPUT        │
                  └──────────────┬───────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               │
          ┌─────────────┐                        │
          │   OBSERVE   │ (Capture screenshot & DOM)
          └──────┬──────┘                        │
                 ▼                               │
          ┌─────────────┐                        │
          │   PERCEIVE  │ (OpenCV + Tesseract fusion)
          └──────┬──────┘                        │
                 ▼                               │
          ┌─────────────┐                        │
          │   SANITIZE  │ (Privacy Gatekeeper)   │
          └──────┬──────┘                        │
                 ▼                               │
          ┌─────────────┐                        │
          │    PLAN     │ (Score & rank candidate)
          └──────┬──────┘                        │
                 ▼                               │
          ┌─────────────┐                        │
          │  VALIDATE   │ (Pre-execution Safety Gate)
          └──────┬──────┘                        │
                 ├─────────────► ┌─────────────────────────┐
                 │ (High Risk)   │ HUMAN CONFIRMATION GATE │
                 ▼               └─────────────────────────┘
          ┌─────────────┐
          │   EXECUTE   │ (Atomic Browser Action)
          └──────┬──────┘
                 ▼
          ┌─────────────┐
          │   VERIFY    │ (Evaluate state mutation)
          └──────┬──────┘
                 │
                 ├───────────────────────────────┐
                 │ (Page Changed / More Objs)    │ (All Objs Complete)
                 ▼                               ▼
          [ RE-PERCEIVE ]                  [ COMPLETED ]
```

---

## 2. Recovery Strategies

| Trigger Condition | Primary Recovery Action | Fallback Strategy |
| :--- | :--- | :--- |
| **`TARGET_NOT_FOUND` / `STALE_TARGET`** | Trigger immediate re-perception snapshot | Search alternative candidate element |
| **`PAGE_CHANGED`** | Invalidate previous coordinate cache | Re-perceive updated viewport |
| **`POSSIBLE_AGENT_LOOP`** | Halt automatic retries after 3 duplicate failures | Transition state to `PAUSED` / `BLOCKED` |
| **`ACTION_BUDGET_EXCEEDED`** | Safely terminate task ($> \text{max\_actions}$) | Transition state to `FAILED` with audit trace |
| **`REQUIRES_CONFIRMATION`** | Pause autonomous action loop | Display confirmation modal to user |
