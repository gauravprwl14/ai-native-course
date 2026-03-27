"""Lab 12: Structured Output — Invoice Extractor"""
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
    """
    Call LLM and parse JSON response, retrying on parse failures.

    # TODO:
    # 1. Get the Anthropic client via get_anthropic_client()
    # 2. Build initial messages list: [{"role": "user", "content": prompt}]
    # 3. For each attempt in range(max_retries):
    #      a. Call client.messages.create with MODEL, temperature=0, max_tokens=1024,
    #         system="Respond with valid JSON only. No explanations or code fences.",
    #         and messages
    #      b. Get raw text: response.content[0].text.strip()
    #      c. Try json.loads(raw) — if it succeeds, return the dict
    #      d. If JSONDecodeError and this is not the last attempt:
    #           - Append {"role": "assistant", "content": raw} to messages
    #           - Append {"role": "user", "content": f"Your response was not valid JSON.
    #             Parse error: {e}. Please respond with ONLY the JSON object."} to messages
    #      e. If JSONDecodeError and this IS the last attempt:
    #           - Raise ValueError with a message explaining all retries were exhausted
    # 4. Raise ValueError if the loop completes without returning (should be unreachable)
    """
    raise NotImplementedError("Implement parse_json_with_retry")


def extract_invoice_data(text: str) -> dict:
    """
    Extract structured invoice data from invoice text.
    Returns dict matching the schema above.

    # TODO:
    # 1. Format EXTRACTION_PROMPT with the provided text:
    #      prompt = EXTRACTION_PROMPT.format(text=text)
    # 2. Call parse_json_with_retry(prompt) and return the result
    """
    raise NotImplementedError("Implement extract_invoice_data")


def validate_invoice(data: dict) -> tuple[bool, list[str]]:
    """
    Validate that extracted invoice data has required fields and types.
    Returns (is_valid: bool, errors: list[str])

    # TODO:
    # 1. Start with an empty errors list
    # 2. Check for required keys: "vendor", "amount", "currency", "date", "items"
    #      For each missing key, append f"Missing required field: {key}" to errors
    # 3. If "amount" is present, check it is int or float
    #      If not numeric, append "Field 'amount' must be a number" to errors
    # 4. If "items" is present, check it is a list
    #      If not a list, append "Field 'items' must be a list" to errors
    # 5. Return (True, []) if errors is empty, else (False, errors)
    """
    raise NotImplementedError("Implement validate_invoice")


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
