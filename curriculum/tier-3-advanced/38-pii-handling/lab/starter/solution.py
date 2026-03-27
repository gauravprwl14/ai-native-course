"""Lab 38: PII Handling"""
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
    """Detect PII in text. Returns {pii_type: [matched_values]}.
    # TODO: for each (pii_type, pattern) in PII_PATTERNS.items():
    #   matches = re.findall(pattern, text)
    #   if matches, clean them (handle tuple groups) and add to results dict.
    # Return only types that have matches (don't include empty lists).
    """
    raise NotImplementedError()


def redact_pii(text: str) -> str:
    """Replace all PII with [TYPE_REDACTED] labels.
    # TODO: for each (pii_type, pattern), apply:
    #   re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", text)
    # Return the final redacted string.
    """
    raise NotImplementedError()


def pseudonymize(text: str) -> tuple[str, dict]:
    """Replace PII with consistent fake values.
    Returns (pseudonymized_text, mapping_dict) where mapping is {placeholder: original}.
    # TODO:
    # For each pii_type and pattern, find all matches.
    # For each unique match, assign a placeholder like f"{pii_type}_1", f"{pii_type}_2"...
    # Replace each occurrence in text.
    # Build mapping: {placeholder: original_value}.
    # Return (modified_text, mapping).
    """
    raise NotImplementedError()


def restore_pseudonyms(text: str, mapping: dict) -> str:
    """Reverse pseudonymization using the mapping.
    # TODO: for each (placeholder, original) in mapping.items():
    #   result = result.replace(placeholder, original)
    # Return the restored text.
    """
    raise NotImplementedError()
