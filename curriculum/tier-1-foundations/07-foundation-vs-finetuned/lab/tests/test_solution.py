"""Tests for Lab 07: Compare Model Outputs on Same Task"""
import pytest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))


# ---------------------------------------------------------------------------
# classify_sentiment
# ---------------------------------------------------------------------------

def _make_mock_response(text: str) -> MagicMock:
    """Helper: build a mock Anthropic messages.create response."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=text)]
    return mock_response


def test_classify_sentiment_returns_positive():
    from solution import classify_sentiment
    mock_response = _make_mock_response("positive")

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = classify_sentiment("I love this product!")

    assert result == "positive"


def test_classify_sentiment_returns_negative():
    from solution import classify_sentiment
    mock_response = _make_mock_response("negative")

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = classify_sentiment("This was a terrible experience.")

    assert result == "negative"


def test_classify_sentiment_returns_neutral():
    from solution import classify_sentiment
    mock_response = _make_mock_response("neutral")

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = classify_sentiment("The package arrived on Tuesday.")

    assert result == "neutral"


def test_classify_sentiment_uses_temperature_zero():
    """classify_sentiment must pass temperature=0 to the API."""
    from solution import classify_sentiment
    mock_response = _make_mock_response("positive")

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        classify_sentiment("Great stuff!")

        _, kwargs = mock_client.messages.create.call_args
        assert kwargs.get("temperature") == 0, (
            "classify_sentiment must call messages.create with temperature=0"
        )


# ---------------------------------------------------------------------------
# compare_model_outputs
# ---------------------------------------------------------------------------

def test_compare_model_outputs_returns_dict_with_model_keys():
    from solution import compare_model_outputs, MODELS
    mock_response = _make_mock_response("positive")

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        results = compare_model_outputs(["I love this!"])

    assert isinstance(results, dict)
    for key in MODELS:
        assert key in results, f"Expected model key '{key}' in results"


def test_compare_model_outputs_list_length_matches_texts():
    from solution import compare_model_outputs
    texts = ["text one", "text two", "text three"]
    mock_response = _make_mock_response("neutral")

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        results = compare_model_outputs(texts)

    for model_key, labels in results.items():
        assert len(labels) == len(texts), (
            f"Model '{model_key}' returned {len(labels)} results for {len(texts)} texts"
        )


# ---------------------------------------------------------------------------
# calculate_agreement_rate
# ---------------------------------------------------------------------------

def test_calculate_agreement_rate_all_agree():
    from solution import calculate_agreement_rate
    results = {
        "haiku": ["positive", "negative", "neutral"],
        "sonnet": ["positive", "negative", "neutral"],
    }
    assert calculate_agreement_rate(results) == 1.0


def test_calculate_agreement_rate_no_agreement():
    from solution import calculate_agreement_rate
    results = {
        "haiku": ["positive", "negative"],
        "sonnet": ["negative", "positive"],
    }
    assert calculate_agreement_rate(results) == 0.0


def test_calculate_agreement_rate_partial_agreement():
    from solution import calculate_agreement_rate
    # 2 out of 4 texts agree
    results = {
        "haiku": ["positive", "positive", "negative", "neutral"],
        "sonnet": ["positive", "negative", "negative", "positive"],
    }
    rate = calculate_agreement_rate(results)
    assert rate == pytest.approx(0.5), f"Expected 0.5, got {rate}"
