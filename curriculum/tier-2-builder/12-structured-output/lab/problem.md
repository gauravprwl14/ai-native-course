# Lab 12: Structured Output — Invoice Extractor

## Overview

You will build an invoice extractor that turns freeform invoice text into a validated Python dict. The extractor must handle LLM formatting quirks gracefully by implementing a retry loop with error feedback.

---

## Functions to Implement

### 1. `parse_json_with_retry(prompt, max_retries=3) -> dict`

Call the Anthropic API with the given prompt and parse the response as JSON.

**Requirements:**
- Call the API with `temperature=0`
- Attempt `json.loads` on the response text
- If `json.JSONDecodeError` is raised:
  - Append the model's bad response to the message history as an `assistant` turn
  - Append a `user` turn that includes the parse error and asks the model to try again
  - Retry up to `max_retries` total attempts
- Raise `ValueError` if all retries are exhausted without a successful parse

**Signature:**
```python
def parse_json_with_retry(prompt: str, max_retries: int = 3) -> dict:
```

---

### 2. `extract_invoice_data(text) -> dict`

Extract structured invoice data from freeform invoice text.

**Requirements:**
- Format `EXTRACTION_PROMPT` with the provided `text`
- Call `parse_json_with_retry` with the formatted prompt
- Return the parsed dict

**Expected output schema:**
```python
{
    "vendor": str,        # company or vendor name
    "amount": float,      # total invoice amount
    "currency": str,      # currency code e.g. "USD"
    "date": str,          # date in YYYY-MM-DD format
    "items": [
        {
            "description": str,
            "price": float
        }
    ]
}
```

**Signature:**
```python
def extract_invoice_data(text: str) -> dict:
```

---

### 3. `validate_invoice(data) -> tuple[bool, list[str]]`

Validate that an extracted invoice dict has all required fields with correct types.

**Requirements:**
- Check for required keys: `vendor`, `amount`, `currency`, `date`, `items`
- Check that `amount` is numeric (`int` or `float`)
- Check that `items` is a `list`
- Return `(True, [])` if all checks pass
- Return `(False, [error_message, ...])` for each validation failure found

**Signature:**
```python
def validate_invoice(data: dict) -> tuple[bool, list[str]]:
```

---

## Example Usage

```python
text = """
Invoice #1042
From: CloudHost Inc.
Date: January 15, 2024
Total: $89.00 USD

Line items:
- Server hosting (monthly): $79.00
- Domain renewal: $10.00
"""

data = extract_invoice_data(text)
valid, errors = validate_invoice(data)

print(data)
# {
#   "vendor": "CloudHost Inc.",
#   "amount": 89.0,
#   "currency": "USD",
#   "date": "2024-01-15",
#   "items": [
#     {"description": "Server hosting (monthly)", "price": 79.0},
#     {"description": "Domain renewal", "price": 10.0}
#   ]
# }

print(valid, errors)
# True []
```

---

## Running Your Solution

```bash
cd curriculum/tier-2-builder/12-structured-output/lab/starter
python solution.py
```

## Running Tests

```bash
cd curriculum/tier-2-builder/12-structured-output/lab
pytest tests/ -v
```
