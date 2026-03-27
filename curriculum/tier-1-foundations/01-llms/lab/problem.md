# Lab 01 — Your First LLM API Call

## Problem Statement

You work at a startup building an internal tool. Your first task is to integrate Claude into a Python script that:

1. Accepts a question from the user
2. Asks Claude the question at three different temperatures (0, 0.7, 1.0)
3. Prints each response so you can compare how temperature affects output
4. Reports the token count and estimated cost for each call

## Constraints

- Use the `anthropic` Python SDK (already in requirements.txt)
- Use `claude-haiku-4-5-20251001` (cheapest model — good for experiments)
- Must work with the `shared.utils` helper module
- Maximum 1024 output tokens per call

## Acceptance Criteria

- [ ] `call_claude(prompt, temperature)` returns a string response
- [ ] `compare_temperatures(prompt)` calls Claude 3 times and returns a dict with keys "0.0", "0.7", "1.0"
- [ ] `estimate_call_cost(input_tokens, output_tokens)` returns a float (USD)
- [ ] Running `python solution.py` prints all three responses without error
- [ ] All tests in `tests/test_solution.py` pass

## What Makes This Interesting

Temperature 0 gives deterministic, focused answers. Temperature 1.0 gives creative, varied answers. Seeing this difference concretely — with the same prompt — builds intuition you'll use when choosing parameters for production systems.

## Extension (optional)

Compare `claude-haiku-4-5-20251001` vs `claude-sonnet-4-6` on the same prompt. Notice the quality difference. Then calculate the cost difference. Is the quality worth the price?
