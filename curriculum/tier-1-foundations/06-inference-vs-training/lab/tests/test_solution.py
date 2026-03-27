"""
Tests for Lab 06 — Inference via API
These tests verify the function signatures and logic WITHOUT making real API calls.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, call

# Add starter (or solution for CI) to path so we test the learner's code
# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def make_mock_response(text: str):
    """Create a mock Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


class TestRunInference:
    def test_returns_string(self):
        """run_inference() must return a string."""
        from solution import run_inference

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("Hello!")

            result = run_inference("Say hello")
            assert isinstance(result, str)
            assert result == "Hello!"

    def test_passes_system_prompt_when_provided(self):
        """run_inference() must include system= when system_prompt is given."""
        from solution import run_inference

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            run_inference("test prompt", system_prompt="You are a helpful assistant.")
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert "system" in call_kwargs
            assert call_kwargs["system"] == "You are a helpful assistant."

    def test_works_without_system_prompt(self):
        """run_inference() must work correctly when system_prompt is not provided."""
        from solution import run_inference

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("response text")

            result = run_inference("no system prompt here")
            assert isinstance(result, str)
            assert result == "response text"

    def test_no_system_key_when_system_prompt_is_none(self):
        """run_inference() must NOT include system= when system_prompt is None."""
        from solution import run_inference

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("ok")

            run_inference("test", system_prompt=None)
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert "system" not in call_kwargs


class TestBatchInference:
    def test_returns_list_same_length_as_input(self):
        """batch_inference() must return a list with the same length as the input."""
        from solution import batch_inference

        with patch('solution.run_inference', side_effect=["r1", "r2", "r3"]) as mock_run:
            result = batch_inference(["p1", "p2", "p3"])
            assert isinstance(result, list)
            assert len(result) == 3

    def test_returns_responses_in_order(self):
        """batch_inference() must return responses in the same order as prompts."""
        from solution import batch_inference

        responses = ["first response", "second response", "third response"]
        with patch('solution.run_inference', side_effect=responses):
            result = batch_inference(["p1", "p2", "p3"])
            assert result == responses

    def test_calls_run_inference_for_each_prompt(self):
        """batch_inference() must call run_inference once per prompt."""
        from solution import batch_inference

        with patch('solution.run_inference', return_value="response") as mock_run:
            batch_inference(["a", "b", "c"])
            assert mock_run.call_count == 3

    def test_empty_input_returns_empty_list(self):
        """batch_inference() with empty list must return empty list."""
        from solution import batch_inference

        with patch('solution.run_inference', return_value="response"):
            result = batch_inference([])
            assert result == []


class TestMeasureInferenceLatency:
    def test_returns_dict_with_correct_keys(self):
        """measure_inference_latency() must return dict with avg_latency_ms, min_ms, max_ms, n."""
        from solution import measure_inference_latency

        with patch('solution.run_inference', return_value="ok"):
            result = measure_inference_latency("test prompt", n=3)
            assert isinstance(result, dict)
            assert "avg_latency_ms" in result
            assert "min_ms" in result
            assert "max_ms" in result
            assert "n" in result

    def test_avg_latency_ms_is_float(self):
        """measure_inference_latency() avg_latency_ms must be a float."""
        from solution import measure_inference_latency

        with patch('solution.run_inference', return_value="ok"):
            result = measure_inference_latency("test prompt", n=3)
            assert isinstance(result["avg_latency_ms"], float)

    def test_n_matches_parameter(self):
        """measure_inference_latency() n in result must match the n parameter."""
        from solution import measure_inference_latency

        with patch('solution.run_inference', return_value="ok"):
            result = measure_inference_latency("test", n=5)
            assert result["n"] == 5

    def test_calls_run_inference_n_times(self):
        """measure_inference_latency() must call run_inference exactly n times."""
        from solution import measure_inference_latency

        with patch('solution.run_inference', return_value="ok") as mock_run:
            measure_inference_latency("test", n=4)
            assert mock_run.call_count == 4
