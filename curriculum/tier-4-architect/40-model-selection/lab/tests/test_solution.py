"""Tests for Lab 40 — Model Benchmark Harness"""

import sys
import os
from pathlib import Path

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_caller(response_text="The answer is Paris.", latency=250.0, in_tokens=20, out_tokens=10):
    """Return a mock llm_caller that always returns the same values."""
    def caller(model: str, prompt: str):
        return response_text, latency, in_tokens, out_tokens
    return caller


# ---------------------------------------------------------------------------
# TestCase and BenchmarkResult dataclass imports
# ---------------------------------------------------------------------------

class TestDataClasses:
    def test_test_case_has_required_fields(self):
        from solution import TestCase
        tc = TestCase(prompt="Hello?", expected_keywords=["hello"])
        assert tc.prompt == "Hello?"
        assert tc.expected_keywords == ["hello"]

    def test_benchmark_result_has_required_fields(self):
        from solution import BenchmarkResult
        br = BenchmarkResult(
            model="gpt-4o-mini",
            test_case_id=0,
            response="test response",
            passed=True,
            latency_ms=200.0,
            input_tokens=15,
            output_tokens=5,
        )
        assert br.model == "gpt-4o-mini"
        assert br.passed is True
        assert br.latency_ms == 200.0


# ---------------------------------------------------------------------------
# evaluate_response
# ---------------------------------------------------------------------------

class TestEvaluateResponse:
    def test_all_keywords_present_returns_true(self):
        from solution import evaluate_response
        assert evaluate_response("Paris is the capital of France", ["paris", "france"]) is True

    def test_missing_keyword_returns_false(self):
        from solution import evaluate_response
        assert evaluate_response("London is in England", ["paris"]) is False

    def test_case_insensitive(self):
        from solution import evaluate_response
        assert evaluate_response("PARIS is a city", ["paris"]) is True
        assert evaluate_response("paris is a city", ["PARIS"]) is True

    def test_empty_keywords_returns_true(self):
        """No keywords to check → trivially all present."""
        from solution import evaluate_response
        assert evaluate_response("any response", []) is True

    def test_partial_match_is_not_enough(self):
        """All keywords must be present, not just some."""
        from solution import evaluate_response
        assert evaluate_response("Paris is a city", ["paris", "france"]) is False

    def test_returns_bool(self):
        from solution import evaluate_response
        result = evaluate_response("hello world", ["hello"])
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# run_benchmark
# ---------------------------------------------------------------------------

class TestRunBenchmark:
    def test_returns_list(self):
        from solution import run_benchmark, TestCase
        test_cases = [TestCase(prompt="Q?", expected_keywords=["a"])]
        models = ["model-a"]
        caller = make_mock_caller("The answer is a.")
        result = run_benchmark(test_cases, models, caller)
        assert isinstance(result, list)

    def test_one_result_per_model_per_test_case(self):
        """Should return len(models) × len(test_cases) results."""
        from solution import run_benchmark, TestCase
        test_cases = [
            TestCase("Q1?", ["answer"]),
            TestCase("Q2?", ["result"]),
        ]
        models = ["model-a", "model-b"]
        caller = make_mock_caller("answer and result")
        results = run_benchmark(test_cases, models, caller)
        assert len(results) == 4  # 2 models × 2 test cases

    def test_result_fields_populated(self):
        """Each BenchmarkResult should have all fields populated."""
        from solution import run_benchmark, TestCase, BenchmarkResult
        test_cases = [TestCase("What is Python?", ["python"])]
        models = ["claude-3-haiku-20240307"]
        caller = make_mock_caller("Python is a programming language.", 350.0, 18, 8)

        results = run_benchmark(test_cases, models, caller)
        assert len(results) == 1
        r = results[0]
        assert isinstance(r, BenchmarkResult)
        assert r.model == "claude-3-haiku-20240307"
        assert r.test_case_id == 0
        assert r.response == "Python is a programming language."
        assert r.latency_ms == 350.0
        assert r.input_tokens == 18
        assert r.output_tokens == 8

    def test_passed_true_when_keywords_present(self):
        from solution import run_benchmark, TestCase
        test_cases = [TestCase("Q?", ["capital", "paris"])]
        models = ["gpt-4o-mini"]
        caller = make_mock_caller("The capital is Paris.")
        results = run_benchmark(test_cases, models, caller)
        assert results[0].passed is True

    def test_passed_false_when_keywords_missing(self):
        from solution import run_benchmark, TestCase
        test_cases = [TestCase("Q?", ["london"])]
        models = ["gpt-4o-mini"]
        caller = make_mock_caller("Paris is the capital of France.")
        results = run_benchmark(test_cases, models, caller)
        assert results[0].passed is False

    def test_caller_called_with_correct_args(self):
        """llm_caller should be called with (model, prompt) for each combination."""
        from solution import run_benchmark, TestCase

        calls = []

        def tracking_caller(model, prompt):
            calls.append((model, prompt))
            return "response", 100.0, 5, 5

        test_cases = [TestCase("Hello?", ["response"])]
        models = ["model-x"]
        run_benchmark(test_cases, models, tracking_caller)

        assert len(calls) == 1
        assert calls[0] == ("model-x", "Hello?")


# ---------------------------------------------------------------------------
# summarize_benchmark
# ---------------------------------------------------------------------------

class TestSummarizeBenchmark:
    def _make_result(self, model, passed, latency=300.0, in_tok=100, out_tok=50, tc_id=0):
        from solution import BenchmarkResult
        return BenchmarkResult(
            model=model,
            test_case_id=tc_id,
            response="some response",
            passed=passed,
            latency_ms=latency,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )

    def test_returns_dict(self):
        from solution import summarize_benchmark
        results = [self._make_result("model-a", True)]
        summary = summarize_benchmark(results)
        assert isinstance(summary, dict)

    def test_keyed_by_model_name(self):
        from solution import summarize_benchmark
        results = [
            self._make_result("model-a", True),
            self._make_result("model-b", False),
        ]
        summary = summarize_benchmark(results)
        assert "model-a" in summary
        assert "model-b" in summary

    def test_accuracy_all_pass(self):
        """Accuracy should be 1.0 when all tests pass."""
        from solution import summarize_benchmark
        results = [
            self._make_result("model-a", True, tc_id=0),
            self._make_result("model-a", True, tc_id=1),
        ]
        summary = summarize_benchmark(results)
        assert summary["model-a"]["accuracy"] == 1.0

    def test_accuracy_none_pass(self):
        """Accuracy should be 0.0 when no tests pass."""
        from solution import summarize_benchmark
        results = [
            self._make_result("model-a", False, tc_id=0),
            self._make_result("model-a", False, tc_id=1),
        ]
        summary = summarize_benchmark(results)
        assert summary["model-a"]["accuracy"] == 0.0

    def test_accuracy_partial(self):
        """Accuracy should be 0.5 when half the tests pass."""
        from solution import summarize_benchmark
        results = [
            self._make_result("model-a", True, tc_id=0),
            self._make_result("model-a", False, tc_id=1),
        ]
        summary = summarize_benchmark(results)
        assert summary["model-a"]["accuracy"] == 0.5

    def test_avg_latency(self):
        """avg_latency_ms should be the mean of all result latencies."""
        from solution import summarize_benchmark
        results = [
            self._make_result("model-a", True, latency=200.0, tc_id=0),
            self._make_result("model-a", True, latency=400.0, tc_id=1),
        ]
        summary = summarize_benchmark(results)
        assert summary["model-a"]["avg_latency_ms"] == 300.0

    def test_summary_has_required_keys(self):
        """Each model summary must have accuracy, avg_latency_ms, total_cost_estimate."""
        from solution import summarize_benchmark
        results = [self._make_result("model-a", True)]
        summary = summarize_benchmark(results)
        assert "accuracy" in summary["model-a"]
        assert "avg_latency_ms" in summary["model-a"]
        assert "total_cost_estimate" in summary["model-a"]

    def test_cost_estimate_is_positive(self):
        """total_cost_estimate should be > 0 when tokens > 0."""
        from solution import summarize_benchmark
        results = [self._make_result("model-a", True, in_tok=1000, out_tok=500)]
        summary = summarize_benchmark(results)
        assert summary["model-a"]["total_cost_estimate"] > 0

    def test_multiple_models_independent(self):
        """Summaries for different models should be computed independently."""
        from solution import summarize_benchmark
        results = [
            self._make_result("model-a", True, latency=100.0, tc_id=0),
            self._make_result("model-b", False, latency=900.0, tc_id=0),
        ]
        summary = summarize_benchmark(results)
        assert summary["model-a"]["accuracy"] == 1.0
        assert summary["model-b"]["accuracy"] == 0.0
        assert summary["model-a"]["avg_latency_ms"] == 100.0
        assert summary["model-b"]["avg_latency_ms"] == 900.0
