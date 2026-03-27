"""
Tests for Lab 04 — Compare Outputs at Different Temperatures

All tests use unittest.mock so no real API calls are made.
Import target: starter/solution.py (set LAB_TARGET=solution to test reference solution)
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

# Allow switching to the reference solution via environment variable
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_response(text: str) -> MagicMock:
    """Build a minimal mock of an Anthropic messages.create() response."""
    mock_content = MagicMock()
    mock_content.text = text

    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


# ---------------------------------------------------------------------------
# Tests: generate_at_temperature
# ---------------------------------------------------------------------------

class TestGenerateAtTemperature:

    def test_returns_list(self):
        """generate_at_temperature must return a list."""
        from solution import generate_at_temperature

        mock_resp = _make_mock_response("Mars")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            result = generate_at_temperature("Name a planet.", 0.0, n=3)

        assert isinstance(result, list)

    def test_returns_n_strings(self):
        """The returned list must contain exactly n strings."""
        from solution import generate_at_temperature

        mock_resp = _make_mock_response("Venus")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            result = generate_at_temperature("Name a planet.", 0.5, n=5)

        assert len(result) == 5
        assert all(isinstance(s, str) for s in result)

    def test_default_n_is_3(self):
        """Default n should produce 3 responses."""
        from solution import generate_at_temperature

        mock_resp = _make_mock_response("Jupiter")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            result = generate_at_temperature("Name a planet.", 0.0)

        assert len(result) == 3

    def test_temperature_passed_to_api(self):
        """The temperature value must be forwarded to every API call."""
        from solution import generate_at_temperature

        mock_resp = _make_mock_response("Saturn")
        with patch("anthropic.Anthropic") as MockClient:
            mock_create = MockClient.return_value.messages.create
            mock_create.return_value = mock_resp

            generate_at_temperature("Name a planet.", temperature=0.7, n=2)

            for actual_call in mock_create.call_args_list:
                kwargs = actual_call.kwargs if actual_call.kwargs else actual_call[1]
                assert kwargs.get("temperature") == 0.7, (
                    f"Expected temperature=0.7, got {kwargs.get('temperature')}"
                )

    def test_api_called_n_times(self):
        """The API must be called exactly n times."""
        from solution import generate_at_temperature

        mock_resp = _make_mock_response("Neptune")
        with patch("anthropic.Anthropic") as MockClient:
            mock_create = MockClient.return_value.messages.create
            mock_create.return_value = mock_resp

            generate_at_temperature("Name a planet.", 0.0, n=4)

            assert mock_create.call_count == 4

    def test_response_text_extracted(self):
        """The returned strings must be the text content from the API response."""
        from solution import generate_at_temperature

        mock_resp = _make_mock_response("Earth")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            result = generate_at_temperature("Name a planet.", 0.0, n=1)

        assert result == ["Earth"]

    def test_temperature_zero_passes_correctly(self):
        """temperature=0.0 (not 0 integer) must be passed correctly."""
        from solution import generate_at_temperature

        mock_resp = _make_mock_response("Mercury")
        with patch("anthropic.Anthropic") as MockClient:
            mock_create = MockClient.return_value.messages.create
            mock_create.return_value = mock_resp

            generate_at_temperature("Name a planet.", temperature=0.0, n=1)

            kwargs = mock_create.call_args.kwargs if mock_create.call_args.kwargs else mock_create.call_args[1]
            assert kwargs.get("temperature") == 0.0


# ---------------------------------------------------------------------------
# Tests: compare_temperatures
# ---------------------------------------------------------------------------

class TestCompareTemperatures:

    def test_returns_dict(self):
        """compare_temperatures must return a dict."""
        from solution import compare_temperatures

        mock_resp = _make_mock_response("Dog")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            result = compare_temperatures("Name an animal.", [0.0, 1.0])

        assert isinstance(result, dict)

    def test_keys_match_temperatures(self):
        """Dict keys must be exactly the temperature values provided."""
        from solution import compare_temperatures

        mock_resp = _make_mock_response("Cat")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            temperatures = [0.0, 0.5, 1.0]
            result = compare_temperatures("Name an animal.", temperatures)

        assert set(result.keys()) == set(temperatures)

    def test_each_value_is_list_of_3(self):
        """Each dict value must be a list of 3 strings (default n=3)."""
        from solution import compare_temperatures

        mock_resp = _make_mock_response("Bird")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            result = compare_temperatures("Name an animal.", [0.0, 0.5])

        for temp, responses in result.items():
            assert isinstance(responses, list), f"Value for temp={temp} should be a list"
            assert len(responses) == 3, f"Expected 3 responses for temp={temp}, got {len(responses)}"

    def test_default_temperatures(self):
        """Default temperatures should be [0.0, 0.5, 1.0] producing 3 keys."""
        from solution import compare_temperatures

        mock_resp = _make_mock_response("Fish")
        with patch("anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create.return_value = mock_resp
            result = compare_temperatures("Name an animal.")

        assert len(result) == 3


# ---------------------------------------------------------------------------
# Tests: is_valid_json_output
# ---------------------------------------------------------------------------

class TestIsValidJsonOutput:

    def test_valid_object(self):
        from solution import is_valid_json_output
        assert is_valid_json_output('{"name": "Alice", "age": 30}') is True

    def test_valid_array(self):
        from solution import is_valid_json_output
        assert is_valid_json_output('[1, 2, 3]') is True

    def test_valid_string(self):
        from solution import is_valid_json_output
        assert is_valid_json_output('"hello"') is True

    def test_invalid_plain_text(self):
        from solution import is_valid_json_output
        assert is_valid_json_output("not json at all") is False

    def test_invalid_empty_string(self):
        from solution import is_valid_json_output
        assert is_valid_json_output("") is False

    def test_invalid_broken_json(self):
        from solution import is_valid_json_output
        assert is_valid_json_output('{"key": }') is False

    def test_returns_bool(self):
        from solution import is_valid_json_output
        result = is_valid_json_output('{"a": 1}')
        assert isinstance(result, bool)
