# Lab 13: Role + Meta Prompting — Auto-generate Prompt Variants

## Background

Writing good prompts is hard. Meta-prompting is the practice of using an LLM to write prompts for you. Combined with role prompting — assigning an expert persona — meta-prompting can generate high-quality, domain-aware prompts faster than hand-crafting each one.

In this lab you will build a pipeline that:
1. Applies a role to a task and calls the LLM
2. Uses a meta-prompt to generate N diverse prompt variants for a task
3. Evaluates each variant by checking whether expected keywords appear in the LLM's responses

This is the core workflow for prompt library building and A/B prompt testing.

## Your Task

Implement three functions in `starter/solution.py`:

---

### Function 1: `apply_role_prompt(task, role_description) -> str`

Wrap a user task with a role in the system prompt and return the model's text response.

**Requirements:**
- Build a system prompt: `"You are {role_description}."`
- Call the Anthropic API with `temperature=0.3`, the system prompt, and the task as the user message
- Return the response text as a string

**Example:**
```python
response = apply_role_prompt(
    task="Review this code for bugs: def add(a, b): return a - b",
    role_description="a senior Python engineer reviewing code for correctness"
)
# => "I found a bug: the function subtracts instead of adds. ..."
```

---

### Function 2: `generate_prompt_variants(task_description, n=5) -> list[str]`

Use a meta-prompt to generate N diverse prompt variants for a task.

**Requirements:**
- Format `META_PROMPT_TEMPLATE` with `n` and `task_description`
- Call the API with `temperature=0.8` (high temperature encourages diverse variants)
- Split the response by `"---"` to get individual variants
- Strip whitespace and remove leading numbering from each variant
- Return a list of exactly `n` prompts (truncate if the model produces more, pad with an empty string if fewer)

**Example:**
```python
variants = generate_prompt_variants("Explain Python list comprehensions", n=3)
# => [
#   "You are a Python educator...",
#   "You are a senior engineer doing code review...",
#   "You are a technical writer..."
# ]
```

---

### Function 3: `evaluate_prompt(prompt, test_cases) -> float`

Evaluate a prompt against a list of test cases using keyword matching.

Each test case is a dict:
```python
{"input": str, "expected_keywords": list[str]}
```

**Requirements:**
- For each test case:
  - Build the full prompt: `full_prompt = prompt + "\n\n" + test_case["input"]`
  - Call the API and get the response text
  - Check whether ALL `expected_keywords` appear in the response (case-insensitive)
- Return `count_passed / len(test_cases)` as a float

**Examples:**
- 3 test cases, all pass → `1.0`
- 3 test cases, 2 pass → `0.667`
- 3 test cases, 0 pass → `0.0`

---

## Running the Lab

```bash
cd curriculum/tier-2-builder/13-role-meta-prompting/lab/starter
python solution.py
```

## Running Tests

```bash
cd curriculum/tier-2-builder/13-role-meta-prompting/lab
pytest tests/ -v
```

## Acceptance Criteria

- [ ] `apply_role_prompt` returns a string
- [ ] `apply_role_prompt` sets "You are {role_description}." as the system prompt
- [ ] `generate_prompt_variants` returns a list
- [ ] `generate_prompt_variants` calls the API with `temperature >= 0.7`
- [ ] `evaluate_prompt` returns a float between 0.0 and 1.0
- [ ] `evaluate_prompt` returns `1.0` when all keywords are present in every response
- [ ] `evaluate_prompt` returns `0.0` when no keywords match any response
- [ ] `evaluate_prompt` handles multiple test cases correctly
