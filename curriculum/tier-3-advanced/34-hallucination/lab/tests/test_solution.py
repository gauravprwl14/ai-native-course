"""Tests for Lab 34 — Hallucination Detection"""

import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def _make_mock_client(response_text: str):
    """Create a mock Anthropic client returning response_text."""
    mock_content = MagicMock()
    mock_content.text = response_text
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


class TestCheckFaithfulness(unittest.TestCase):
    def _run(self, response_text: str, answer: str = "test", context: str = "ctx"):
        from solution import check_faithfulness
        mock_client = _make_mock_client(response_text)
        with patch("solution.get_anthropic_client", return_value=mock_client):
            return check_faithfulness(answer, context)

    def test_returns_float(self):
        result = self._run('{"score": 0.9, "reason": "fully supported"}')
        self.assertIsInstance(result, float)

    def test_high_score_for_supported_answer(self):
        result = self._run('{"score": 0.95, "reason": "all claims supported"}')
        self.assertGreaterEqual(result, 0.8)

    def test_low_score_for_contradicting_answer(self):
        result = self._run('{"score": 0.1, "reason": "contradicts context"}')
        self.assertLessEqual(result, 0.3)

    def test_score_in_valid_range(self):
        result = self._run('{"score": 0.75, "reason": "mostly supported"}')
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_fallback_on_invalid_json(self):
        result = self._run("I cannot determine the score.")
        self.assertIsInstance(result, float)
        self.assertEqual(result, 0.5)

    def test_calls_api_once(self):
        from solution import check_faithfulness
        mock_client = _make_mock_client('{"score": 0.8, "reason": "ok"}')
        with patch("solution.get_anthropic_client", return_value=mock_client):
            check_faithfulness("answer", "context")
        mock_client.messages.create.assert_called_once()


class TestDetectContradictions(unittest.TestCase):
    def _run(self, response_text: str, answer: str = "test", context: str = "ctx"):
        from solution import detect_contradictions
        mock_client = _make_mock_client(response_text)
        with patch("solution.get_anthropic_client", return_value=mock_client):
            return detect_contradictions(answer, context)

    def test_returns_list(self):
        result = self._run('["Sentence one is wrong.", "Sentence two is unsupported."]')
        self.assertIsInstance(result, list)

    def test_returns_contradicting_sentences(self):
        result = self._run('["Refunds accepted within 60 days."]')
        self.assertEqual(len(result), 1)
        self.assertIn("60 days", result[0])

    def test_returns_empty_list_when_no_contradictions(self):
        result = self._run("[]")
        self.assertEqual(result, [])

    def test_fallback_empty_list_on_invalid_response(self):
        result = self._run("No contradictions found.")
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])


class TestVerifyRagAnswer(unittest.TestCase):
    def _run(self, faithfulness_score: float, contradictions: list,
             question: str = "Q?", answer: str = "A.", chunks=None):
        from solution import verify_rag_answer
        if chunks is None:
            chunks = ["Chunk one.", "Chunk two."]
        score_response = json.dumps({"score": faithfulness_score, "reason": "test"})
        contradiction_response = json.dumps(contradictions)

        responses = [score_response, contradiction_response]
        call_count = [0]

        def side_effect(**kwargs):
            mock_content = MagicMock()
            mock_content.text = responses[call_count[0] % len(responses)]
            call_count[0] += 1
            mock_response = MagicMock()
            mock_response.content = [mock_content]
            return mock_response

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = side_effect

        with patch("solution.get_anthropic_client", return_value=mock_client):
            return verify_rag_answer(question, answer, chunks)

    def test_returns_dict_with_required_keys(self):
        result = self._run(0.9, [])
        self.assertIn("faithful", result)
        self.assertIn("score", result)
        self.assertIn("issues", result)

    def test_faithful_true_when_score_above_threshold(self):
        result = self._run(0.9, [])
        self.assertTrue(result["faithful"])

    def test_faithful_false_when_score_below_threshold(self):
        result = self._run(0.5, ["Claim X is wrong."])
        self.assertFalse(result["faithful"])


if __name__ == "__main__":
    unittest.main()
