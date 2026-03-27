"""Tests for Lab 02 — Token Counter & Cost Estimator"""

import sys
import os
import pytest

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))


class TestCountTokens:
    def test_returns_integer(self):
        from solution import count_tokens
        assert isinstance(count_tokens("hello"), int)

    def test_empty_string_returns_zero(self):
        from solution import count_tokens
        assert count_tokens("") == 0

    def test_longer_text_more_tokens(self):
        from solution import count_tokens
        assert count_tokens("hello world foo bar baz") > count_tokens("hi")

    def test_known_token_count(self):
        from solution import count_tokens
        # "Hello" is reliably 1 token in cl100k_base
        assert count_tokens("Hello") == 1


class TestEstimateCost:
    def test_returns_float(self):
        from solution import estimate_cost
        assert isinstance(estimate_cost(1000, 500), float)

    def test_positive_for_nonzero_tokens(self):
        from solution import estimate_cost
        assert estimate_cost(1000, 500) > 0

    def test_zero_tokens_zero_cost(self):
        from solution import estimate_cost
        assert estimate_cost(0, 0) == 0.0

    def test_more_tokens_more_cost(self):
        from solution import estimate_cost
        assert estimate_cost(2000, 1000) > estimate_cost(1000, 500)


class TestTruncateToTokens:
    def test_short_text_unchanged(self):
        from solution import truncate_to_tokens
        text = "Hello world"
        result = truncate_to_tokens(text, max_tokens=100)
        assert result == text

    def test_long_text_truncated(self):
        from solution import truncate_to_tokens, count_tokens
        long_text = "word " * 500  # ~500 tokens
        result = truncate_to_tokens(long_text, max_tokens=50)
        assert count_tokens(result) <= 50

    def test_result_is_string(self):
        from solution import truncate_to_tokens
        assert isinstance(truncate_to_tokens("test", 10), str)


class TestTokenize:
    def test_returns_list(self):
        from solution import tokenize
        assert isinstance(tokenize("hello"), list)

    def test_all_items_are_strings(self):
        from solution import tokenize
        result = tokenize("Hello, world!")
        assert all(isinstance(t, str) for t in result)

    def test_reconstruct_matches_original(self):
        from solution import tokenize
        text = "Hello world"
        tokens = tokenize(text)
        reconstructed = "".join(tokens)
        assert reconstructed == text

    def test_empty_string(self):
        from solution import tokenize
        assert tokenize("") == []
