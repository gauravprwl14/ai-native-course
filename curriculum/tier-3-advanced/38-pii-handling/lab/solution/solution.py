"""Lab 38: PII Handling — Reference Solution"""
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

PII_PATTERNS = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
}


def detect_pii(text: str) -> dict[str, list[str]]:
    """Detect PII in text. Returns {pii_type: [matched_values]}."""
    results = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            # re.findall returns tuples when pattern has capture groups
            cleaned = [m if isinstance(m, str) else m[0] for m in matches]
            # Filter out empty strings from group captures
            cleaned = [v for v in cleaned if v.strip()]
            if cleaned:
                results[pii_type] = cleaned
    return results


def redact_pii(text: str) -> str:
    """Replace all PII with [TYPE_REDACTED] labels."""
    result = text
    for pii_type, pattern in PII_PATTERNS.items():
        result = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", result)
    return result


def pseudonymize(text: str) -> tuple[str, dict]:
    """Replace PII with consistent fake values. Returns (pseudonymized_text, mapping)."""
    result = text
    mapping = {}      # placeholder → original
    reverse = {}      # original → placeholder (for consistency)
    counters = {}     # pii_type → count

    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, result)
        for match in matches:
            value = match if isinstance(match, str) else match[0]
            if not value.strip():
                continue
            if value not in reverse:
                count = counters.get(pii_type, 0) + 1
                counters[pii_type] = count
                placeholder = f"{pii_type}_{count}"
                reverse[value] = placeholder
                mapping[placeholder] = value
            result = result.replace(value, reverse[value], 1)

    return result, mapping


def restore_pseudonyms(text: str, mapping: dict) -> str:
    """Reverse pseudonymization using the mapping."""
    result = text
    for placeholder, original in mapping.items():
        result = result.replace(placeholder, original)
    return result
