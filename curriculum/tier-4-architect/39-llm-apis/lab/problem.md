# Lab 39 — Cost Estimator CLI

## Problem Statement

You're building a cost-monitoring tool for an LLM-powered product. Before deciding which model to use for a given prompt, your tool should:

1. Accept a text string (the prompt/context you plan to send)
2. Count how many tokens it contains
3. Estimate the cost for sending that text to four different models with an assumed output token count
4. Print a formatted comparison table so engineers can make an informed model choice

## Acceptance Criteria

- [ ] `count_tokens(text, model)` → `int` — counts tokens using tiktoken
- [ ] `estimate_cost(input_tokens, output_tokens, model)` → `dict` with keys: `model`, `input_tokens`, `output_tokens`, `input_cost`, `output_cost`, `total_cost`
- [ ] `format_cost_table(estimates)` → `str` — a formatted text table with a header row containing `Model`
- [ ] `estimate_all_models(text, estimated_output_tokens)` → `list[dict]` sorted by `total_cost` ascending
- [ ] All tests pass: `pytest tests/ -v`

## Models to Support

| Model ID | Input ($/1M tokens) | Output ($/1M tokens) |
|----------|--------------------|--------------------|
| `claude-3-haiku-20240307` | $0.25 | $1.25 |
| `claude-3-5-sonnet-20241022` | $3.00 | $15.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |
| `gpt-4o` | $5.00 | $15.00 |

## What Makes This Interesting

Token counting and cost estimation are the foundation of any production LLM system. Engineers who can estimate costs before a request is sent can:
- Enforce per-user or per-feature cost budgets
- Automatically route to cheaper models when the request is simple
- Alert on unusually large context windows before they hit the API
