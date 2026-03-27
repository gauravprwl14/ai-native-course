"""Tests for Lab 32 — LLM Evaluation"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


# ---------------------------------------------------------------------------
# exact_match_score
# ---------------------------------------------------------------------------

class TestExactMatchScore:
    def test_identical_strings_return_one(self):
        from solution import exact_match_score
        assert exact_match_score("Paris", "Paris") == 1.0

    def test_case_insensitive_match(self):
        from solution import exact_match_score
        assert exact_match_score("paris", "PARIS") == 1.0

    def test_strip_whitespace_match(self):
        from solution import exact_match_score
        assert exact_match_score("  yes  ", "yes") == 1.0

    def test_different_strings_return_zero(self):
        from solution import exact_match_score
        assert exact_match_score("Paris, France", "Paris") == 0.0

    def test_returns_float(self):
        from solution import exact_match_score
        result = exact_match_score("hello", "hello")
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# rouge_l_score
# ---------------------------------------------------------------------------

class TestRougeLScore:
    def test_identical_strings_return_one(self):
        from solution import rouge_l_score
        assert rouge_l_score("the cat sat", "the cat sat") == pytest.approx(1.0)

    def test_empty_prediction_returns_zero(self):
        from solution import rouge_l_score
        assert rouge_l_score("", "the cat sat") == 0.0

    def test_empty_reference_returns_zero(self):
        from solution import rouge_l_score
        assert rouge_l_score("the cat sat", "") == 0.0

    def test_partial_overlap_between_zero_and_one(self):
        from solution import rouge_l_score
        score = rouge_l_score("the cat on mat", "the cat sat on the mat")
        assert 0.0 < score < 1.0

    def test_no_overlap_returns_zero(self):
        from solution import rouge_l_score
        score = rouge_l_score("apple banana cherry", "dog elephant fox")
        assert score == 0.0

    def test_returns_float(self):
        from solution import rouge_l_score
        result = rouge_l_score("hello world", "hello world")
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# run_eval
# ---------------------------------------------------------------------------

class TestRunEval:
    def test_returns_dict_with_required_keys(self):
        from solution import run_eval
        dataset = [{"input": "Q", "expected_output": "A"}]
        result = run_eval(lambda q: "A", dataset)
        assert "scores" in result
        assert "mean_score" in result
        assert "results" in result

    def test_mean_score_is_float(self):
        from solution import run_eval
        dataset = [{"input": "Q", "expected_output": "A"}]
        result = run_eval(lambda q: "A", dataset)
        assert isinstance(result["mean_score"], float)

    def test_scores_length_matches_dataset(self):
        from solution import run_eval
        dataset = [
            {"input": "Q1", "expected_output": "A1"},
            {"input": "Q2", "expected_output": "A2"},
        ]
        result = run_eval(lambda q: "A1", dataset)
        assert len(result["scores"]) == 2

    def test_perfect_model_mean_score_one(self):
        from solution import run_eval
        dataset = [
            {"input": "Q1", "expected_output": "perfect answer"},
            {"input": "Q2", "expected_output": "perfect answer"},
        ]
        result = run_eval(lambda q: "perfect answer", dataset)
        assert result["mean_score"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------

class TestCompareToBaseline:
    def test_returns_required_keys(self):
        from solution import compare_to_baseline
        current = {"mean_score": 0.7}
        baseline = {"mean_score": 0.65}
        result = compare_to_baseline(current, baseline)
        for key in ["current_mean", "baseline_mean", "delta", "regression", "improvement"]:
            assert key in result

    def test_improvement_detected(self):
        from solution import compare_to_baseline
        current = {"mean_score": 0.75}
        baseline = {"mean_score": 0.70}
        result = compare_to_baseline(current, baseline)
        assert result["improvement"] is True
        assert result["regression"] is False

    def test_regression_detected(self):
        from solution import compare_to_baseline
        current = {"mean_score": 0.55}
        baseline = {"mean_score": 0.70}
        result = compare_to_baseline(current, baseline)
        assert result["regression"] is True
        assert result["improvement"] is False

    def test_delta_computed_correctly(self):
        from solution import compare_to_baseline
        current = {"mean_score": 0.80}
        baseline = {"mean_score": 0.60}
        result = compare_to_baseline(current, baseline)
        assert result["delta"] == pytest.approx(0.20)
