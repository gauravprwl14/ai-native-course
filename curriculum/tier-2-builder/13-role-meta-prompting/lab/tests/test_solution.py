"""Tests for Lab 13 — Role + Meta Prompting"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))


def _make_mock_response(text: str):
    """Build a mock Anthropic API response with the given text."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


class TestApplyRolePrompt:
    def test_returns_string(self):
        """apply_role_prompt returns a string."""
        from solution import apply_role_prompt

        mock_response = _make_mock_response("Here are the top 3 things to check...")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = apply_role_prompt(
                task="What should I check in code review?",
                role_description="a senior Python engineer"
            )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_passes_role_in_system_prompt(self):
        """apply_role_prompt includes the role description in the system prompt."""
        from solution import apply_role_prompt

        mock_response = _make_mock_response("I am reviewing your code...")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            apply_role_prompt(
                task="Review this code",
                role_description="a security engineer specialising in Python"
            )

        call_kwargs = mock_client.messages.create.call_args
        # system should contain the role description
        system_arg = call_kwargs.kwargs.get("system", "")
        assert "a security engineer specialising in Python" in system_arg


class TestGeneratePromptVariants:
    def test_returns_a_list(self):
        """generate_prompt_variants returns a list."""
        from solution import generate_prompt_variants

        raw = "You are a Python tutor.\n---\nYou are a senior engineer.\n---\nYou are a teacher."
        mock_response = _make_mock_response(raw)

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = generate_prompt_variants("Explain Python lists", n=3)

        assert isinstance(result, list)

    def test_returns_n_variants(self):
        """generate_prompt_variants returns exactly n variants."""
        from solution import generate_prompt_variants

        raw = "You are a Python tutor.\n---\nYou are a senior engineer.\n---\nYou are a teacher."
        mock_response = _make_mock_response(raw)

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = generate_prompt_variants("Explain Python lists", n=3)

        assert len(result) == 3

    def test_uses_high_temperature(self):
        """generate_prompt_variants calls the API with temperature >= 0.7."""
        from solution import generate_prompt_variants

        raw = "Variant A.\n---\nVariant B."
        mock_response = _make_mock_response(raw)

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            generate_prompt_variants("Some task", n=2)

        call_kwargs = mock_client.messages.create.call_args
        temperature = call_kwargs.kwargs.get("temperature")
        assert temperature is not None, "temperature should be set explicitly"
        assert temperature >= 0.7, f"Expected temperature >= 0.7, got {temperature}"


class TestEvaluatePrompt:
    def test_returns_float_between_0_and_1(self):
        """evaluate_prompt returns a float between 0.0 and 1.0."""
        from solution import evaluate_prompt

        mock_response = _make_mock_response("This is about iteration and loops")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            test_cases = [{"input": "What is a loop?", "expected_keywords": ["iteration"]}]
            result = evaluate_prompt("You are a tutor.", test_cases)

        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0

    def test_returns_1_when_all_keywords_present(self):
        """evaluate_prompt returns 1.0 when all expected_keywords appear in every response."""
        from solution import evaluate_prompt

        mock_response = _make_mock_response("iteration repeat loop goes round and round")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            test_cases = [
                {"input": "What is a for loop?", "expected_keywords": ["iteration", "repeat"]}
            ]
            result = evaluate_prompt("You are a Python tutor.", test_cases)

        assert result == 1.0

    def test_returns_0_when_no_keywords_match(self):
        """evaluate_prompt returns 0.0 when no expected_keywords appear in any response."""
        from solution import evaluate_prompt

        mock_response = _make_mock_response("The sky is blue and the grass is green.")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            test_cases = [
                {"input": "What is a variable?", "expected_keywords": ["store", "value", "memory"]}
            ]
            result = evaluate_prompt("You are a Python tutor.", test_cases)

        assert result == 0.0

    def test_handles_multiple_test_cases(self):
        """evaluate_prompt scores across multiple test cases correctly."""
        from solution import evaluate_prompt

        # First call: keywords present; second call: keywords absent
        pass_response = _make_mock_response("iteration loop repeat over and over")
        fail_response = _make_mock_response("something completely unrelated here")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [pass_response, fail_response]
            mock_client_fn.return_value = mock_client

            test_cases = [
                {"input": "What is a loop?", "expected_keywords": ["iteration", "repeat"]},
                {"input": "What is a dict?", "expected_keywords": ["key", "value"]},
            ]
            result = evaluate_prompt("You are a tutor.", test_cases)

        # 1 out of 2 cases pass
        assert result == pytest.approx(0.5)
