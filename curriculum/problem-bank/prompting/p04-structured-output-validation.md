# Structured Output Validation

**Category:** prompting
**Difficulty:** Medium
**Key Concepts:** structured output, JSON mode, retry loops, output parsing, tool use
**Time:** 20–35 min

---

## Problem Statement

You use an LLM to extract structured data from medical records. Each record produces a patient summary in this schema:

```python
{
  "patient_id": str,
  "age": int,
  "diagnosis": str,
  "medications": list[str],
  "allergies": list[str],
  "follow_up_required": bool
}
```

Your prompt ends with: `"Respond only with valid JSON matching the schema above."`

In production, 8% of responses fail to parse:
- Some return JSON wrapped in markdown fences (` ```json ... ``` `)
- Some include a preamble: `"Here is the extracted data: {...}"`
- Some are truncated mid-object when the record is long

You're silently dropping 8% of medical records. Fix this without switching models.

---

## What Makes This Hard

The obvious fix is "use JSON mode." But **JSON mode only guarantees syntactically valid JSON — not that the keys and values match your schema.**

A response like `{"patient_id": null, "age": "forty-two", "diagnosis": 123}` is valid JSON. It will pass JSON mode. It will fail your schema and corrupt your database.

The deeper issue: you have two separate failure modes that need separate solutions:

1. **Format failures** — markdown fences, extra text, truncation (parse errors)
2. **Schema failures** — wrong types, missing required fields, unexpected nulls (validation errors)

A retry that just says "respond only with JSON" fixes format failures. It doesn't fix schema failures. You need a retry loop that feeds back the specific validation error.

A second subtlety: **truncation** is not a prompt issue. It's a `max_tokens` issue. No amount of prompt engineering fixes truncation — you need to increase `max_tokens` or use a streaming response with a timeout.

---

## Naive Approach

```python
prompt = """Extract the following fields from this medical record and respond ONLY with valid JSON,
no other text, no markdown, no explanation:
{
  "patient_id": ...,
  "age": ...,
  ...
}"""

response = client.messages.create(...)
data = json.loads(response.content[0].text)  # crashes 8% of the time
```

**Why this fails:**

1. "Respond only with JSON" is already in the prompt — models ignore it a non-trivial percentage of the time. Repeating it louder has diminishing returns.
2. Still no protection against schema violations (wrong types, missing fields).
3. Still no protection against truncation — the instruction doesn't change the token budget.
4. A bare `json.loads()` crash with no retry loses the record silently.

---

## Expert Approach

Four mechanisms in order of impact:

**Mechanism 1: Anthropic tool use (forces schema-valid output)**

Instead of asking the model to produce JSON, define the extraction as a tool call. The model is forced to call the tool with arguments that match your schema — the API rejects malformed calls.

```python
tools = [{
    "name": "extract_patient_data",
    "description": "Extract structured patient data from a medical record",
    "input_schema": {
        "type": "object",
        "properties": {
            "patient_id": {"type": "string"},
            "age": {"type": "integer"},
            "diagnosis": {"type": "string"},
            "medications": {"type": "array", "items": {"type": "string"}},
            "allergies": {"type": "array", "items": {"type": "string"}},
            "follow_up_required": {"type": "boolean"}
        },
        "required": ["patient_id", "age", "diagnosis", "medications", "allergies", "follow_up_required"]
    }
}]
```

This eliminates format failures entirely. The API enforces the schema at the wire level.

**Mechanism 2: Pydantic validation + targeted retry loop (if tool use unavailable)**

If you cannot use tool use, parse the response, validate with Pydantic, and retry with the specific error on failure:

```python
retry_prompt = f"""Your previous response failed schema validation with this error:
{validation_error}

The field "age" must be an integer (not a string like "forty-two").
The field "follow_up_required" must be a boolean (true/false, not "yes"/"no").

Try again. Respond with valid JSON only."""
```

Feeding back the exact Pydantic error is far more effective than a generic "try again."

**Mechanism 3: Fix truncation at the source**

Truncation is a `max_tokens` budget problem. For medical records up to 5,000 words, the JSON output can be ~400 tokens. Set `max_tokens=1024` minimum for extraction tasks. Monitor `stop_reason` — if it's `"max_tokens"` rather than `"end_turn"`, the response is incomplete by definition.

**Mechanism 4: Two-step pipeline for complex records**

For very long records, separate concerns: `generate → extract`.

- Step 1: Summarize the record in natural language (no schema pressure)
- Step 2: Extract structured fields from the summary (shorter, cleaner input)

This reduces truncation risk and reduces schema errors because the extraction model operates on cleaner input.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import json
import anthropic
from pydantic import BaseModel, ValidationError, field_validator
from typing import Optional

client = anthropic.Anthropic()

# --- Pydantic schema ---

class PatientRecord(BaseModel):
    patient_id: str
    age: int
    diagnosis: str
    medications: list[str]
    allergies: list[str]
    follow_up_required: bool

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v):
        if v <= 0 or v > 150:
            raise ValueError(f"Age {v} is not a valid human age")
        return v

    @field_validator("patient_id")
    @classmethod
    def patient_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("patient_id cannot be empty")
        return v.strip()


# --- Approach 1: Tool use (preferred) ---

EXTRACTION_TOOL = {
    "name": "extract_patient_data",
    "description": "Extract structured patient data from a medical record. "
                   "Use null/empty list for fields not found in the record.",
    "input_schema": {
        "type": "object",
        "properties": {
            "patient_id": {"type": "string", "description": "Patient identifier from the record"},
            "age": {"type": "integer", "description": "Patient age in years"},
            "diagnosis": {"type": "string", "description": "Primary diagnosis"},
            "medications": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of current medications"
            },
            "allergies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of known allergies. Empty list if none."
            },
            "follow_up_required": {
                "type": "boolean",
                "description": "True if the record indicates a follow-up appointment is needed"
            }
        },
        "required": ["patient_id", "age", "diagnosis", "medications", "allergies", "follow_up_required"]
    }
}

def extract_with_tool_use(medical_record: str) -> PatientRecord:
    """
    Primary extraction method. Uses tool use to force schema-valid output.
    The API-level schema enforcement eliminates format failures entirely.
    """
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "any"},  # Force a tool call — no free-form text
        messages=[{
            "role": "user",
            "content": f"Extract patient data from this medical record:\n\n{medical_record}"
        }]
    )

    # Find the tool use block
    tool_use_block = next(
        (block for block in response.content if block.type == "tool_use"),
        None
    )
    if tool_use_block is None:
        raise ValueError("No tool call in response despite tool_choice=any")

    # Validate with Pydantic (catches semantic issues the API schema can't)
    return PatientRecord(**tool_use_block.input)


# --- Approach 2: Retry loop with targeted error feedback (fallback) ---

EXTRACTION_PROMPT = """Extract structured data from this medical record. Respond with valid JSON only.
No markdown fences. No explanation. Just the JSON object.

Required schema:
{
  "patient_id": "string",
  "age": integer,
  "diagnosis": "string",
  "medications": ["string", ...],
  "allergies": ["string", ...],
  "follow_up_required": true or false
}

Example of a valid response:
{
  "patient_id": "PT-20491",
  "age": 45,
  "diagnosis": "Type 2 diabetes mellitus",
  "medications": ["Metformin 500mg", "Lisinopril 10mg"],
  "allergies": ["Penicillin"],
  "follow_up_required": true
}

Medical record:
{record}"""


def strip_json_fences(text: str) -> str:
    """Remove markdown code fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove opening fence (```json or ```)
        lines = lines[1:] if lines[0].startswith("```") else lines
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def extract_json_substring(text: str) -> str:
    """Try to extract a JSON object from text that has surrounding content."""
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")
    return text[start:end]


def extract_with_retry(medical_record: str, max_retries: int = 3) -> PatientRecord:
    """
    Fallback extraction method using a retry loop with targeted error feedback.
    """
    messages = [{
        "role": "user",
        "content": EXTRACTION_PROMPT.format(record=medical_record)
    }]

    last_error = None

    for attempt in range(max_retries):
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,  # Explicit budget — prevents truncation for typical records
            messages=messages
        )

        # Check for truncation — max_tokens hit means response is incomplete
        if response.stop_reason == "max_tokens":
            raise ValueError(
                "Response was truncated (stop_reason=max_tokens). "
                "Increase max_tokens or use the two-step pipeline for this record."
            )

        raw_text = response.content[0].text

        # Try to parse
        try:
            # Step 1: Strip markdown fences
            cleaned = strip_json_fences(raw_text)
            # Step 2: Extract JSON if surrounded by text
            json_str = extract_json_substring(cleaned)
            # Step 3: Parse JSON
            data = json.loads(json_str)
            # Step 4: Validate schema
            record = PatientRecord(**data)
            return record

        except json.JSONDecodeError as e:
            last_error = f"Invalid JSON syntax: {e}"
        except ValidationError as e:
            # Extract only the most actionable error messages
            errors = [f"  - {err['loc']}: {err['msg']}" for err in e.errors()]
            last_error = "Schema validation failed:\n" + "\n".join(errors)
        except Exception as e:
            last_error = f"Parsing error: {e}"

        # On failure: add assistant response and retry with targeted feedback
        messages.append({"role": "assistant", "content": raw_text})
        messages.append({
            "role": "user",
            "content": (
                f"Your response failed validation with this error:\n{last_error}\n\n"
                "Please try again. Return ONLY valid JSON — no markdown, no explanation.\n"
                "Pay attention to: age must be an integer (not a string), "
                "follow_up_required must be true or false (not 'yes'/'no'), "
                "medications and allergies must be arrays (use [] if empty)."
            )
        })

    raise ValueError(
        f"Failed to extract valid structured data after {max_retries} attempts. "
        f"Last error: {last_error}"
    )


# --- Two-step pipeline for long/complex records ---

def extract_with_two_step_pipeline(medical_record: str) -> PatientRecord:
    """
    For records too complex for direct extraction.
    Step 1: Summarize in natural language (no schema pressure).
    Step 2: Extract structured fields from the cleaner summary.
    """
    # Step 1: Summarize
    summary_response = client.messages.create(
        model="claude-haiku-4-5",  # Cheap model for summarization
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": (
                f"Summarize this medical record in plain language. "
                f"Include: patient ID, age, primary diagnosis, all medications, "
                f"all allergies, and whether a follow-up is required.\n\n{medical_record}"
            )
        }]
    )
    summary = summary_response.content[0].text

    # Step 2: Extract from summary (shorter, cleaner input → fewer errors)
    return extract_with_tool_use(summary)


# --- Main entrypoint with fallback chain ---

def extract_patient_record(medical_record: str) -> PatientRecord:
    """
    Full extraction pipeline with fallback chain:
    1. Try tool use (best: API-enforced schema)
    2. Fall back to retry loop (good: targeted error feedback)
    3. Fall back to two-step pipeline (handles complex/long records)
    """
    try:
        return extract_with_tool_use(medical_record)
    except Exception as e:
        print(f"Tool use failed ({e}), falling back to retry loop")

    try:
        return extract_with_retry(medical_record)
    except Exception as e:
        print(f"Retry loop failed ({e}), falling back to two-step pipeline")

    return extract_with_two_step_pipeline(medical_record)


if __name__ == "__main__":
    sample_record = """
    Patient: John Smith, ID: PT-48291
    DOB: 1978-03-15 (age 46)

    Chief complaint: Follow-up for hypertension management

    Diagnosis: Essential hypertension (I10), Type 2 diabetes mellitus (E11.9)

    Current medications:
    - Lisinopril 10mg daily
    - Metformin 1000mg twice daily
    - Atorvastatin 20mg at bedtime

    Allergies: Penicillin (hives), Sulfa drugs

    Plan: Continue current regimen. Follow-up in 3 months for HbA1c recheck.
    Blood pressure controlled. Recommend dietary counseling referral.
    """

    try:
        record = extract_patient_record(sample_record)
        print(f"Extracted record: {record.model_dump_json(indent=2)}")
    except Exception as e:
        print(f"Extraction failed: {e}")
```

</details>

---

## Interview Version

**Opening (20 seconds):** "8% failure rate in medical data extraction means 8% of patients have no record in your system. The prompt fix 'respond only with JSON' is already there — it's not a prompt problem. It's an architecture problem."

**Draw the failure taxonomy:**
```
Format failures (markdown fences, preamble):
  → Fix: tool use (API-level enforcement) or strip_json_fences() + json.loads()

Schema failures (wrong types, missing fields):
  → Fix: Pydantic validation + retry with specific error message

Truncation (response cut off mid-object):
  → Fix: increase max_tokens; check stop_reason == "max_tokens"
  → NOT fixable with prompting alone
```

**The key insight:** "JSON mode guarantees syntax. Tool use guarantees schema. These are different guarantees. Most teams confuse them and then wonder why JSON mode still breaks their downstream code."

**Medical data angle:** "For medical records, silent failures are worse than loud failures. The retry loop should log every failed attempt with the original record ID so nothing is silently dropped."

---

## Follow-up Questions

1. Your Pydantic model catches `age: "forty-two"` (string instead of int). But it does not catch `age: 420` (valid int, invalid human age). How would you extend the validation to catch semantic range errors, and where does Pydantic validation end and domain validation begin?
2. The retry loop feeds back the specific `ValidationError` to the model. Could this approach leak sensitive information from other patients' records back into the context? Under what circumstances, and how would you sanitize the retry feedback?
3. The two-step pipeline adds latency (two API calls) and cost. At what failure rate does the two-step pipeline become cheaper than paying for 3 retries on every complex record?
