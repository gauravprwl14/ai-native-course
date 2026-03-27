"""Lab 32: LLM Evaluation — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from typing import Callable


def exact_match_score(prediction: str, reference: str) -> float:
    """Return 1.0 if prediction matches reference (case-insensitive, stripped), else 0.0."""
    return 1.0 if prediction.strip().lower() == reference.strip().lower() else 0.0


def _lcs_length(a: list, b: list) -> int:
    """Compute the Longest Common Subsequence length of two token lists using DP."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def rouge_l_score(prediction: str, reference: str) -> float:
    """Compute ROUGE-L F1 score between prediction and reference.
    Tokenizes by splitting on whitespace. Case-insensitive.
    Returns 0.0 if either string is empty.
    """
    pred_tokens = prediction.strip().lower().split()
    ref_tokens = reference.strip().lower().split()

    if not pred_tokens or not ref_tokens:
        return 0.0

    lcs = _lcs_length(pred_tokens, ref_tokens)
    precision = lcs / len(pred_tokens)
    recall = lcs / len(ref_tokens)

    if precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)


def run_eval(model_fn: Callable[[str], str], dataset: list[dict]) -> dict:
    """Run model_fn on each dataset item and score with rouge_l_score.
    Each dataset item: {"input": str, "expected_output": str}
    Returns: {"scores": list[float], "mean_score": float, "results": list[dict]}
    """
    results = []
    for item in dataset:
        prediction = model_fn(item["input"])
        score = rouge_l_score(prediction, item["expected_output"])
        results.append({
            "input": item["input"],
            "prediction": prediction,
            "expected": item["expected_output"],
            "score": score,
        })

    scores = [r["score"] for r in results]
    mean_score = sum(scores) / len(scores) if scores else 0.0

    return {
        "scores": scores,
        "mean_score": mean_score,
        "results": results,
    }


def compare_to_baseline(current_results: dict, baseline_results: dict) -> dict:
    """Compare current eval results to baseline.
    Returns: {"current_mean", "baseline_mean", "delta", "regression": bool, "improvement": bool}
    """
    current_mean = current_results["mean_score"]
    baseline_mean = baseline_results["mean_score"]
    delta = current_mean - baseline_mean

    return {
        "current_mean": current_mean,
        "baseline_mean": baseline_mean,
        "delta": delta,
        "regression": delta < -0.02,
        "improvement": delta > 0.02,
    }


if __name__ == "__main__":
    # Quick smoke test
    print("=== Exact Match ===")
    print(exact_match_score("Paris", "paris"))           # 1.0
    print(exact_match_score("Paris, France", "Paris"))   # 0.0

    print("\n=== ROUGE-L ===")
    print(rouge_l_score("the cat sat on the mat", "the cat sat on the mat"))  # 1.0
    print(rouge_l_score("the cat rested on a mat", "the cat sat on the mat")) # ~0.8
    print(rouge_l_score("", "reference"))                                      # 0.0

    print("\n=== Eval Pipeline ===")
    dataset = [
        {"input": "What is the capital of France?", "expected_output": "Paris"},
        {"input": "What is the capital of Germany?", "expected_output": "Berlin"},
    ]
    model = lambda q: q.split("capital of ")[-1].rstrip("?")
    results = run_eval(model, dataset)
    print(f"Mean score: {results['mean_score']:.3f}")

    baseline = run_eval(lambda q: "I don't know.", dataset)
    report = compare_to_baseline(results, baseline)
    print(f"Delta: {report['delta']:+.3f}, Regression: {report['regression']}")
