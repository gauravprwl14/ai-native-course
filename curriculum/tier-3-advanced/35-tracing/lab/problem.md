# Lab 35: Tracing & Observability

## Problem

Production AI pipelines fail silently. Your task is to build a lightweight tracing system that records latency, token usage, and cost for every step in an AI pipeline.

## What to Implement

### `calculate_cost_from_trace(trace: Trace) -> float`

Calculate total USD cost from all spans in a trace. Use `COST_PER_1K_TOKENS` for pricing. Skip spans with unknown models.

### `create_span(name: str, fn, *args, **kwargs) -> tuple[Span, any]`

Execute `fn(*args, **kwargs)`, record the latency in milliseconds, and catch any exceptions (storing the error message in `span.error`). Return `(span, result)`. Return `(span, None)` if an exception occurs.

## Files

- `starter/solution.py` — implement your solution here
- `solution/solution.py` — reference solution
- `tests/test_solution.py` — run with `pytest tests/ -v`

## Running Tests

```bash
cd curriculum/tier-3-advanced/35-tracing/lab
pytest tests/ -v
```
