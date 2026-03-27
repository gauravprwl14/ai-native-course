# Lab 04 — Compare Outputs at Different Temperatures

## Overview

In this lab you'll build a module that demonstrates how temperature affects LLM output. You'll call the Anthropic API at multiple temperature settings for the same prompt and observe how the outputs differ.

---

## Functions to Implement

### 1. `generate_at_temperature(prompt, temperature, n=3) -> list[str]`

Call the Anthropic API `n` times with the provided `prompt` and `temperature`, collecting all responses.

**Requirements:**
- Use `claude-haiku-4-5-20251001` as the model
- Set `max_tokens=300`
- Pass the exact `temperature` value to the API
- Make exactly `n` separate API calls
- Return a list of `n` response strings (the text content of each response)

**Example:**
```python
responses = generate_at_temperature("Name a color.", temperature=0.0, n=3)
# At temperature=0.0, all 3 responses will likely be identical
# e.g. ["Blue", "Blue", "Blue"]

responses = generate_at_temperature("Name a color.", temperature=1.2, n=3)
# At temperature=1.2, responses will vary
# e.g. ["Blue", "Red", "Violet"]
```

---

### 2. `compare_temperatures(prompt, temperatures=[0.0, 0.5, 1.0]) -> dict[float, list[str]]`

Run `generate_at_temperature` for each value in `temperatures` (using the default `n=3`) and collect the results.

**Requirements:**
- Iterate over every temperature in the `temperatures` list
- For each temperature, call `generate_at_temperature` with `n=3`
- Return a dict mapping each temperature (float) to its list of responses
- The returned dict must have exactly `len(temperatures)` keys

**Example:**
```python
results = compare_temperatures("Name an animal.", temperatures=[0.0, 1.0])
# Returns:
# {
#   0.0: ["Dog", "Dog", "Dog"],
#   1.0: ["Cat", "Elephant", "Parrot"]
# }
```

---

### 3. `is_valid_json_output(text) -> bool`

Attempt to parse `text` as JSON. Return `True` if it succeeds, `False` if it raises any exception.

**Requirements:**
- Use `json.loads(text)` to attempt parsing
- Return `True` if parsing succeeds (no exception)
- Return `False` if any exception is raised (including `json.JSONDecodeError`, `TypeError`, etc.)
- Do not raise exceptions — always return a bool

**Example:**
```python
is_valid_json_output('{"name": "Alice", "age": 30}')  # True
is_valid_json_output('[1, 2, 3]')                      # True
is_valid_json_output('not json at all')                # False
is_valid_json_output('')                               # False
is_valid_json_output('{"broken": }')                   # False
```

---

## Files

| File | Description |
|------|-------------|
| `starter/solution.py` | Scaffold with `# TODO:` markers — edit this file |
| `solution/solution.py` | Complete reference implementation |
| `tests/test_solution.py` | Automated tests using mocks (no real API calls needed) |

---

## Running the Lab

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run your implementation
cd curriculum/tier-1-foundations/04-temperature/lab/starter
python solution.py

# Run tests (from the lab/ directory)
cd curriculum/tier-1-foundations/04-temperature/lab
pytest tests/ -v
```

---

## Acceptance Criteria

- [ ] `generate_at_temperature` returns a list of exactly `n` strings
- [ ] `generate_at_temperature` passes the correct `temperature` to every API call
- [ ] `compare_temperatures` returns a dict with one key per temperature
- [ ] Each dict value is a list of 3 strings
- [ ] `is_valid_json_output` returns `True` for valid JSON strings
- [ ] `is_valid_json_output` returns `False` for invalid or empty strings
- [ ] All tests pass: `pytest tests/ -v`
