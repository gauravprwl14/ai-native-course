"""Lab 12: Structured Output — Invoice Extractor (SOLUTION)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import json
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

EXTRACTION_PROMPT = """Extract invoice data from the following text and return ONLY valid JSON.
No explanations, no markdown, just the JSON object.

Required JSON schema:
{{
  "vendor": "string — company name",
  "amount": "number — total amount",
  "currency": "string — USD, EUR, etc.",
  "date": "string — YYYY-MM-DD format",
  "items": [
    {{"description": "string", "price": "number"}}
  ]
}}

Invoice text:
{text}"""


def parse_json_with_retry(prompt: str, max_retries: int = 3) -> dict:
    """Call LLM and parse JSON response, retrying on parse failures."""
    client = get_anthropic_client()
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(max_retries):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            temperature=0,
            system="Respond with valid JSON only. No explanations or code fences.",
            messages=messages,
        )
        raw = response.content[0].text.strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                raise ValueError(
                    f"Failed to parse JSON after {max_retries} attempts. "
                    f"Last response: {raw!r}"
                ) from e

            # Feed the error back to the model for self-correction
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": (
                    f"Your response was not valid JSON. "
                    f"Parse error: {e}. "
                    f"Please respond with ONLY the JSON object, nothing else."
                ),
            })

    raise ValueError("Unreachable: loop exhausted without returning or raising")


def extract_invoice_data(text: str) -> dict:
    """Extract structured invoice data from invoice text."""
    prompt = EXTRACTION_PROMPT.format(text=text)
    return parse_json_with_retry(prompt)


def validate_invoice(data: dict) -> tuple[bool, list[str]]:
    """
    Validate that extracted invoice data has required fields and types.
    Returns (is_valid: bool, errors: list[str])
    """
    errors = []
    required_keys = ["vendor", "amount", "currency", "date", "items"]

    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required field: {key}")

    if "amount" in data and not isinstance(data["amount"], (int, float)):
        errors.append("Field 'amount' must be a number")

    if "items" in data and not isinstance(data["items"], list):
        errors.append("Field 'items' must be a list")

    return (True, []) if not errors else (False, errors)


if __name__ == "__main__":
    sample_invoice = """
    Invoice #1042
    From: CloudHost Inc.
    Date: January 15, 2024
    Total: $89.00 USD

    Line items:
    - Server hosting (monthly): $79.00
    - Domain renewal: $10.00
    """

    print("Extracting invoice data...")
    data = extract_invoice_data(sample_invoice)
    print("Extracted:", json.dumps(data, indent=2))

    valid, errors = validate_invoice(data)
    print(f"Valid: {valid}")
    if errors:
        print(f"Errors: {errors}")
