# Lightweight Browser Agent — Architecture & State Machine

## 1. Overview
PrivyBrowse AI features a lightweight, on-device browser automation planner designed for the Smart India Hackathon (SIH26171 — ISRO). The agent consumes structured visual perception representations from Prompt 4 and sanitized layout contexts from Prompt 5 to formulate safe, explainable browser actions without cloud vision-language models.

---

## 2. The Core Perception-Action Lifecycle
```
PERCEIVE → UNDERSTAND → PLAN → CHECK → ACT → VERIFY → RE-PERCEIVE
```

1. **PERCEIVE**: Capture screenshot and DOM, perform OpenCV contour detection, OCR extraction, and multi-source context fusion.
2. **UNDERSTAND**: Ingest sanitized layout tokens and classify interactive affordances (buttons, inputs, links, forms).
3. **PLAN**: Select active objective, generate candidate actions, and apply transparent multi-factor scoring.
4. **CHECK / VALIDATE**: Safety Gatekeeper verifies coordinates, confidence thresholds, action budget limits, and loop detection.
5. **ACT**: Dispatch validated atomic action payload (`CLICK`, `TYPE`, `SCROLL`, `NAVIGATE`) to the browser extension.
6. **VERIFY**: Evaluate post-execution state change (URL navigation, DOM mutation, or input update).
7. **RE-PERCEIVE**: If page changed or verification requires updated state, trigger a fresh observation cycle.

---

## 3. Explicit Agent State Machine

```
              ┌─────────┐
              │  IDLE   │◄─────────────────────────────┐
              └────┬────┘                              │
                   │ (Start Task)                      │
                   ▼                                   │
             ┌───────────┐                             │
             │ OBSERVING │                             │
             └─────┬─────┘                             │
                   ▼                                   │
            ┌─────────────┐                            │
            │ PERCEIVING  │                            │
            └──────┬──────┘                            │
                   ▼                                   │
           ┌───────────────┐                           │
           │ UNDERSTANDING │                           │
           └───────┬───────┘                           │
                   ▼                                   │
             ┌───────────┐    (Pause/Resume)           │
             │ PLANNING  │◄────────────────► ┌─────────┴┐
             └─────┬─────┘                   │  PAUSED  │
                   ▼                         └──────────┘
            ┌─────────────┐                            ▲
            │ VALIDATING  │                            │
            └──────┬──────┘                            │
                   ├─────────────► ┌─────────┐         │
                   │ (High Risk)   │ BLOCKED │─────────┤
                   ▼               └─────────┘         │
              ┌─────────┐                              │
              │ ACTING  │                              │
              └────┬────┘                              │
                   ▼                                   │
             ┌───────────┐                             │
             │ VERIFYING │                             │
             └─────┬─────┘                             │
                   ├───────────────────────────────────┤
                   ▼                                   ▼
             ┌───────────┐                       ┌───────────┐
             │ COMPLETED │                       │  FAILED   │
             └───────────┘                       └───────────┘
```

### State Transitions Table

| State | Allowed Transitions | Trigger Condition |
| :--- | :--- | :--- |
| `IDLE` | `OBSERVING`, `PLANNING`, `PAUSED` | Task initiated |
| `OBSERVING` | `PERCEIVING`, `FAILED`, `PAUSED`, `BLOCKED`, `IDLE` | Frame & DOM captured |
| `PERCEIVING` | `UNDERSTANDING`, `FAILED`, `PAUSED`, `BLOCKED`, `IDLE` | OpenCV + OCR fusion complete |
| `UNDERSTANDING` | `PLANNING`, `FAILED`, `PAUSED`, `BLOCKED`, `IDLE` | Sanitized context classified |
| `PLANNING` | `VALIDATING`, `COMPLETED`, `FAILED`, `PAUSED`, `BLOCKED` | Candidate action scored |
| `VALIDATING` | `ACTING`, `BLOCKED`, `PLANNING`, `FAILED`, `PAUSED` | Constraints & policies checked |
| `ACTING` | `VERIFYING`, `FAILED`, `PAUSED`, `IDLE` | Action dispatched to extension |
| `VERIFYING` | `OBSERVING`, `PLANNING`, `COMPLETED`, `FAILED`, `PAUSED` | Outcome verified |
| `PAUSED` | `OBSERVING`, `PERCEIVING`, `PLANNING`, `IDLE` | User resumed execution |
| `BLOCKED` | `IDLE`, `PLANNING`, `ACTING`, `FAILED` | Human confirmation or abort |
| `COMPLETED` | `IDLE`, `OBSERVING` | All objectives satisfied |
| `FAILED` | `IDLE`, `OBSERVING` | Unrecoverable error or budget hit |
