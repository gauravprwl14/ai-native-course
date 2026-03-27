"""
Tests for Lab 01 — Your First LLM API Call
These tests verify the function signatures and logic WITHOUT making real API calls.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add starter (or solution for CI) to path so we test the learner's code
# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def make_mock_response(text: str, input_tokens: int = 50, output_tokens: int = 100):
    """Create a mock Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    mock.usage.input_tokens = input_tokens
    mock.usage.output_tokens = output_tokens
    return mock


class TestCallClaude:
    def test_returns_string(self):
        """call_claude() must return a string."""
        from solution import call_claude

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("Hello!")

            result = call_claude("Say hello")
            assert isinstance(result, str)
            assert result == "Hello!"

    def test_uses_correct_model(self):
        """call_claude() must use claude-haiku-4-5-20251001."""
        from solution import call_claude

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            call_claude("test")
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs.get('model') == 'claude-haiku-4-5-20251001'

    def test_passes_temperature(self):
        """call_claude() must pass the temperature parameter."""
        from solution import call_claude

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            call_claude("test", temperature=0.3)
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs.get('temperature') == 0.3


class TestCompareTemperatures:
    def test_returns_three_keys(self):
        """compare_temperatures() must return dict with keys '0.0', '0.7', '1.0'."""
        from solution import compare_temperatures

        with patch('solution.call_claude', return_value="response") as mock_call:
            result = compare_temperatures("test prompt")
            assert set(result.keys()) == {"0.0", "0.7", "1.0"}

    def test_calls_claude_three_times(self):
        """compare_temperatures() must call Claude 3 times."""
        from solution import compare_temperatures

        with patch('solution.call_claude', return_value="response") as mock_call:
            compare_temperatures("test")
            assert mock_call.call_count == 3

    def test_each_value_is_string(self):
        """compare_temperatures() values must all be strings."""
        from solution import compare_temperatures

        with patch('solution.call_claude', side_effect=["resp1", "resp2", "resp3"]):
            result = compare_temperatures("test")
            for val in result.values():
                assert isinstance(val, str)


class TestEstimateCallCost:
    def test_returns_float(self):
        """estimate_call_cost() must return a float."""
        from solution import estimate_call_cost

        result = estimate_call_cost(1000, 500)
        assert isinstance(result, float)

    def test_positive_cost(self):
        """estimate_call_cost() must return positive value for non-zero tokens."""
        from solution import estimate_call_cost

        result = estimate_call_cost(1000, 500)
        assert result > 0

    def test_zero_tokens_zero_cost(self):
        """estimate_call_cost() with zero tokens returns zero."""
        from solution import estimate_call_cost

        result = estimate_call_cost(0, 0)
        assert result == 0.0
