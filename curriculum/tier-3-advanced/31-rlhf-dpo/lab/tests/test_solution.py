"""Tests for Lab 31 — DPO Dataset Construction"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def make_mock_response(text: str):
    """Create a mock Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


# ---------------------------------------------------------------------------
# create_preference_pair
# ---------------------------------------------------------------------------

class TestCreatePreferencePair:
    def test_returns_dict(self):
        from solution import create_preference_pair
        result = create_preference_pair("prompt", "good answer", "bad answer")
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        from solution import create_preference_pair
        result = create_preference_pair("prompt", "good answer", "bad answer")
        assert "prompt" in result
        assert "chosen" in result
        assert "rejected" in result

    def test_values_match_inputs(self):
        from solution import create_preference_pair
        result = create_preference_pair("What is ML?", "Machine learning is...", "Dunno")
        assert result["prompt"] == "What is ML?"
        assert result["chosen"] == "Machine learning is..."
        assert result["rejected"] == "Dunno"


# ---------------------------------------------------------------------------
# validate_preference_pair
# ---------------------------------------------------------------------------

class TestValidatePreferencePair:
    def test_valid_pair_returns_true_empty_errors(self):
        from solution import validate_preference_pair
        pair = {"prompt": "Q", "chosen": "Good answer", "rejected": "Bad answer"}
        valid, errors = validate_preference_pair(pair)
        assert valid is True
        assert errors == []

    def test_missing_key_returns_false(self):
        from solution import validate_preference_pair
        pair = {"prompt": "Q", "chosen": "Good answer"}  # missing rejected
        valid, errors = validate_preference_pair(pair)
        assert valid is False
        assert len(errors) > 0

    def test_empty_chosen_is_invalid(self):
        from solution import validate_preference_pair
        pair = {"prompt": "Q", "chosen": "", "rejected": "Bad answer"}
        valid, errors = validate_preference_pair(pair)
        assert valid is False
        assert any("chosen" in e for e in errors)

    def test_identical_chosen_rejected_is_invalid(self):
        from solution import validate_preference_pair
        pair = {"prompt": "Q", "chosen": "Same", "rejected": "Same"}
        valid, errors = validate_preference_pair(pair)
        assert valid is False
        assert any("differ" in e or "chosen" in e for e in errors)

    def test_returns_tuple_of_bool_and_list(self):
        from solution import validate_preference_pair
        pair = {"prompt": "Q", "chosen": "A", "rejected": "B"}
        result = validate_preference_pair(pair)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)


# ---------------------------------------------------------------------------
# generate_rejection
# ---------------------------------------------------------------------------

class TestGenerateRejection:
    def test_returns_string(self):
        from solution import generate_rejection
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("vague response")
            result = generate_rejection("What is Python?", "Python is a high-level language...")
            assert isinstance(result, str)

    def test_calls_api_with_correct_temperature(self):
        from solution import generate_rejection
        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("worse response")
            generate_rejection("prompt", "good response")
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs.get("temperature") == 0.7


# ---------------------------------------------------------------------------
# build_dpo_dataset
# ---------------------------------------------------------------------------

class TestBuildDpoDataset:
    def test_returns_list(self):
        from solution import build_dpo_dataset
        with patch('solution.get_anthropic_client') as mock_client_fn, \
             patch('solution.generate_rejection', return_value="bad answer"):
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("good answer")
            result = build_dpo_dataset(["What is ML?"])
            assert isinstance(result, list)

    def test_one_pair_per_valid_prompt(self):
        from solution import build_dpo_dataset
        with patch('solution.get_anthropic_client') as mock_client_fn, \
             patch('solution.generate_rejection', return_value="bad answer"):
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("good answer")
            result = build_dpo_dataset(["What is ML?", "What is DL?"])
            assert len(result) == 2

    def test_each_pair_has_required_keys(self):
        from solution import build_dpo_dataset
        with patch('solution.get_anthropic_client') as mock_client_fn, \
             patch('solution.generate_rejection', return_value="bad answer"):
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("good answer")
            result = build_dpo_dataset(["What is ML?"])
            assert len(result) == 1
            pair = result[0]
            assert "prompt" in pair
            assert "chosen" in pair
            assert "rejected" in pair
