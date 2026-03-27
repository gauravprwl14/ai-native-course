# Lab 36: Guardrails

## Problem

An unguarded LLM endpoint will eventually be misused. Your task is to build a composable guardrail pipeline that checks inputs before they reach the model and filters outputs before they reach the user.

## Functions to Implement

### `is_safe_input(text: str) -> tuple[bool, str]`

Check the input against `BLOCKED_PATTERNS` (regex). Returns `(True, "ok")` if safe, `(False, reason)` if a pattern matched.

### `is_on_topic(text: str, allowed_topics: list[str]) -> bool`

Ask an LLM whether the text is about one of the allowed topics. Returns `True` or `False`.

### `filter_output(response: str, max_length: int = 2000) -> str`

Trim the response to `max_length`. Try to cut at a sentence boundary.

### `GuardrailPipeline.run(user_input, model_response_fn) -> dict`

Compose all three checks. Returns:
```python
{"safe": bool, "response": str, "blocked_reason": str | None}
```

## Files

- `starter/solution.py` — implement your solution here
- `solution/solution.py` — reference solution
- `tests/test_solution.py` — run with `pytest tests/ -v`

## Running Tests

```bash
cd curriculum/tier-3-advanced/36-guardrails/lab
pytest tests/ -v
```
