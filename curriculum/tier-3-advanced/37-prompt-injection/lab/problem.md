# Lab 37: Prompt Injection Security

## Problem

Prompt injection is the SQL injection of AI applications. Your task is to build a set of detection and defense functions that protect against both direct and indirect injection attacks.

## Functions to Implement

### `detect_injection_attempt(text: str) -> tuple[bool, list[str]]`

Check text against `INJECTION_PATTERNS`. Returns `(is_injection, matched_patterns)`. Case-insensitive.

### `sanitize_input(user_input: str) -> str`

Replace injection phrases with `"[REMOVED]"` using regex substitution. The resulting text is safe to embed in a prompt.

### `wrap_user_input(user_input: str) -> str`

Wrap the input in XML tags: `<user_input>{user_input}</user_input>`. Used to isolate user content from developer instructions in a prompt.

### `test_injection_resilience(system_prompt: str, injection_attempts: list[str]) -> dict`

Test a list of injection attempts. Returns `{"total": int, "blocked": int, "passed": int}` where `blocked` = attempts detected as injections.

## Files

- `starter/solution.py` — implement your solution here
- `solution/solution.py` — reference solution
- `tests/test_solution.py` — run with `pytest tests/ -v`

## Running Tests

```bash
cd curriculum/tier-3-advanced/37-prompt-injection/lab
pytest tests/ -v
```
