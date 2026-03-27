# Chapter 45 Lab — LLM Latency Profiler

## Goal

Build a benchmarking tool that measures the latency of any LLM caller. The profiler captures TTFT (time to first token) and total latency per request, aggregates across N requests, and outputs a p50/p95/p99 summary report.

## Tasks

1. **`measure_latency(llm_caller, prompt)`** — Call `llm_caller(prompt)` which returns `(response_text, ttft_ms)`. Time the full call with `time.perf_counter()`. Estimate token count as `len(response.split())`. Return a `LatencyMeasurement`.

2. **`run_benchmark(llm_caller, prompts)`** — Call `measure_latency` for each prompt in the list. Return all measurements as a list.

3. **`compute_stats(measurements, metric="total_ms")`** — Extract the metric values from all measurements (e.g., `[m.total_ms for m in measurements]`). Sort them. Compute p50, p95, p99 using sorted-index arithmetic or `statistics.quantiles`. Compute mean, min, max. Return a `BenchmarkStats`.

4. **`format_report(measurements)`** — Call `compute_stats` for both `"total_ms"` and `"ttft_ms"`. Format a plain-text report with a header line showing request count, and a table with columns: `Metric | p50 | p95 | p99 | Mean | Min | Max`. Return the formatted string.

## The `llm_caller` Contract

```python
def llm_caller(prompt: str) -> tuple[str, float]:
    """
    Returns:
        response_text: full generated response
        ttft_ms: simulated or real time-to-first-token in milliseconds
    """
```

## Constraints

- Use only Python standard library (`time`, `statistics`, `dataclasses`).
- No API calls — use mock callers in tests and the smoke test.
- `compute_stats` must handle edge cases: single measurement, all identical values.

## Expected Behaviour

```python
import time

def mock_llm(prompt: str) -> tuple[str, float]:
    time.sleep(0.1)  # simulate 100ms latency
    return "The answer is 42.", 50.0  # (response, ttft_ms)

prompts = ["Q1", "Q2", "Q3", "Q4", "Q5"]
measurements = run_benchmark(mock_llm, prompts)
report = format_report(measurements)
print(report)
```

Output (approximate — actual timings vary):
```
LLM Latency Benchmark Report
=============================
Requests: 5

Metric     |   p50 |   p95 |   p99 |  Mean |   Min |   Max
-----------|-------|-------|-------|-------|-------|------
total_ms   | 100.x | 100.x | 100.x | 100.x | 100.x | 100.x
ttft_ms    |  50.0 |  50.0 |  50.0 |  50.0 |  50.0 |  50.0
```

## Files

| File | Purpose |
|------|---------|
| `starter/solution.py` | Skeleton with `# TODO:` comments |
| `solution/solution.py` | Reference implementation |
| `tests/test_solution.py` | Pytest tests (mocked, no real LLM) |
