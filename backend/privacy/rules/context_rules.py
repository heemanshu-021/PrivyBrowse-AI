"""
PrivyBrowse AI — Context Rules & False Positive Elimination
Distinguishes ordinary numbers (Years, Currency, Product IDs, Order IDs, Dimensions)
from genuine sensitive identifiers, and boosts confidence when contextual keywords are present.
"""

import re
from typing import List, Dict, Any, Tuple


# Regexes for ordinary non-PII numbers
YEAR_REGEX = re.compile(r'\b(?:19\d{2}|20\d{2})\b')
PRICE_REGEX = re.compile(r'(?:[₹$€£¥]\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\s*(?:INR|USD|EUR|GBP|Rs\.?|Rupees|cents|dollars)\b)', re.IGNORECASE)
ORDER_PRODUCT_ID_REGEX = re.compile(r'\b(?:order|product|item|sku|pid|ref|invoice|bill|ticket|case|tracking)[\s#:-]*[A-Z0-9_-]{3,20}\b', re.IGNORECASE)
DIMENSION_MEASUREMENT_REGEX = re.compile(r'\b(?:\d+x\d+|\d+\s*(?:px|em|rem|%|ms|s|kg|g|km|m|cm|mm|mb|gb|tb|hz|fps))\b', re.IGNORECASE)
ZIP_POSTAL_IN_CONTEXT = re.compile(r'\b(?:zip|pin|postal)[\s:]*([0-9]{5,6})\b', re.IGNORECASE)

# Context keyword dictionaries
CONTEXT_KEYWORDS: Dict[str, List[str]] = {
    "CARD": [
        "card", "credit", "debit", "card number", "cvv", "cvc", "expiry", "expires",
        "valid thru", "visa", "mastercard", "amex", "rupay", "billing", "payment",
        "cardholder", "pan"
    ],
    "PAN": [
        "pan", "pan number", "pan card", "permanent account number", "income tax",
        "tax id", "tax identification", "it department"
    ],
    "AADHAAR": [
        "aadhaar", "aadhar", "uidai", "unique identification", "uid", "identity card",
        "citizen id"
    ],
    "EMAIL": [
        "email", "e-mail", "mail", "contact email", "username", "login id", "user id", "email address"
    ],
    "PHONE": [
        "phone", "mobile", "contact", "cell", "telephone", "tel", "call", "whatsapp",
        "dial", "fax", "phone number"
    ],
    "PASSWORD": [
        "password", "pass", "pwd", "secret", "passcode", "pin", "credentials", "current-password", "new-password"
    ],
    "OTP": [
        "otp", "one time password", "one-time", "verification code", "2fa", "two-factor",
        "security code", "passcode", "auth code"
    ],
    "BANK_ACCOUNT": [
        "bank", "account number", "a/c", "acct", "savings", "current account", "ifsc",
        "iban", "swift", "routing", "branch"
    ],
    "ADDRESS": [
        "address", "billing address", "shipping address", "street", "city", "state",
        "country", "postal code", "pincode", "zipcode", "apartment", "suite", "road"
    ],
    "NAME": [
        "full name", "first name", "last name", "name", "customer name", "recipient",
        "cardholder", "account holder", "owner"
    ],
}


def is_false_positive_number(text: str, context: str = "") -> Tuple[bool, str]:
    """
    Evaluates whether a numeric text string is an ordinary non-sensitive number
    (e.g., Year, Price, Order ID, Metric, Dimension, or Item count).

    Returns:
        (is_false_positive: bool, reason: str)
    """
    clean_text = text.strip()
    full_context = f"{context} {text}".lower()

    # 1. Check Year (1900 - 2099)
    if YEAR_REGEX.fullmatch(clean_text):
        # If explicitly marked as year or copyright
        if any(w in full_context for w in ["year", "since", "copyright", "©", "date", "est", "model", "batch"]):
            return True, "YEAR"
        # 4-digit number starting with 19 or 20 without card/id keywords is a year
        if not any(w in full_context for w in ["cvv", "otp", "pin", "code"]):
            return True, "YEAR"

    # 2. Check Currency / Price
    if PRICE_REGEX.search(clean_text) or any(c in clean_text for c in ['₹', '$', '€', '£', '¥']):
        return True, "CURRENCY_PRICE"

    # 3. Check Order / Product / Tracking ID
    if ORDER_PRODUCT_ID_REGEX.search(full_context):
        # Only suppress if it doesn't look like a valid PAN or Aadhaar
        if not re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', clean_text):
            return True, "ORDER_OR_PRODUCT_ID"

    # 4. Check Dimension / Measurement / Percentage
    if DIMENSION_MEASUREMENT_REGEX.search(clean_text):
        return True, "DIMENSION_MEASUREMENT"

    # 5. Check Plain Small Numbers (1-4 digits) without PII context
    if clean_text.isdigit() and len(clean_text) <= 3:
        if not any(kw in full_context for kw in ["cvv", "cvc", "otp"]):
            return True, "SMALL_NUMERIC_COUNT"

    return False, ""


def get_context_keywords_for_type(pii_type: str) -> List[str]:
    """Returns the list of relevant keywords for a given PII type."""
    return CONTEXT_KEYWORDS.get(pii_type.upper(), [])


def boost_confidence_with_context(
    base_confidence: float,
    pii_type: str,
    surrounding_text: str,
    dom_attributes: Dict[str, Any] = None
) -> Tuple[float, List[str]]:
    """
    Calculates contextual boost based on keyword proximity and DOM attribute alignment.

    Returns:
        (adjusted_confidence: float, detected_signals: List[str])
    """
    conf = base_confidence
    signals = []
    dom_attrs = dom_attributes or {}

    combined_context = (
        f"{surrounding_text} "
        f"{dom_attrs.get('placeholder', '')} "
        f"{dom_attrs.get('name', '')} "
        f"{dom_attrs.get('id', '')} "
        f"{dom_attrs.get('aria-label', '')} "
        f"{dom_attrs.get('autocomplete', '')}"
    ).lower()

    keywords = get_context_keywords_for_type(pii_type)

    # Keyword match in surrounding text or DOM
    matched_kws = [kw for kw in keywords if kw in combined_context]
    if matched_kws:
        conf = min(0.99, conf + 0.08)
        signals.append(f"CONTEXT_KEYWORD_MATCH({matched_kws[0]})")

    # Explicit input type match
    input_type = dom_attrs.get("type", "").lower()
    if pii_type == "PASSWORD" and input_type == "password":
        conf = 0.99
        signals.append("DOM_INPUT_TYPE_PASSWORD")
    elif pii_type == "EMAIL" and input_type == "email":
        conf = max(conf, 0.98)
        signals.append("DOM_INPUT_TYPE_EMAIL")
    elif pii_type == "PHONE" and input_type in ("tel", "phone"):
        conf = max(conf, 0.97)
        signals.append("DOM_INPUT_TYPE_TEL")

    return round(conf, 3), signals
