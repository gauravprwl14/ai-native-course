import sys
import time
import statistics
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

from solution import (
    LatencyMeasurement,
    BenchmarkStats,
    measure_latency,
    run_benchmark,
    compute_stats,
    format_report,
)


def make_mock_llm(response: str = "hello world", ttft_ms: float = 50.0, sleep_s: float = 0.0):
    """Create a deterministic mock llm_caller."""
    def _caller(prompt: str) -> tuple[str, float]:
        if sleep_s > 0:
            time.sleep(sleep_s)
        return response, ttft_ms
    return _caller


def make_measurements(total_ms_values: list[float], ttft_ms_values: list[float] = None):
    """Create LatencyMeasurement objects with given total_ms values."""
    if ttft_ms_values is None:
        ttft_ms_values = [v * 0.25 for v in total_ms_values]
    return [
        LatencyMeasurement(
            prompt=f"prompt_{i}",
            ttft_ms=ttft_ms_values[i],
            total_ms=total_ms_values[i],
            token_count=10,
        )
        for i in range(len(total_ms_values))
    ]


class TestMeasureLatency(unittest.TestCase):
    def test_returns_latency_measurement_type(self):
        caller = make_mock_llm()
        result = measure_latency(caller, "Hello")
        self.assertIsInstance(result, LatencyMeasurement)

    def test_prompt_is_stored(self):
        caller = make_mock_llm()
        result = measure_latency(caller, "test prompt")
        self.assertEqual(result.prompt, "test prompt")

    def test_ttft_ms_matches_caller_return(self):
        caller = make_mock_llm(ttft_ms=123.4)
        result = measure_latency(caller, "Hello")
        self.assertAlmostEqual(result.ttft_ms, 123.4, places=1)

    def test_total_ms_is_positive(self):
        caller = make_mock_llm()
        result = measure_latency(caller, "Hello")
        self.assertGreater(result.total_ms, 0)

    def test_total_ms_reflects_sleep(self):
        caller = make_mock_llm(sleep_s=0.05)
        result = measure_latency(caller, "Hello")
        # Should be at least 50ms but not more than 500ms (generous bound)
        self.assertGreater(result.total_ms, 40)
        self.assertLess(result.total_ms, 500)

    def test_token_count_is_word_count_of_response(self):
        caller = make_mock_llm(response="one two three four five")
        result = measure_latency(caller, "Hello")
        self.assertEqual(result.token_count, 5)


class TestRunBenchmark(unittest.TestCase):
    def test_returns_correct_number_of_measurements(self):
        caller = make_mock_llm()
        prompts = ["a", "b", "c"]
        results = run_benchmark(caller, prompts)
        self.assertEqual(len(results), 3)

    def test_each_measurement_has_correct_prompt(self):
        caller = make_mock_llm()
        prompts = ["first", "second", "third"]
        results = run_benchmark(caller, prompts)
        self.assertEqual([r.prompt for r in results], prompts)

    def test_empty_prompts_returns_empty_list(self):
        caller = make_mock_llm()
        results = run_benchmark(caller, [])
        self.assertEqual(results, [])

    def test_all_measurements_are_latency_measurement_type(self):
        caller = make_mock_llm()
        results = run_benchmark(caller, ["a", "b"])
        for r in results:
            self.assertIsInstance(r, LatencyMeasurement)


class TestComputeStats(unittest.TestCase):
    def test_basic_stats_on_known_values(self):
        # 5 values: 100, 200, 300, 400, 500
        ms = [100.0, 200.0, 300.0, 400.0, 500.0]
        measurements = make_measurements(ms)
        stats = compute_stats(measurements, "total_ms")

        self.assertIsInstance(stats, BenchmarkStats)
        self.assertEqual(stats.count, 5)
        self.assertAlmostEqual(stats.min_ms, 100.0, places=1)
        self.assertAlmostEqual(stats.max_ms, 500.0, places=1)
        self.assertAlmostEqual(stats.mean_ms, 300.0, places=1)

    def test_p50_is_median(self):
        ms = [100.0, 200.0, 300.0, 400.0, 500.0]
        measurements = make_measurements(ms)
        stats = compute_stats(measurements, "total_ms")
        # p50 should be around the median (300)
        self.assertAlmostEqual(stats.p50_ms, 300.0, places=0)

    def test_p99_approaches_max_for_small_samples(self):
        ms = [100.0, 200.0, 300.0, 400.0, 500.0]
        measurements = make_measurements(ms)
        stats = compute_stats(measurements, "total_ms")
        # p99 index = int(0.99 * 4) = 3, so sorted[3] = 400
        self.assertLessEqual(stats.p99_ms, stats.max_ms)
        self.assertGreaterEqual(stats.p99_ms, stats.p50_ms)

    def test_ttft_metric_is_used(self):
        total = [100.0, 200.0, 300.0]
        ttft = [10.0, 20.0, 30.0]
        measurements = make_measurements(total, ttft)
        stats = compute_stats(measurements, "ttft_ms")
        self.assertAlmostEqual(stats.min_ms, 10.0, places=1)
        self.assertAlmostEqual(stats.max_ms, 30.0, places=1)

    def test_single_measurement(self):
        measurements = make_measurements([250.0])
        stats = compute_stats(measurements, "total_ms")
        self.assertEqual(stats.count, 1)
        self.assertAlmostEqual(stats.p50_ms, 250.0, places=1)
        self.assertAlmostEqual(stats.p95_ms, 250.0, places=1)
        self.assertAlmostEqual(stats.p99_ms, 250.0, places=1)

    def test_percentiles_are_ordered(self):
        ms = list(range(100, 200))  # 100 values: 100..199
        measurements = make_measurements([float(v) for v in ms])
        stats = compute_stats(measurements, "total_ms")
        self.assertLessEqual(stats.p50_ms, stats.p95_ms)
        self.assertLessEqual(stats.p95_ms, stats.p99_ms)


class TestFormatReport(unittest.TestCase):
    def setUp(self):
        ms = [100.0, 200.0, 300.0, 400.0, 500.0]
        ttft = [25.0, 50.0, 75.0, 100.0, 125.0]
        self.measurements = make_measurements(ms, ttft)
        self.report = format_report(self.measurements)

    def test_report_is_string(self):
        self.assertIsInstance(self.report, str)

    def test_report_contains_header(self):
        self.assertIn("LLM Latency Benchmark Report", self.report)

    def test_report_contains_request_count(self):
        self.assertIn("5", self.report)  # "Requests: 5"

    def test_report_contains_total_ms_row(self):
        self.assertIn("total_ms", self.report)

    def test_report_contains_ttft_ms_row(self):
        self.assertIn("ttft_ms", self.report)

    def test_report_contains_p95_column(self):
        self.assertIn("p95", self.report)

    def test_report_contains_p99_column(self):
        self.assertIn("p99", self.report)

    def test_single_measurement_report(self):
        measurements = make_measurements([300.0], [75.0])
        report = format_report(measurements)
        self.assertIn("1", report)  # Requests: 1
        self.assertIn("total_ms", report)


if __name__ == "__main__":
    unittest.main()
