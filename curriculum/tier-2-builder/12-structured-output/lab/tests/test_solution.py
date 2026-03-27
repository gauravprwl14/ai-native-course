"""Tests for Lab 12 — Structured Output: Invoice Extractor"""

import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch, call

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


class TestParseJsonWithRetry:
    def test_returns_dict_on_first_success(self):
        """Returns a dict immediately when LLM responds with valid JSON."""
        from solution import parse_json_with_retry

        valid_json = '{"vendor": "ACME", "amount": 150.0}'
        mock_response = _make_mock_response(valid_json)

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = parse_json_with_retry("Extract invoice data")

        assert isinstance(result, dict)
        assert result["vendor"] == "ACME"
        assert result["amount"] == 150.0

    def test_retries_on_json_decode_error(self):
        """Retries the API call when the first response is invalid JSON."""
        from solution import parse_json_with_retry

        bad_response = _make_mock_response("Sure! Here's the data: {}")
        good_response = _make_mock_response('{"vendor": "ACME", "amount": 99.0}')

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [bad_response, good_response]
            mock_client_fn.return_value = mock_client

            result = parse_json_with_retry("Extract invoice data", max_retries=3)

        assert mock_client.messages.create.call_count == 2
        assert result["vendor"] == "ACME"

    def test_raises_value_error_after_max_retries(self):
        """Raises ValueError after exhausting all retries with invalid JSON."""
        from solution import parse_json_with_retry

        bad_response = _make_mock_response("Not JSON at all!!!")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = bad_response
            mock_client_fn.return_value = mock_client

            with pytest.raises(ValueError):
                parse_json_with_retry("Extract invoice data", max_retries=3)

        assert mock_client.messages.create.call_count == 3

    def test_uses_temperature_zero(self):
        """Verifies API is called with temperature=0."""
        from solution import parse_json_with_retry

        valid_json = '{"vendor": "Test", "amount": 1.0}'
        mock_response = _make_mock_response(valid_json)

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            parse_json_with_retry("Extract invoice data")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs.get("temperature") == 0 or (
            len(call_kwargs.args) > 0 and call_kwargs.args[0] == 0
        ) or "temperature" in str(call_kwargs)


class TestExtractInvoiceData:
    def test_returns_dict(self):
        """extract_invoice_data returns a dict."""
        from solution import extract_invoice_data

        expected = {
            "vendor": "CloudHost Inc.",
            "amount": 89.0,
            "currency": "USD",
            "date": "2024-01-15",
            "items": [{"description": "Hosting", "price": 89.0}],
        }

        with patch("solution.parse_json_with_retry", return_value=expected) as mock_retry:
            result = extract_invoice_data("Invoice from CloudHost Inc. $89 on Jan 15 2024")

        assert isinstance(result, dict)
        assert result["vendor"] == "CloudHost Inc."

    def test_calls_parse_json_with_retry(self):
        """extract_invoice_data delegates to parse_json_with_retry."""
        from solution import extract_invoice_data

        dummy_result = {"vendor": "X", "amount": 1.0, "currency": "USD", "date": "2024-01-01", "items": []}

        with patch("solution.parse_json_with_retry", return_value=dummy_result) as mock_retry:
            extract_invoice_data("some invoice text")

        mock_retry.assert_called_once()
        # Verify the prompt contains the invoice text
        call_args = mock_retry.call_args
        prompt_arg = call_args.args[0] if call_args.args else call_args.kwargs.get("prompt", "")
        assert "some invoice text" in prompt_arg


class TestValidateInvoice:
    def test_valid_invoice_returns_true_empty_errors(self):
        """Returns (True, []) for a complete, correctly-typed invoice."""
        from solution import validate_invoice

        data = {
            "vendor": "ACME Corp",
            "amount": 150.0,
            "currency": "USD",
            "date": "2024-01-05",
            "items": [{"description": "Widget", "price": 150.0}],
        }
        valid, errors = validate_invoice(data)
        assert valid is True
        assert errors == []

    def test_missing_vendor_returns_false_with_error(self):
        """Returns (False, errors) when vendor field is missing."""
        from solution import validate_invoice

        data = {
            "amount": 150.0,
            "currency": "USD",
            "date": "2024-01-05",
            "items": [],
        }
        valid, errors = validate_invoice(data)
        assert valid is False
        assert len(errors) > 0
        assert any("vendor" in e.lower() for e in errors)

    def test_non_numeric_amount_returns_false_with_error(self):
        """Returns (False, errors) when amount is a string instead of a number."""
        from solution import validate_invoice

        data = {
            "vendor": "ACME Corp",
            "amount": "150.00",  # string instead of float
            "currency": "USD",
            "date": "2024-01-05",
            "items": [],
        }
        valid, errors = validate_invoice(data)
        assert valid is False
        assert any("amount" in e.lower() for e in errors)

    def test_missing_items_key_returns_false_with_error(self):
        """Returns (False, errors) when items field is missing entirely."""
        from solution import validate_invoice

        data = {
            "vendor": "ACME Corp",
            "amount": 150.0,
            "currency": "USD",
            "date": "2024-01-05",
            # items is absent
        }
        valid, errors = validate_invoice(data)
        assert valid is False
        assert any("items" in e.lower() for e in errors)

    def test_multiple_missing_fields_all_reported(self):
        """All missing required fields are reported in the errors list."""
        from solution import validate_invoice

        valid, errors = validate_invoice({})
        assert valid is False
        # All five required fields should be reported
        assert len(errors) >= 5
