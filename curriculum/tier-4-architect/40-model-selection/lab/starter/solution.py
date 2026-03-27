"""
Lab 40 — Model Benchmark Harness
----------------------------------
Fill in the TODOs to complete this lab.

Run:  python solution.py
Test: cd .. && pytest tests/ -v
"""

from dataclasses import dataclass


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
    """Check if response contains all expected keywords (case insensitive).

    Args:
        response:          The model's response text.
        expected_keywords: All keywords that must appear in the response.

    Returns:
        True if ALL keywords appear in response.lower(), False otherwise.
    """
    # TODO: Return True if ALL expected_keywords appear in response.lower()
    # Hint: use all() with a generator expression
    pass


def run_benchmark(
    test_cases: list[TestCase],
    models: list[str],
    llm_caller,
) -> list[BenchmarkResult]:
    """Run all test cases against each model.

    Args:
        test_cases:  List of TestCase objects to evaluate.
        models:      List of model name strings.
        llm_caller:  Callable: (model: str, prompt: str) -> (response: str,
                     latency_ms: float, input_tokens: int, output_tokens: int)

    Returns:
        List of BenchmarkResult — one per (model, test_case) combination.
    """
    # TODO: For each model, for each test_case (with index i):
    #   1. Call llm_caller(model, test_case.prompt) to get (response, latency_ms, input_tokens, output_tokens)
    #   2. Call evaluate_response(response, test_case.expected_keywords) to get passed
    #   3. Create a BenchmarkResult and append to results list
    # TODO: Return the full results list
    pass


def summarize_benchmark(results: list[BenchmarkResult]) -> dict:
    """Summarize benchmark results by model.

    Args:
        results: List of BenchmarkResult objects from run_benchmark().

    Returns:
        dict keyed by model name. Each value is a dict with:
          - accuracy:            float (proportion of passed tests, 0.0 to 1.0)
          - avg_latency_ms:      float (average latency across all test cases)
          - total_cost_estimate: float (estimated USD cost for all test cases)

    For total_cost_estimate, use generic mid-tier pricing as an approximation:
        cost = total_input_tokens / 1_000_000 * 1.0
             + total_output_tokens / 1_000_000 * 3.0
    """
    # TODO: Group results by model name
    # TODO: For each model compute:
    #   - accuracy:  sum(r.passed for r in model_results) / len(model_results)
    #   - avg_latency_ms: average of r.latency_ms
    #   - total_cost_estimate: use the formula above
    # TODO: Return dict keyed by model name
    pass


if __name__ == "__main__":
    # Example with a mock LLM caller (no real API calls)
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
