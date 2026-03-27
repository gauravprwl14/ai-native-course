"""Tests for Lab 33 — LLM-as-Judge"""

import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock, call

_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def make_mock_response(text: str):
    """Create a mock Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


# ---------------------------------------------------------------------------
# score_response
# ---------------------------------------------------------------------------

class TestScoreResponse:
    def test_returns_dict(self):
        from solution import score_response
        scores_json = json.dumps({"helpfulness": 4, "accuracy": 5, "clarity": 4})
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(scores_json)
            result = score_response("What is ML?", "ML is machine learning.")
            assert isinstance(result, dict)

    def test_returns_rubric_keys(self):
        from solution import score_response, DEFAULT_RUBRIC
        scores_json = json.dumps({k: 3 for k in DEFAULT_RUBRIC})
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(scores_json)
            result = score_response("prompt", "response")
            for key in DEFAULT_RUBRIC:
                assert key in result

    def test_uses_temperature_zero(self):
        from solution import score_response
        scores_json = json.dumps({"helpfulness": 4, "accuracy": 5, "clarity": 4})
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(scores_json)
            score_response("prompt", "response")
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs.get("temperature") == 0

    def test_custom_rubric_used(self):
        from solution import score_response
        custom_rubric = {"tone": "Is the tone appropriate? (1-5)"}
        scores_json = json.dumps({"tone": 4})
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(scores_json)
            result = score_response("prompt", "response", rubric=custom_rubric)
            assert "tone" in result


# ---------------------------------------------------------------------------
# pairwise_judge
# ---------------------------------------------------------------------------

class TestPairwiseJudge:
    def test_returns_a_when_both_runs_agree_a_wins(self):
        from solution import pairwise_judge
        # Run 1: A first → judge says A
        # Run 2: B first → judge says B (meaning A won in original labeling)
        responses = iter([
            make_mock_response("A"),  # run 1: A first → A wins
            make_mock_response("B"),  # run 2: B first → judge said B = original B → inverted to A
        ])
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.side_effect = lambda **kwargs: next(responses)
            result = pairwise_judge("prompt", "response A", "response B")
            assert result == "A"

    def test_returns_tie_when_runs_disagree(self):
        from solution import pairwise_judge
        # Run 1: A first → judge says A
        # Run 2: B first → judge says A (first shown = B) → inverted to B
        # Run 1 says A, Run 2 says B → disagree → tie
        responses = iter([
            make_mock_response("A"),  # run 1: A first → A wins
            make_mock_response("A"),  # run 2: B first → judge says A (position bias toward first) → inverted to B
        ])
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.side_effect = lambda **kwargs: next(responses)
            result = pairwise_judge("prompt", "response A", "response B")
            assert result == "tie"

    def test_calls_api_twice(self):
        from solution import pairwise_judge
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("A")
            pairwise_judge("prompt", "response A", "response B")
            assert mock_client.messages.create.call_count == 2

    def test_returns_string(self):
        from solution import pairwise_judge
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("A")
            result = pairwise_judge("prompt", "response A", "response B")
            assert isinstance(result, str)


# ---------------------------------------------------------------------------
# run_judge_eval
# ---------------------------------------------------------------------------

class TestRunJudgeEval:
    def test_returns_required_keys(self):
        from solution import run_judge_eval
        scores_json = json.dumps({"helpfulness": 4, "accuracy": 5, "clarity": 4})
        with patch('solution.score_response', return_value={"helpfulness": 4, "accuracy": 5, "clarity": 4}):
            result = run_judge_eval([{"prompt": "Q", "response": "A"}])
            assert "avg_scores" in result
            assert "results" in result

    def test_results_length_matches_dataset(self):
        from solution import run_judge_eval
        with patch('solution.score_response', return_value={"helpfulness": 4, "accuracy": 5, "clarity": 4}):
            dataset = [
                {"prompt": "Q1", "response": "A1"},
                {"prompt": "Q2", "response": "A2"},
            ]
            result = run_judge_eval(dataset)
            assert len(result["results"]) == 2

    def test_avg_scores_has_rubric_dimensions(self):
        from solution import run_judge_eval, DEFAULT_RUBRIC
        with patch('solution.score_response', return_value={k: 3 for k in DEFAULT_RUBRIC}):
            result = run_judge_eval([{"prompt": "Q", "response": "A"}])
            for dim in DEFAULT_RUBRIC:
                assert dim in result["avg_scores"]

    def test_avg_scores_computed_correctly(self):
        from solution import run_judge_eval
        # Two items, helpfulness scores 2 and 4 → avg 3.0
        scores_list = [
            {"helpfulness": 2, "accuracy": 3, "clarity": 3},
            {"helpfulness": 4, "accuracy": 3, "clarity": 3},
        ]
        call_count = [0]

        def mock_score(*args, **kwargs):
            idx = call_count[0]
            call_count[0] += 1
            return scores_list[idx]

        with patch('solution.score_response', side_effect=mock_score):
            dataset = [
                {"prompt": "Q1", "response": "A1"},
                {"prompt": "Q2", "response": "A2"},
            ]
            result = run_judge_eval(dataset)
            assert result["avg_scores"]["helpfulness"] == pytest.approx(3.0)
