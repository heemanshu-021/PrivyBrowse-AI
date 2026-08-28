# PII Detection Strategy & False-Positive Elimination

## 1. Multi-Signal Detection Architecture

The PII Detector combines three orthogonal signal channels:

```
                  ┌─────────────────────────────────────────┐
                  │           OBSERVATION INPUT             │
                  └────────────────────┬────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
│   OCR TEXT ANALYSIS   │  │     DOM SEMANTICS     │  │    COMPUTER VISION    │
│ - Deterministic Regex │  │ - Input element types │  │ - OpenCV Haar Cascade │
│ - Luhn checksum check │  │ - Autocomplete hints  │  │   frontal face bbox   │
│ - Indian PAN & UIDAI  │  │ - Placeholder/Name/ID │  │ - Visual input rects  │
└───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    CONTEXT & FALSE-POSITIVE FILTER      │
                  │ - Suppress Years (1900-2099)            │
                  │ - Suppress Prices ($49, ₹999)           │
                  │ - Suppress Order IDs & Measurements     │
                  │ - Proximity keyword confidence boost    │
                  └────────────────────┬────────────────────┘
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │   STRUCTURED PII ENTITIES & LEDGER      │
                  └─────────────────────────────────────────┘
```

---

## 2. Algorithmic Validation

### Payment Cards: Luhn Algorithm (Mod 10 Checksum)
```python
def validate_luhn(card_number: str) -> bool:
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0
```

### Indian PAN Format Verification
* Standard regex: `^[A-Z]{5}[0-9]{4}[A-Z]{1}$`
* Fourth character validation (Entity Status: `P` for Individual, `C` for Company, `H` for HUF, `F` for Firm, `A` for AOP, `T` for Trust).

### Indian Aadhaar (UIDAI) Structure
* 12 digits, standard representation `\d{4}\s\d{4}\s\d{4}` or continuous starting with `[2-9]` (0 and 1 barred).

---

## 3. False Positive Suppression Matrix

| Content Example | Raw Pattern Risk | Suppression Logic | Result |
| :--- | :--- | :--- | :--- |
| `2026`, `1969` | Matches 4-digit numeric pattern | Recognized as calendar year; no CVV/OTP keywords | **IGNORED (PUBLIC)** |
| `₹999`, `$49.99` | Matches currency numbers | Currency symbol / ISO code detected | **IGNORED (PUBLIC)** |
| `Order #12345`, `PID-84729` | Matches numeric sequences | Prefixed with order/product reference tokens | **IGNORED (PUBLIC)** |
| `1920x1080 @ 60fps`, `42ms` | Matches dimension numbers | Matched measurement dimension patterns | **IGNORED (PUBLIC)** |
| `1247 users`, `3 items` | Matches integer digits | Plain counts without security/PII context | **IGNORED (PUBLIC)** |
