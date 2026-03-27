"""
Tests for shared utilities.
These tests do NOT make real API calls.
"""

import os
import pytest
from unittest.mock import patch


def test_count_tokens_simple():
    """count_tokens returns a positive integer for any non-empty string."""
    from shared.utils import count_tokens

    result = count_tokens("Hello, world!")
    assert isinstance(result, int)
    assert result > 0


def test_count_tokens_empty():
    """count_tokens returns 0 for an empty string."""
    from shared.utils import count_tokens

    result = count_tokens("")
    assert result == 0


def test_count_tokens_longer_text_has_more_tokens():
    """Longer text should produce more tokens than shorter text."""
    from shared.utils import count_tokens

    short = count_tokens("Hi")
    long = count_tokens("Hi " * 100)
    assert long > short


def test_estimate_cost_known_model():
    """estimate_cost_usd returns a float for a known model."""
    from shared.utils import estimate_cost_usd

    cost = estimate_cost_usd(input_tokens=1000, output_tokens=500, model="claude-haiku-4-5-20251001")
    assert isinstance(cost, float)
    assert cost > 0


def test_estimate_cost_scales_with_tokens():
    """Double the tokens → double the cost."""
    from shared.utils import estimate_cost_usd

    cost_1k = estimate_cost_usd(1000, 500, "claude-haiku-4-5-20251001")
    cost_2k = estimate_cost_usd(2000, 1000, "claude-haiku-4-5-20251001")
    assert abs(cost_2k - 2 * cost_1k) < 0.000001


def test_estimate_cost_unknown_model_raises():
    """estimate_cost_usd raises ValueError for unknown model."""
    from shared.utils import estimate_cost_usd

    with pytest.raises(ValueError, match="Unknown model"):
        estimate_cost_usd(1000, 500, model="not-a-real-model")


def test_get_anthropic_client_raises_without_key():
    """get_anthropic_client raises EnvironmentError when key is missing."""
    from shared.utils import get_anthropic_client

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
            get_anthropic_client()


def test_get_openai_client_raises_without_key():
    """get_openai_client raises EnvironmentError when key is missing."""
    from shared.utils import get_openai_client

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY"):
            get_openai_client()
