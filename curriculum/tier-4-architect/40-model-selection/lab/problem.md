# Lab 40 — Model Benchmark Harness

## Problem Statement

You're evaluating which LLM to use for a new feature. Instead of guessing, you want to test systematically: run the same set of prompts through multiple models, check if responses meet acceptance criteria, measure latency and cost, and produce a comparison report.

Your task is to build the benchmark harness that powers this evaluation.

## Acceptance Criteria

- [ ] `evaluate_response(response, expected_keywords)` → `bool`
  - Returns `True` if ALL keywords appear in `response.lower()`
  - Returns `False` if any keyword is missing
- [ ] `run_benchmark(test_cases, models, llm_caller)` → `list[BenchmarkResult]`
  - Calls `llm_caller(model, prompt)` for every (model, test_case) combination
  - `llm_caller` returns `(response: str, latency_ms: float, input_tokens: int, output_tokens: int)`
  - Returns one `BenchmarkResult` per combination
- [ ] `summarize_benchmark(results)` → `dict`
  - Groups results by model name
  - For each model: computes `accuracy` (0.0–1.0), `avg_latency_ms`, `total_cost_estimate`
  - Returns `dict[str, dict]` keyed by model name
- [ ] All tests pass: `pytest tests/ -v`

## What Makes This Interesting

A benchmark harness with a pluggable `llm_caller` is a pattern you'll use throughout your career. By injecting the caller function, you can:
- Test against real models in production
- Mock the caller in unit tests (no API calls)
- Swap between APIs without changing the benchmark logic

This is also the foundation for continuous evaluation: run the harness on every deployment to catch model regressions.
