"""Tests for Lab 39 — Cost Estimator CLI"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


class TestCountTokens:
    def test_returns_integer(self):
        """count_tokens should return an int."""
        from solution import count_tokens

        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1, 2, 3, 4, 5]

        with patch("tiktoken.get_encoding", return_value=mock_enc):
            result = count_tokens("hello world")

        assert isinstance(result, int)

    def test_returns_correct_count(self):
        """count_tokens should return the number of tokens from the encoder."""
        from solution import count_tokens

        mock_enc = MagicMock()
        mock_enc.encode.return_value = [10, 20, 30]  # 3 tokens

        with patch("tiktoken.get_encoding", return_value=mock_enc):
            result = count_tokens("any text")

        assert result == 3

    def test_empty_string_returns_zero(self):
        """count_tokens("") should return 0."""
        from solution import count_tokens

        mock_enc = MagicMock()
        mock_enc.encode.return_value = []

        with patch("tiktoken.get_encoding", return_value=mock_enc):
            result = count_tokens("")

        assert result == 0

    def test_uses_cl100k_base_by_default(self):
        """count_tokens should use cl100k_base encoding by default."""
        from solution import count_tokens

        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1]

        with patch("tiktoken.get_encoding", return_value=mock_enc) as mock_get:
            count_tokens("hello")
            mock_get.assert_called_once_with("cl100k_base")


class TestEstimateCost:
    def test_returns_dict(self):
        """estimate_cost should return a dict."""
        from solution import estimate_cost
        result = estimate_cost(1000, 500, "claude-3-haiku-20240307")
        assert isinstance(result, dict)

    def test_required_keys(self):
        """estimate_cost result must contain all required keys."""
        from solution import estimate_cost
        result = estimate_cost(1000, 500, "claude-3-haiku-20240307")
        required_keys = {"model", "input_tokens", "output_tokens", "input_cost", "output_cost", "total_cost"}
        assert required_keys.issubset(result.keys())

    def test_model_key_matches_input(self):
        """The model key in the result must match the input model name."""
        from solution import estimate_cost
        result = estimate_cost(1000, 500, "gpt-4o-mini")
        assert result["model"] == "gpt-4o-mini"

    def test_token_counts_preserved(self):
        """Input and output token counts should be preserved in the result."""
        from solution import estimate_cost
        result = estimate_cost(1234, 567, "gpt-4o")
        assert result["input_tokens"] == 1234
        assert result["output_tokens"] == 567

    def test_cost_calculation_haiku(self):
        """Haiku: $0.25/M input, $1.25/M output. Test with 1M tokens each."""
        from solution import estimate_cost
        result = estimate_cost(1_000_000, 1_000_000, "claude-3-haiku-20240307")
        assert abs(result["input_cost"] - 0.25) < 0.0001
        assert abs(result["output_cost"] - 1.25) < 0.0001
        assert abs(result["total_cost"] - 1.50) < 0.0001

    def test_cost_calculation_gpt4o_mini(self):
        """GPT-4o-mini: $0.15/M input, $0.60/M output."""
        from solution import estimate_cost
        result = estimate_cost(1_000_000, 1_000_000, "gpt-4o-mini")
        assert abs(result["input_cost"] - 0.15) < 0.0001
        assert abs(result["output_cost"] - 0.60) < 0.0001

    def test_total_cost_equals_sum(self):
        """total_cost must equal input_cost + output_cost."""
        from solution import estimate_cost
        result = estimate_cost(500_000, 200_000, "gpt-4o")
        assert abs(result["total_cost"] - (result["input_cost"] + result["output_cost"])) < 1e-10

    def test_zero_tokens_zero_cost(self):
        """Zero tokens should produce zero cost."""
        from solution import estimate_cost
        result = estimate_cost(0, 0, "claude-3-5-sonnet-20241022")
        assert result["total_cost"] == 0.0


class TestFormatCostTable:
    def _make_estimate(self, model, in_tok, out_tok, in_cost, out_cost, total):
        return {
            "model": model,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "input_cost": in_cost,
            "output_cost": out_cost,
            "total_cost": total,
        }

    def test_returns_string(self):
        """format_cost_table should return a string."""
        from solution import format_cost_table
        estimates = [self._make_estimate("gpt-4o-mini", 100, 50, 0.00001, 0.00003, 0.00004)]
        result = format_cost_table(estimates)
        assert isinstance(result, str)

    def test_header_contains_model(self):
        """The output table must contain the word 'Model' in the header."""
        from solution import format_cost_table
        estimates = [self._make_estimate("gpt-4o-mini", 100, 50, 0.00001, 0.00003, 0.00004)]
        result = format_cost_table(estimates)
        assert "Model" in result

    def test_model_name_in_table(self):
        """The model name should appear in the table output."""
        from solution import format_cost_table
        estimates = [self._make_estimate("claude-3-haiku-20240307", 200, 100, 0.00005, 0.0001, 0.00015)]
        result = format_cost_table(estimates)
        assert "claude-3-haiku-20240307" in result

    def test_multiple_estimates(self):
        """Table should include all model names when multiple estimates are provided."""
        from solution import format_cost_table
        estimates = [
            self._make_estimate("gpt-4o-mini", 100, 50, 0.00001, 0.00003, 0.00004),
            self._make_estimate("gpt-4o", 100, 50, 0.0005, 0.00075, 0.00125),
        ]
        result = format_cost_table(estimates)
        assert "gpt-4o-mini" in result
        assert "gpt-4o" in result


class TestEstimateAllModels:
    def test_returns_list(self):
        """estimate_all_models should return a list."""
        from solution import estimate_all_models

        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1] * 50  # 50 tokens

        with patch("tiktoken.get_encoding", return_value=mock_enc):
            result = estimate_all_models("test text", 100)

        assert isinstance(result, list)

    def test_returns_one_entry_per_model(self):
        """There should be one estimate per model in MODEL_PRICING."""
        from solution import estimate_all_models, MODEL_PRICING

        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1] * 30

        with patch("tiktoken.get_encoding", return_value=mock_enc):
            result = estimate_all_models("some text", 100)

        assert len(result) == len(MODEL_PRICING)

    def test_sorted_by_total_cost_ascending(self):
        """Results should be sorted by total_cost from cheapest to most expensive."""
        from solution import estimate_all_models

        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1] * 1000  # 1000 input tokens

        with patch("tiktoken.get_encoding", return_value=mock_enc):
            result = estimate_all_models("large text", 500)

        costs = [e["total_cost"] for e in result]
        assert costs == sorted(costs), "Results should be sorted by total_cost ascending"

    def test_each_entry_has_required_keys(self):
        """Each entry in the list must have all required keys."""
        from solution import estimate_all_models

        mock_enc = MagicMock()
        mock_enc.encode.return_value = [1] * 20

        with patch("tiktoken.get_encoding", return_value=mock_enc):
            result = estimate_all_models("hello", 100)

        required_keys = {"model", "input_tokens", "output_tokens", "input_cost", "output_cost", "total_cost"}
        for entry in result:
            assert required_keys.issubset(entry.keys())
