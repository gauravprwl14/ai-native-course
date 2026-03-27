"""
Tests for Lab 10 — Chain-of-Thought Prompting
These tests verify the function signatures and logic WITHOUT making real API calls.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, call

# Add starter (or solution for CI) to path so we test the learner's code.
# Set LAB_TARGET=solution to run tests against the reference solution.
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def make_mock_response(text: str):
    """Create a mock Anthropic API response with the given text."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


COT_RESPONSE_42 = (
    "First, I need to calculate 6 × 7 = 42.\n"
    "Therefore, the answer is: 42"
)

COT_RESPONSE_17 = (
    "Step 1: 4 × 6 = 24 apples total.\n"
    "Step 2: 24 - 7 = 17 good apples.\n"
    "Therefore, the answer is: 17"
)

NO_ANSWER_RESPONSE = "I'm not sure how to solve this problem."

DECIMAL_RESPONSE = (
    "60 mph × 2.5 h = 150 miles. 80 mph × 1.5 h = 120 miles. "
    "150 + 120 = 270. Therefore, the answer is: 270.5"
)


class TestSolveWithCot:
    def test_returns_string(self):
        """solve_with_cot() must return a string."""
        from solution import solve_with_cot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(COT_RESPONSE_42)

            result = solve_with_cot("What is 6 times 7?")
            assert isinstance(result, str)

    def test_returns_full_response_text(self):
        """solve_with_cot() must return the full response text including reasoning."""
        from solution import solve_with_cot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(COT_RESPONSE_42)

            result = solve_with_cot("What is 6 times 7?")
            assert result == COT_RESPONSE_42

    def test_calls_api_with_temperature_zero(self):
        """solve_with_cot() must use temperature=0 for deterministic output."""
        from solution import solve_with_cot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(COT_RESPONSE_42)

            solve_with_cot("test problem")
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs.get('temperature') == 0


class TestExtractAnswer:
    def test_extracts_integer_answer(self):
        """extract_answer() must return the number from the 'Therefore' line."""
        from solution import extract_answer

        result = extract_answer(COT_RESPONSE_42)
        assert result == "42"

    def test_returns_none_when_pattern_not_found(self):
        """extract_answer() must return None when the pattern is absent."""
        from solution import extract_answer

        result = extract_answer(NO_ANSWER_RESPONSE)
        assert result is None

    def test_extracts_decimal_answer(self):
        """extract_answer() must handle decimal numbers."""
        from solution import extract_answer

        result = extract_answer(DECIMAL_RESPONSE)
        assert result == "270.5"

    def test_extracts_from_multiline_response(self):
        """extract_answer() must find the pattern anywhere in a multi-line response."""
        from solution import extract_answer

        result = extract_answer(COT_RESPONSE_17)
        assert result == "17"


class TestSolveWithSelfConsistency:
    def test_calls_api_n_times(self):
        """solve_with_self_consistency() must call the API exactly n times."""
        from solution import solve_with_self_consistency

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(COT_RESPONSE_42)

            solve_with_self_consistency("test problem", n=3)
            assert mock_client.messages.create.call_count == 3

    def test_returns_most_common_answer(self):
        """solve_with_self_consistency() must return the majority vote answer."""
        from solution import solve_with_self_consistency

        responses = [
            make_mock_response(COT_RESPONSE_42),   # 42
            make_mock_response(COT_RESPONSE_42),   # 42
            make_mock_response(COT_RESPONSE_17),   # 17
            make_mock_response(COT_RESPONSE_42),   # 42
            make_mock_response(COT_RESPONSE_17),   # 17
        ]

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.side_effect = responses

            result = solve_with_self_consistency("test problem", n=5)
            assert result == "42"

    def test_returns_none_when_no_answers_extracted(self):
        """solve_with_self_consistency() returns None if no answers can be extracted."""
        from solution import solve_with_self_consistency

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response(NO_ANSWER_RESPONSE)

            result = solve_with_self_consistency("impossible problem", n=3)
            assert result is None


class TestEvaluateMathAccuracy:
    def test_perfect_accuracy(self):
        """evaluate_math_accuracy() returns 1.0 when all predictions match."""
        from solution import evaluate_math_accuracy

        result = evaluate_math_accuracy(["42", "17", "5"], ["42", "17", "5"])
        assert result == 1.0

    def test_none_predictions_count_as_wrong(self):
        """evaluate_math_accuracy() treats None predictions as incorrect."""
        from solution import evaluate_math_accuracy

        result = evaluate_math_accuracy([None, "17", None], ["42", "17", "5"])
        # Only "17" matches out of 3
        assert abs(result - 1 / 3) < 1e-9

    def test_all_wrong_returns_zero(self):
        """evaluate_math_accuracy() returns 0.0 when no predictions are correct."""
        from solution import evaluate_math_accuracy

        result = evaluate_math_accuracy(["1", "2", "3"], ["4", "5", "6"])
        assert result == 0.0
