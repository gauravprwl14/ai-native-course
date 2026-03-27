import time
import statistics
from dataclasses import dataclass
from typing import Callable


@dataclass
class LatencyMeasurement:
    prompt: str
    ttft_ms: float       # time to first token (ms)
    total_ms: float      # total round-trip latency (ms)
    token_count: int     # approximate output token count


@dataclass
class BenchmarkStats:
    count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    min_ms: float
    max_ms: float


def measure_latency(llm_caller: Callable, prompt: str) -> LatencyMeasurement:
    """Measure latency for a single LLM call."""
    start = time.perf_counter()
    response, ttft_ms = llm_caller(prompt)
    total_ms = (time.perf_counter() - start) * 1000
    token_count = len(response.split())
    return LatencyMeasurement(
        prompt=prompt,
        ttft_ms=ttft_ms,
        total_ms=total_ms,
        token_count=token_count,
    )


def run_benchmark(llm_caller: Callable, prompts: list[str]) -> list[LatencyMeasurement]:
    """Run benchmark across all prompts."""
    return [measure_latency(llm_caller, prompt) for prompt in prompts]


def compute_stats(
    measurements: list[LatencyMeasurement], metric: str = "total_ms"
) -> BenchmarkStats:
    """Compute percentile statistics for a given metric."""
    values = sorted(getattr(m, metric) for m in measurements)
    n = len(values)
    p50 = values[int(0.50 * (n - 1))]
    p95 = values[int(0.95 * (n - 1))]
    p99 = values[int(0.99 * (n - 1))]
    return BenchmarkStats(
        count=n,
        p50_ms=p50,
        p95_ms=p95,
        p99_ms=p99,
        mean_ms=statistics.mean(values),
        min_ms=min(values),
        max_ms=max(values),
    )


def format_report(measurements: list[LatencyMeasurement]) -> str:
    """Format benchmark results as a plain-text table."""
    total_stats = compute_stats(measurements, "total_ms")
    ttft_stats = compute_stats(measurements, "ttft_ms")

    def _row(label: str, s: BenchmarkStats) -> str:
        return (
            f"{label:<10} | {s.p50_ms:>5.1f} | {s.p95_ms:>5.1f} | {s.p99_ms:>5.1f} "
            f"| {s.mean_ms:>5.1f} | {s.min_ms:>5.1f} | {s.max_ms:>5.1f}"
        )

    lines = [
        "LLM Latency Benchmark Report",
        "=============================",
        f"Requests: {len(measurements)}",
        "",
        f"{'Metric':<10} | {'p50':>5} | {'p95':>5} | {'p99':>5} | {'Mean':>5} | {'Min':>5} | {'Max':>5}",
        f"{'-'*10}-|-{'-'*5}-|-{'-'*5}-|-{'-'*5}-|-{'-'*5}-|-{'-'*5}-|-{'-'*5}",
        _row("total_ms", total_stats),
        _row("ttft_ms", ttft_stats),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time as _time

    def mock_llm(prompt: str) -> tuple[str, float]:
        _time.sleep(0.05)
        return "The answer is 42 words in this short response.", 25.0

    prompts = [f"Question {i}" for i in range(10)]
    measurements = run_benchmark(mock_llm, prompts)
    report = format_report(measurements)
    print(report)
