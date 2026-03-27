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
    """Measure latency for a single LLM call.

    Args:
        llm_caller: callable(prompt) -> (response_text: str, ttft_ms: float)
        prompt: the prompt string to send

    Returns:
        LatencyMeasurement with prompt, ttft_ms, total_ms, token_count
    """
    # TODO: Record start time using time.perf_counter()
    # TODO: Call llm_caller(prompt) — it returns (response_text, ttft_ms)
    # TODO: Record end time using time.perf_counter()
    # TODO: Calculate total_ms = (end - start) * 1000
    # TODO: Estimate token_count = len(response_text.split())
    # TODO: Return a LatencyMeasurement dataclass
    pass


def run_benchmark(llm_caller: Callable, prompts: list[str]) -> list[LatencyMeasurement]:
    """Run benchmark across all prompts.

    Args:
        llm_caller: callable(prompt) -> (response_text, ttft_ms)
        prompts: list of prompt strings

    Returns:
        List of LatencyMeasurement, one per prompt
    """
    # TODO: Call measure_latency(llm_caller, prompt) for each prompt in prompts
    # TODO: Collect and return all measurements as a list
    pass


def compute_stats(
    measurements: list[LatencyMeasurement], metric: str = "total_ms"
) -> BenchmarkStats:
    """Compute percentile statistics for a given metric.

    Args:
        measurements: list of LatencyMeasurement objects
        metric: attribute name to extract — "total_ms" or "ttft_ms"

    Returns:
        BenchmarkStats with p50, p95, p99, mean, min, max
    """
    # TODO: Extract metric values: [getattr(m, metric) for m in measurements]
    # TODO: Sort the values list
    # TODO: Compute p50: sorted_values[int(0.50 * (n-1))]
    # TODO: Compute p95: sorted_values[int(0.95 * (n-1))]
    # TODO: Compute p99: sorted_values[int(0.99 * (n-1))]
    # TODO: Compute mean using statistics.mean() or sum/len
    # TODO: Compute min and max
    # TODO: Return BenchmarkStats
    pass


def format_report(measurements: list[LatencyMeasurement]) -> str:
    """Format benchmark results as a plain-text table.

    Args:
        measurements: list of LatencyMeasurement objects

    Returns:
        Formatted string report
    """
    # TODO: Call compute_stats(measurements, "total_ms") for total latency stats
    # TODO: Call compute_stats(measurements, "ttft_ms") for TTFT stats
    # TODO: Build report string with:
    #   - Header: "LLM Latency Benchmark Report"
    #   - Separator: "============================="
    #   - Line: "Requests: N"
    #   - Empty line
    #   - Column header: "Metric     |   p50 |   p95 |   p99 |  Mean |   Min |   Max"
    #   - Separator line: "-----------|-------|-------|-------|-------|-------|------"
    #   - Row for total_ms with values formatted to 1 decimal place
    #   - Row for ttft_ms with values formatted to 1 decimal place
    # TODO: Return the complete formatted string
    pass


# ---------------------------------------------------------------------------
# Manual smoke test — demonstrates expected behaviour
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import time as _time

    def mock_llm(prompt: str) -> tuple[str, float]:
        _time.sleep(0.05)  # 50ms simulated latency
        return "The answer is 42 words in this short response.", 25.0

    prompts = [f"Question {i}" for i in range(10)]
    measurements = run_benchmark(mock_llm, prompts)
    report = format_report(measurements)
    print(report)
