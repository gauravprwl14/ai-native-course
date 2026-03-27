"""
Lab 40 — Model Benchmark Harness (SOLUTION)
"""

from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TestCase:
    """A single benchmark test case."""
    prompt: str
    expected_keywords: list[str]  # response must contain ALL of these words (case-insensitive)


@dataclass
class BenchmarkResult:
    """Result for one model on one test case."""
    model: str
    test_case_id: int
    response: str
    passed: bool
    latency_ms: float
    input_tokens: int
    output_tokens: int


def evaluate_response(response: str, expected_keywords: list[str]) -> bool:
    """Check if response contains all expected keywords (case insensitive)."""
    return all(kw.lower() in response.lower() for kw in expected_keywords)


def run_benchmark(
    test_cases: list[TestCase],
    models: list[str],
    llm_caller,
) -> list[BenchmarkResult]:
    """Run all test cases against each model."""
    results = []
    for model in models:
        for i, test_case in enumerate(test_cases):
            response, latency_ms, input_tokens, output_tokens = llm_caller(model, test_case.prompt)
            passed = evaluate_response(response, test_case.expected_keywords)
            results.append(BenchmarkResult(
                model=model,
                test_case_id=i,
                response=response,
                passed=passed,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ))
    return results


def summarize_benchmark(results: list[BenchmarkResult]) -> dict:
    """Summarize benchmark results by model."""
    grouped = defaultdict(list)
    for r in results:
        grouped[r.model].append(r)

    summary = {}
    for model, model_results in grouped.items():
        total_input = sum(r.input_tokens for r in model_results)
        total_output = sum(r.output_tokens for r in model_results)
        cost_estimate = total_input / 1_000_000 * 1.0 + total_output / 1_000_000 * 3.0

        summary[model] = {
            "accuracy": sum(r.passed for r in model_results) / len(model_results),
            "avg_latency_ms": sum(r.latency_ms for r in model_results) / len(model_results),
            "total_cost_estimate": cost_estimate,
        }
    return summary


if __name__ == "__main__":
    def mock_llm_caller(model: str, prompt: str):
        """Mock caller that returns deterministic responses."""
        responses = {
            "claude-3-haiku-20240307": {
                "What is the capital of France?": "The capital of France is Paris.",
                "What language is Python?": "Python is a high-level programming language.",
            },
            "gpt-4o-mini": {
                "What is the capital of France?": "Paris is the capital city of France.",
                "What language is Python?": "Python is a general-purpose programming language.",
            },
        }
        response = responses.get(model, {}).get(prompt, "I don't know.")
        return response, 300.0, 20, len(response.split())

    test_cases = [
        TestCase(prompt="What is the capital of France?", expected_keywords=["paris"]),
        TestCase(prompt="What language is Python?", expected_keywords=["programming", "language"]),
    ]
    models = ["claude-3-haiku-20240307", "gpt-4o-mini"]

    results = run_benchmark(test_cases, models, mock_llm_caller)
    summary = summarize_benchmark(results)

    print("=== Benchmark Summary ===\n")
    for model, stats in summary.items():
        print(f"{model}:")
        print(f"  Accuracy:      {stats['accuracy']:.0%}")
        print(f"  Avg Latency:   {stats['avg_latency_ms']:.0f}ms")
        print(f"  Cost Estimate: ${stats['total_cost_estimate']:.6f}")
        print()
