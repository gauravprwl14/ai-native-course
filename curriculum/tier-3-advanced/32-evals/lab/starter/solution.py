"""Lab 32: LLM Evaluation — Exact Match, ROUGE-L, and Eval Pipeline"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from typing import Callable


def exact_match_score(prediction: str, reference: str) -> float:
    """Return 1.0 if prediction matches reference (case-insensitive, stripped), else 0.0.
    # TODO:
    # 1. Strip whitespace and lowercase both strings
    # 2. Return 1.0 if they are equal, else 0.0
    """
    raise NotImplementedError("Implement exact_match_score")


def rouge_l_score(prediction: str, reference: str) -> float:
    """Compute ROUGE-L F1 score between prediction and reference.
    Tokenizes by splitting on whitespace. Case-insensitive. Returns 0.0 if either is empty.
    # TODO:
    # 1. Tokenize: split prediction and reference on whitespace, lowercase both
    # 2. If either token list is empty, return 0.0
    # 3. Compute LCS length using 2D DP:
    #    - dp is a (len(pred)+1) x (len(ref)+1) table of zeros
    #    - For i in 1..len(pred), j in 1..len(ref):
    #        if pred_tokens[i-1] == ref_tokens[j-1]: dp[i][j] = dp[i-1][j-1] + 1
    #        else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    #    - lcs = dp[len(pred)][len(ref)]
    # 4. precision = lcs / len(pred_tokens)
    #    recall    = lcs / len(ref_tokens)
    # 5. If precision + recall == 0, return 0.0
    # 6. Return 2 * precision * recall / (precision + recall)
    """
    raise NotImplementedError("Implement rouge_l_score")


def run_eval(model_fn: Callable[[str], str], dataset: list[dict]) -> dict:
    """Run model_fn on each dataset item and score with rouge_l_score.
    Each dataset item has keys: "input" and "expected_output".
    Returns: {"scores": list[float], "mean_score": float, "results": list[dict]}
    # TODO:
    # 1. For each item in dataset:
    #    a. prediction = model_fn(item["input"])
    #    b. score = rouge_l_score(prediction, item["expected_output"])
    #    c. Append {"input": ..., "prediction": ..., "expected": ..., "score": ...}
    # 2. Compute mean_score = sum(scores) / len(scores), handle empty dataset (return 0.0)
    # 3. Return {"scores": scores, "mean_score": mean_score, "results": results}
    """
    raise NotImplementedError("Implement run_eval")


def compare_to_baseline(current_results: dict, baseline_results: dict) -> dict:
    """Compare current eval results to a baseline.
    Returns: {"current_mean", "baseline_mean", "delta", "regression": bool, "improvement": bool}
    # TODO:
    # 1. Extract mean_score from both dicts
    # 2. delta = current_mean - baseline_mean
    # 3. regression = delta < -0.02
    # 4. improvement = delta > 0.02
    # 5. Return the dict with all five fields
    """
    raise NotImplementedError("Implement compare_to_baseline")
