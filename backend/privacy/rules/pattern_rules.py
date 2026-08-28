"""
PrivyBrowse AI — PII Pattern Rules & Algorithmic Validators
Provides deterministic regex matchers and algorithmic checksums (Luhn, Aadhaar format).
"""

import re
from typing import List, Tuple, Optional


# 1. EMAIL PATTERN
EMAIL_REGEX = re.compile(
    r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    re.IGNORECASE
)

# 2. PHONE PATTERNS
# Matches:
#   - Indian 10-digit numbers (+91 9876543210, +91-98765-43210, 9876543210)
#   - US/International: +1 (555) 123-4567, 555-123-4567, +44 20 7946 0919
PHONE_REGEX = re.compile(
    r'(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,5}\b'
)
INDIAN_MOBILE_REGEX = re.compile(r'\b(?:(?:\+91|0)[\s.-]?)?[6-9]\d{9}\b')

# 3. PAYMENT CARD PATTERNS
# 13 to 19 digits with optional spaces or hyphens
CARD_REGEX = re.compile(
    r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|2(?:22[1-9]|2[3-9][0-9]|[3-6][0-9]{2}|7[0-1][0-9]|720)[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11}|6[0-9]{15})\b|\b(?:\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4})\b'
)

# 4. INDIAN PAN (Permanent Account Number)
# Format: 5 uppercase letters, 4 digits, 1 uppercase letter. E.g. ABCDE1234F
PAN_REGEX = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')

# 5. INDIAN AADHAAR NUMBER
# Format: 12 digits, typically formatted as 4-4-4 (e.g. 9876 5432 1098 or 9876-5432-1098 or 12 continuous digits starting with 2-9)
AADHAAR_REGEX = re.compile(
    r'\b[2-9]\d{3}[\s-]\d{4}[\s-]\d{4}\b|\b[2-9]\d{11}\b'
)

# 6. BANK ACCOUNT / IBAN
IBAN_REGEX = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b')
BANK_ACCOUNT_REGEX = re.compile(r'\b\d{9,18}\b')

# 7. OTP / 2FA VERIFICATION CODE
OTP_REGEX = re.compile(r'\b\d{4,8}\b')

# 8. API KEYS, SECRETS, AND TOKENS
JWT_REGEX = re.compile(r'\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]+\b')
API_KEY_PREFIX_REGEX = re.compile(
    r'\b(?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{40,}|sk_live_[a-zA-Z0-9]{24,}|pk_live_[a-zA-Z0-9]{24,}|AIza[0-9A-Za-z-_]{35}|xox[baprs]-[0-9a-zA-Z]{10,})\b'
)
BEARER_TOKEN_REGEX = re.compile(r'\bBearer\s+([a-zA-Z0-9_\-\.]{20,})\b', re.IGNORECASE)


def validate_luhn(card_number: str) -> bool:
    """
    Validates a credit/debit card number using the Luhn checksum algorithm (Mod 10).
    Returns True if the checksum passes.
    """
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


def validate_aadhaar_format(aadhaar_str: str) -> bool:
    """
    Checks if a string conforms to the 12-digit Indian Aadhaar format (does not start with 0 or 1).
    """
    digits = [c for c in aadhaar_str if c.isdigit()]
    if len(digits) != 12:
        return False
    # Aadhaar numbers never start with 0 or 1
    if digits[0] in ('0', '1'):
        return False
    # Cannot be all repeating digits (e.g. 999999999999)
    if len(set(digits)) == 1:
        return False
    return True


def matches_email(text: str) -> List[Tuple[str, int, int]]:
    """Returns list of (match_text, start_idx, end_idx) for emails."""
    return [(m.group(), m.start(), m.end()) for m in EMAIL_REGEX.finditer(text)]


def matches_phone(text: str) -> List[Tuple[str, int, int]]:
    """Returns list of (match_text, start_idx, end_idx) for valid phone numbers."""
    matches = []
    # Check Indian mobile specific
    for m in INDIAN_MOBILE_REGEX.finditer(text):
        matches.append((m.group(), m.start(), m.end()))
    # Check general phone
    for m in PHONE_REGEX.finditer(text):
        val = m.group().strip()
        digit_count = sum(c.isdigit() for c in val)
        if 10 <= digit_count <= 15:
            # Avoid duplicating already matched ranges
            if not any(m.start() >= start and m.end() <= end for _, start, end in matches):
                matches.append((val, m.start(), m.end()))
    return matches


def matches_card(text: str) -> List[Tuple[str, int, int, bool]]:
    """
    Returns list of (match_text, start_idx, end_idx, luhn_valid) for card-like numbers.
    """
    matches = []
    for m in CARD_REGEX.finditer(text):
        val = m.group().strip()
        digits = re.sub(r'\D', '', val)
        if 13 <= len(digits) <= 19:
            is_luhn = validate_luhn(digits)
            matches.append((val, m.start(), m.end(), is_luhn))
    return matches


def matches_pan(text: str) -> List[Tuple[str, int, int]]:
    """Returns list of (match_text, start_idx, end_idx) for Indian PAN cards."""
    return [(m.group(), m.start(), m.end()) for m in PAN_REGEX.finditer(text)]


def matches_aadhaar(text: str) -> List[Tuple[str, int, int]]:
    """Returns list of (match_text, start_idx, end_idx) for Aadhaar numbers."""
    matches = []
    for m in AADHAAR_REGEX.finditer(text):
        val = m.group().strip()
        if validate_aadhaar_format(val):
            matches.append((val, m.start(), m.end()))
    return matches


def matches_bank_account(text: str) -> List[Tuple[str, int, int, str]]:
    """Returns list of (match_text, start_idx, end_idx, kind) for bank/IBAN numbers."""
    matches = []
    for m in IBAN_REGEX.finditer(text):
        matches.append((m.group(), m.start(), m.end(), "IBAN"))
    return matches


def matches_secret_token(text: str) -> List[Tuple[str, int, int, str]]:
    """Returns list of (match_text, start_idx, end_idx, token_type) for API keys/tokens."""
    matches = []
    for m in JWT_REGEX.finditer(text):
        matches.append((m.group(), m.start(), m.end(), "JWT"))
    for m in API_KEY_PREFIX_REGEX.finditer(text):
        matches.append((m.group(), m.start(), m.end(), "API_KEY"))
    for m in BEARER_TOKEN_REGEX.finditer(text):
        matches.append((m.group(1), m.start(1), m.end(1), "BEARER_TOKEN"))
    return matches


def matches_otp(text: str, context: str = "") -> List[Tuple[str, int, int]]:
    """
    Matches OTP only if the context text contains verification/security keywords.
    Avoids classifying random 4-6 digit numbers as OTPs.
    """
    ctx_lower = (text + " " + context).lower()
    otp_indicators = ["otp", "one-time", "one time", "verification code", "2fa", "security code", "passcode", "verify code"]
    if not any(ind in ctx_lower for ind in otp_indicators):
        return []

    matches = []
    for m in OTP_REGEX.finditer(text):
        val = m.group().strip()
        if 4 <= len(val) <= 8:
            matches.append((val, m.start(), m.end()))
    return matches
