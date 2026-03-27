# Lab 02 — Token Counter & Cost Estimator

## Problem Statement

You're building a cost-monitoring layer for an LLM-powered application. Before every API call, your system should:
1. Count how many tokens the planned request will use
2. Estimate the cost
3. Truncate text if it exceeds the context budget
4. Provide a breakdown of how text is tokenized (for debugging)

## Acceptance Criteria

- [ ] `count_tokens(text, encoding)` → int
- [ ] `estimate_cost(input_tokens, output_tokens, model)` → float in USD
- [ ] `truncate_to_tokens(text, max_tokens, encoding)` → string (≤ max_tokens when re-counted)
- [ ] `tokenize(text, encoding)` → list of token strings
- [ ] All tests pass

## What Makes This Interesting

Token counting is a microcosm of the cost-precision problem in AI systems. A system that sends 10% more tokens than necessary costs 10% more — at scale, that's thousands of dollars. Engineers who understand this build cheaper systems.
