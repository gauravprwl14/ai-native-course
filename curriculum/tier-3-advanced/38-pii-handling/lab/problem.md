# Lab 38: PII Handling

## Problem

Any AI application that processes user text will encounter PII. Your task is to build a detection and anonymization module that ensures real PII never reaches a third-party LLM API.

## Functions to Implement

### `detect_pii(text: str) -> dict[str, list[str]]`

Run all `PII_PATTERNS` against `text`. Returns a dict of `{pii_type: [matched_values]}`. Only include types with at least one match.

### `redact_pii(text: str) -> str`

Replace every PII match with `[TYPE_REDACTED]` (e.g., `[EMAIL_REDACTED]`). Irreversible — the original values cannot be recovered.

### `pseudonymize(text: str) -> tuple[str, dict]`

Replace PII with consistent placeholders (`email_1`, `email_2`, `ssn_1`, etc.). Return `(pseudonymized_text, mapping)` where `mapping` is `{placeholder: original_value}`.

### `restore_pseudonyms(text: str, mapping: dict) -> str`

Reverse the pseudonymization by replacing each placeholder with its original value from `mapping`.

## Files

- `starter/solution.py` — implement your solution here
- `solution/solution.py` — reference solution
- `tests/test_solution.py` — run with `pytest tests/ -v`

## Running Tests

```bash
cd curriculum/tier-3-advanced/38-pii-handling/lab
pytest tests/ -v
```
