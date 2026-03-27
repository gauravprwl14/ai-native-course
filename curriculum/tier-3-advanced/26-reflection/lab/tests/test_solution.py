"""Tests for Lab 26: Self-improving Summarizer"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock, patch, call


def _make_llm_response(text: str) -> MagicMock:
    """Build a mock Anthropic response object returning the given text."""
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    return response


# ---------------------------------------------------------------------------
# generate_summary
# ---------------------------------------------------------------------------

class TestGenerateSummary(unittest.TestCase):
    """Tests for generate_summary()"""

    @patch("solution.get_anthropic_client")
    def test_returns_string(self, mock_get_client):
        """generate_summary() returns a non-empty string."""
        from solution import generate_summary

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response("This is a summary.")

        result = generate_summary("Some long text about ML.")

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("solution.get_anthropic_client")
    def test_calls_llm_with_text_in_prompt(self, mock_get_client):
        """generate_summary() includes the input text in the LLM prompt."""
        from solution import generate_summary

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response("Summary here.")

        generate_summary("unique_content_marker_abc123")

        call_args = mock_client.messages.create.call_args
        messages = call_args[1].get("messages") or call_args[0][1] if call_args[0] else call_args[1]["messages"]
        content = str(messages)
        self.assertIn("unique_content_marker_abc123", content)


# ---------------------------------------------------------------------------
# critique_summary
# ---------------------------------------------------------------------------

class TestCritiqueSummary(unittest.TestCase):
    """Tests for critique_summary()"""

    @patch("solution.get_anthropic_client")
    def test_returns_string(self, mock_get_client):
        """critique_summary() returns a non-empty string."""
        from solution import critique_summary

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response(
            "The summary is missing the section on reinforcement learning."
        )

        result = critique_summary("Original text.", "Short summary.")

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("solution.get_anthropic_client")
    def test_includes_original_and_summary_in_prompt(self, mock_get_client):
        """critique_summary() passes both original text and summary to the LLM."""
        from solution import critique_summary

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response("NO MAJOR ISSUES")

        critique_summary("original_marker_xyz", "summary_marker_xyz")

        call_args = mock_client.messages.create.call_args
        content = str(call_args)
        self.assertIn("original_marker_xyz", content)
        self.assertIn("summary_marker_xyz", content)

    @patch("solution.get_anthropic_client")
    def test_no_major_issues_signal_returned(self, mock_get_client):
        """critique_summary() can return a string containing 'NO MAJOR ISSUES'."""
        from solution import critique_summary

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response(
            "The summary looks good. NO MAJOR ISSUES"
        )

        result = critique_summary("some text", "a summary")

        self.assertIn("NO MAJOR ISSUES", result.upper())


# ---------------------------------------------------------------------------
# improve_summary
# ---------------------------------------------------------------------------

class TestImproveSummary(unittest.TestCase):
    """Tests for improve_summary()"""

    @patch("solution.critique_summary")
    @patch("solution.generate_summary")
    def test_returns_string(self, mock_generate, mock_critique):
        """improve_summary() returns a non-empty string."""
        from solution import improve_summary

        mock_generate.return_value = "Initial summary."
        mock_critique.return_value = "NO MAJOR ISSUES"

        result = improve_summary("some text", max_iterations=3)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("solution.critique_summary")
    @patch("solution.generate_summary")
    def test_stops_early_when_no_major_issues(self, mock_generate, mock_critique):
        """improve_summary() stops iterating when critique returns 'NO MAJOR ISSUES'."""
        from solution import improve_summary

        mock_generate.return_value = "Great summary."
        mock_critique.return_value = "This summary is excellent. NO MAJOR ISSUES"

        improve_summary("text", max_iterations=3)

        # critique should be called once, then loop exits
        self.assertEqual(mock_critique.call_count, 1)

    @patch("solution.get_anthropic_client")
    @patch("solution.critique_summary")
    @patch("solution.generate_summary")
    def test_does_not_exceed_max_iterations(self, mock_generate, mock_critique, mock_get_client):
        """improve_summary() never exceeds max_iterations revision calls."""
        from solution import improve_summary

        mock_generate.return_value = "Draft."
        # critique always finds issues — never satisfied
        mock_critique.return_value = "Missing key details."

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response("Revised draft.")

        improve_summary("text", max_iterations=2)

        # critique called at most max_iterations times
        self.assertLessEqual(mock_critique.call_count, 2)

    @patch("solution.get_anthropic_client")
    @patch("solution.critique_summary")
    @patch("solution.generate_summary")
    def test_calls_generate_once(self, mock_generate, mock_critique, mock_get_client):
        """improve_summary() calls generate_summary exactly once."""
        from solution import improve_summary

        mock_generate.return_value = "Initial draft."
        mock_critique.return_value = "NO MAJOR ISSUES"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        improve_summary("text", max_iterations=3)

        mock_generate.assert_called_once()

    @patch("solution.get_anthropic_client")
    @patch("solution.critique_summary")
    @patch("solution.generate_summary")
    def test_revises_when_issues_found(self, mock_generate, mock_critique, mock_get_client):
        """improve_summary() calls the LLM to revise when critique finds issues."""
        from solution import improve_summary

        mock_generate.return_value = "Draft v1."
        # First critique finds issues; second says no major issues
        mock_critique.side_effect = ["Missing details.", "NO MAJOR ISSUES"]

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response("Draft v2.")

        result = improve_summary("text", max_iterations=3)

        # LLM should have been called for the revision
        mock_client.messages.create.assert_called()
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
