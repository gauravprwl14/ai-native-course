"""
Tests for Lab 11 — System Prompts: Customer Service Bot

All tests use unittest.mock so no real API calls are made.
Import target: starter/solution.py (set LAB_TARGET=solution to test reference solution)
"""

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

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
# Tests: create_customer_service_bot
# ---------------------------------------------------------------------------

class TestCreateCustomerServiceBot:

    def test_returns_dict_with_system_prompt_key(self):
        """create_customer_service_bot must return a dict with a 'system_prompt' key."""
        from solution import create_customer_service_bot

        result = create_customer_service_bot("Acme", "cloud storage")

        assert isinstance(result, dict), "Result must be a dict"
        assert "system_prompt" in result, "Result must have 'system_prompt' key"

    def test_system_prompt_contains_company_name(self):
        """The system prompt must mention the company name."""
        from solution import create_customer_service_bot

        result = create_customer_service_bot("GlobalTech", "project management software")

        assert "GlobalTech" in result["system_prompt"], (
            "system_prompt must contain the company_name 'GlobalTech'"
        )

    def test_system_prompt_contains_product_type(self):
        """The system prompt must mention the product type."""
        from solution import create_customer_service_bot

        result = create_customer_service_bot("Acme", "inventory management")

        assert "inventory management" in result["system_prompt"], (
            "system_prompt must contain the product_type 'inventory management'"
        )

    def test_returns_company_and_product_keys(self):
        """The returned dict must include 'company' and 'product' keys."""
        from solution import create_customer_service_bot

        result = create_customer_service_bot("BetaCorp", "HR software")

        assert result.get("company") == "BetaCorp", "Result must have 'company' key with company_name value"
        assert result.get("product") == "HR software", "Result must have 'product' key with product_type value"


# ---------------------------------------------------------------------------
# Tests: chat
# ---------------------------------------------------------------------------

class TestChat:

    def test_returns_tuple_of_str_and_list(self):
        """chat must return a (str, list) tuple."""
        from solution import chat

        bot_config = {
            "system_prompt": "You are a helpful assistant.",
            "company": "Acme",
            "product": "cloud storage",
        }
        mock_resp = _make_mock_response("Here is your answer.")

        with patch("solution.get_anthropic_client") as mock_get_client:
            mock_get_client.return_value.messages.create.return_value = mock_resp
            result = chat(bot_config, "Hello", [])

        assert isinstance(result, tuple), "chat must return a tuple"
        assert len(result) == 2, "Tuple must have exactly 2 elements"
        response_text, updated_history = result
        assert isinstance(response_text, str), "First element must be a str"
        assert isinstance(updated_history, list), "Second element must be a list"

    def test_sends_system_prompt_from_bot_config(self):
        """chat must pass bot_config['system_prompt'] as the system parameter to the API."""
        from solution import chat

        custom_system = "You are a very specific assistant for TestCo widgets."
        bot_config = {
            "system_prompt": custom_system,
            "company": "TestCo",
            "product": "widgets",
        }
        mock_resp = _make_mock_response("Got it.")

        with patch("solution.get_anthropic_client") as mock_get_client:
            mock_create = mock_get_client.return_value.messages.create
            mock_create.return_value = mock_resp
            chat(bot_config, "Tell me about widgets", [])

            call_kwargs = mock_create.call_args.kwargs if mock_create.call_args.kwargs else mock_create.call_args[1]
            assert call_kwargs.get("system") == custom_system, (
                f"Expected system='{custom_system}', got system='{call_kwargs.get('system')}'"
            )

    def test_appends_two_messages_to_history(self):
        """Each chat call must append exactly 2 messages to history: user + assistant."""
        from solution import chat

        bot_config = {
            "system_prompt": "You are a helpful assistant.",
            "company": "Acme",
            "product": "cloud storage",
        }
        initial_history = []
        mock_resp = _make_mock_response("I can help with that.")

        with patch("solution.get_anthropic_client") as mock_get_client:
            mock_get_client.return_value.messages.create.return_value = mock_resp
            _, updated_history = chat(bot_config, "How do I sign up?", initial_history)

        assert len(updated_history) == 2, (
            f"Expected history length 2 after one chat call, got {len(updated_history)}"
        )
        assert updated_history[0]["role"] == "user"
        assert updated_history[1]["role"] == "assistant"


# ---------------------------------------------------------------------------
# Tests: is_on_topic
# ---------------------------------------------------------------------------

class TestIsOnTopic:

    def test_returns_true_when_response_is_yes(self):
        """is_on_topic must return True when the LLM responds with 'yes'."""
        from solution import is_on_topic

        mock_resp = _make_mock_response("yes")

        with patch("solution.get_anthropic_client") as mock_get_client:
            mock_get_client.return_value.messages.create.return_value = mock_resp
            result = is_on_topic("How do I upgrade my plan?", ["billing", "account management"])

        assert result is True, "Expected True when LLM responds 'yes'"

    def test_returns_false_when_response_is_no(self):
        """is_on_topic must return False when the LLM responds with 'no'."""
        from solution import is_on_topic

        mock_resp = _make_mock_response("no")

        with patch("solution.get_anthropic_client") as mock_get_client:
            mock_get_client.return_value.messages.create.return_value = mock_resp
            result = is_on_topic("What is the weather today?", ["billing", "account management"])

        assert result is False, "Expected False when LLM responds 'no'"
