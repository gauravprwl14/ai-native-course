"""
Tests for Lab 09 — Zero/Few-shot Prompting
These tests verify function signatures and logic WITHOUT making real API calls.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Import from starter (or solution for CI) — set LAB_TARGET=solution to test reference impl
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def make_mock_response(text: str):
    """Create a minimal mock Anthropic API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


SAMPLE_EXAMPLES = [
    {"text": "Best purchase I've made this year!", "label": "positive"},
    {"text": "Arrived damaged and two weeks late.", "label": "negative"},
    {"text": "It's fine, does what it says.", "label": "neutral"},
    {"text": "Absolutely love it, exceeded expectations.", "label": "positive"},
    {"text": "Terrible customer service, won't buy again.", "label": "negative"},
]


# ---------------------------------------------------------------------------
# classify_zero_shot
# ---------------------------------------------------------------------------

class TestClassifyZeroShot:
    def test_returns_valid_sentiment(self):
        """classify_zero_shot must return one of the three valid labels."""
        from solution import classify_zero_shot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("positive")

            result = classify_zero_shot("Great product!")
            assert result in {"positive", "negative", "neutral"}

    def test_returns_stripped_lowercase(self):
        """classify_zero_shot must return a stripped lowercase string."""
        from solution import classify_zero_shot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            # Simulate API returning text with whitespace / mixed case
            mock_client.messages.create.return_value = make_mock_response("  Negative  ")

            result = classify_zero_shot("Broken on arrival.")
            assert result == "negative"

    def test_uses_temperature_zero(self):
        """classify_zero_shot must call the API with temperature=0."""
        from solution import classify_zero_shot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("neutral")

            classify_zero_shot("It's okay.")
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs.get('temperature') == 0


# ---------------------------------------------------------------------------
# build_few_shot_prompt
# ---------------------------------------------------------------------------

class TestBuildFewShotPrompt:
    def test_contains_example_text(self):
        """build_few_shot_prompt must include example texts in the output."""
        from solution import build_few_shot_prompt

        prompt = build_few_shot_prompt(SAMPLE_EXAMPLES, "Test input.")
        assert "Best purchase I've made this year!" in prompt
        assert "Arrived damaged and two weeks late." in prompt

    def test_contains_input_text(self):
        """build_few_shot_prompt must include the input text in the output."""
        from solution import build_few_shot_prompt

        input_text = "This is the text to classify."
        prompt = build_few_shot_prompt(SAMPLE_EXAMPLES, input_text)
        assert input_text in prompt

    def test_contains_example_labels(self):
        """build_few_shot_prompt must include example labels in the output."""
        from solution import build_few_shot_prompt

        prompt = build_few_shot_prompt(SAMPLE_EXAMPLES, "Any input.")
        assert "positive" in prompt
        assert "negative" in prompt
        assert "neutral" in prompt

    def test_returns_string(self):
        """build_few_shot_prompt must return a string."""
        from solution import build_few_shot_prompt

        result = build_few_shot_prompt(SAMPLE_EXAMPLES, "Hello.")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# classify_few_shot
# ---------------------------------------------------------------------------

class TestClassifyFewShot:
    def test_returns_valid_sentiment(self):
        """classify_few_shot must return one of the three valid labels."""
        from solution import classify_few_shot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("negative")

            result = classify_few_shot("Terrible experience.", SAMPLE_EXAMPLES)
            assert result in {"positive", "negative", "neutral"}

    def test_returns_stripped_lowercase(self):
        """classify_few_shot must return a stripped lowercase string."""
        from solution import classify_few_shot

        with patch('solution.get_anthropic_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.messages.create.return_value = make_mock_response("  Positive\n")

            result = classify_few_shot("Loved it!", SAMPLE_EXAMPLES)
            assert result == "positive"


# ---------------------------------------------------------------------------
# evaluate_accuracy
# ---------------------------------------------------------------------------

class TestEvaluateAccuracy:
    def test_perfect_predictions_returns_one(self):
        """evaluate_accuracy returns 1.0 when all predictions match."""
        from solution import evaluate_accuracy

        predictions = ["positive", "negative", "neutral"]
        labels = ["positive", "negative", "neutral"]
        assert evaluate_accuracy(predictions, labels) == 1.0

    def test_all_wrong_returns_zero(self):
        """evaluate_accuracy returns 0.0 when no predictions match."""
        from solution import evaluate_accuracy

        predictions = ["positive", "positive", "positive"]
        labels = ["negative", "negative", "negative"]
        assert evaluate_accuracy(predictions, labels) == 0.0

    def test_half_correct_returns_half(self):
        """evaluate_accuracy returns 0.5 when half of predictions are correct."""
        from solution import evaluate_accuracy

        predictions = ["positive", "negative", "positive", "negative"]
        labels = ["positive", "positive", "negative", "negative"]
        assert evaluate_accuracy(predictions, labels) == 0.5
