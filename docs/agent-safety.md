# Agent Safety Gatekeeper, Budget Guardrails & Risk Policies

## 1. Pre-Execution Safety Validation
Before ANY browser action is executed, it must pass through the `ActionValidator`:

1. **Target Existence & Bounds**: Target coordinates $(x, y)$ must be within screen dimensions ($1920 \times 1080$).
2. **Confidence Threshold**: Target perception confidence must meet or exceed `min_confidence` (default $\ge 0.50$).
3. **Action Budget Guardrail**: Total executed actions for the task must remain strictly under `max_actions` (default 15). Exceeding this halts the agent with `ACTION_BUDGET_EXCEEDED`.
4. **Loop Detection**: If the same action is attempted 3 times consecutively on the same target, execution is halted with `POSSIBLE_AGENT_LOOP`.
5. **Human Confirmation Policy**: High-impact or financial interactions (`CRITICAL` risk) require explicit user authorization.

---

## 2. Action Risk Classification Matrix

| Risk Level | Trigger Conditions | Policy Enforcement |
| :--- | :--- | :--- |
| **LOW** | Navigation, search query typing, scrolling, public link clicks | Auto-executable if confidence is high |
| **MEDIUM** | Form filling with sanitized contact data, username input | Auto-executable within active task scope |
| **HIGH** | Password submission, settings alteration, account updates | Requires policy check; pre-sanitized tokens only |
| **CRITICAL** | Financial payments, checkout orders, data deletion, subscriptions | **BLOCKED** until explicit Human Confirmation received |

---

## 3. Privacy & Security Invariants
* **Zero Password Logging**: Raw passwords never enter agent memory, telemetry logs, or planning traces.
* **No `eval()` or Arbitrary Script Injection**: The agent only produces typed action payloads (`CLICK`, `TYPE`, `SCROLL`) dispatched through the browser extension API.
* **Sanitized Context Egress**: Only verified `SanitizedContext` is ingested by the reasoning engine.
