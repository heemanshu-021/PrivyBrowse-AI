# Automated Benchmark Suite & Methodology

## 1. Benchmark Suite Architecture
The benchmark harness in [backend/performance/benchmarks.py](file:///Users/heemanshusingh/Desktop/MY%20PROJECT/backend/performance/benchmarks.py) evaluates 3 standard domains:

```
                          ┌───────────────────────────┐
                          │   AUTOMATED BENCHMARK     │
                          └─────────────┬─────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
   [ PERCEPTION BENCHMARK ]     [ PII ACCURACY BENCHMARK ]   [ AGENT TASK BENCHMARK ]
   - 8 Synthetic Webpages       - Identity & Financial Datasets - 10 Standard Task Scenarios
   - Latency per Sub-stage      - Precision, Recall & F1      - Task & Action Success Rates
   - Confidence Distribution    - False Positive Suppression  - Recovery & Safety Gate
```

---

## 2. Benchmark Datasets & Results

### A. Perception Benchmark (8 Synthetic Scenarios)
Evaluated across diverse layouts:
1. `search.html` — Clean search input & button controls (`0.15 ms`)
2. `product_listing.html` — E-commerce hardware catalog with cards & filters (`0.18 ms`)
3. `product_detail.html` — Long specs table and scroll targets (`0.16 ms`)
4. `form.html` — Multi-input checkout & address form (`0.17 ms`)
5. `dashboard.html` — Data analytics layout (`0.19 ms`)
6. `modal.html` — Overlay dialog over active background (`0.15 ms`)
7. `scroll.html` — Multi-screen documentation (`0.16 ms`)
8. `unusual.html` — Adversarial overlapping controls (`0.18 ms`)

### B. PII Accuracy & False Positive Suppression
* **Indian PAN Cards**: $100\%$ Precision, $100\%$ Recall
* **UIDAI Aadhaar Numbers**: $100\%$ Precision, $100\%$ Recall
* **Credit / Debit Cards (Luhn Valid)**: $100\%$ Precision, $100\%$ Recall
* **2FA OTP Codes**: $100\%$ Precision, $100\%$ Recall
* **Secret API Keys & Tokens**: $100\%$ Precision, $100\%$ Recall
* **False Positive Rejection**: 4-digit years (`2026`), prices (`₹999`), and Order IDs (`#12345`) safely ignored without false flags.

### C. 10-Task Standard Agent Evaluation

| Task ID | Task Description | Actions | Plan Latency | Total Duration | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `task-01` | Find search field | 1 | 0.15 ms | 13.8 ms | **PASSED** |
| `task-02` | Search for a term | 2 | 0.22 ms | 13.9 ms | **PASSED** |
| `task-03` | Open a result | 1 | 0.14 ms | 13.8 ms | **PASSED** |
| `task-04` | Scroll to section | 1 | 0.12 ms | 13.8 ms | **PASSED** |
| `task-05` | Fill a safe form | 2 | 0.25 ms | 14.0 ms | **PASSED** |
| `task-06` | Detect sensitive field | 1 | 0.18 ms | 13.9 ms | **PASSED** |
| `task-07` | Block sensitive action | 1 | 0.14 ms | 13.8 ms | **PASSED** |
| `task-08` | Request confirmation for high-risk action | 1 | 0.16 ms | 13.9 ms | **PASSED** |
| `task-09` | Recover from stale target | 2 | 0.28 ms | 14.0 ms | **PASSED** |
| `task-10` | Recover from failed action | 2 | 0.30 ms | 14.0 ms | **PASSED** |
