"""Tests for Lab 22: Streaming (SSE)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock, patch
from types import GeneratorType


def make_mock_stream(chunks: list[str] = None):
    """
    Build a mock that mimics the Anthropic streaming context manager.

    Usage:
        mock_stream_cm = make_mock_stream(["Hello", " world"])
        with patch("solution.get_anthropic_client") as mock_factory:
            mock_client = MagicMock()
            mock_factory.return_value = mock_client
            mock_client.messages.stream.return_value = mock_stream_cm
    """
    if chunks is None:
        chunks = ["Hello", " world"]

    mock_stream = MagicMock()
    mock_stream.text_stream = chunks

    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_stream)
    mock_cm.__exit__ = MagicMock(return_value=False)

    return mock_cm


def patch_stream(chunks: list[str] = None):
    """Context manager helper: patch get_anthropic_client with a mock stream."""
    mock_cm = make_mock_stream(chunks)
    mock_client = MagicMock()
    mock_client.messages.stream.return_value = mock_cm
    return patch("solution.get_anthropic_client", return_value=mock_client)


class TestStreamResponse(unittest.TestCase):

    def test_stream_response_is_generator(self):
        """stream_response() returns a generator, not a list or string."""
        from solution import stream_response
        with patch_stream(["Hello", " world"]):
            result = stream_response("test prompt")
        self.assertIsInstance(result, GeneratorType)

    def test_stream_response_yields_strings(self):
        """stream_response() yields string chunks."""
        from solution import stream_response
        with patch_stream(["Hello", " world"]):
            chunks = list(stream_response("test prompt"))
        self.assertEqual(len(chunks), 2)
        for chunk in chunks:
            self.assertIsInstance(chunk, str)

    def test_stream_response_yields_correct_chunks(self):
        """stream_response() yields exactly the chunks from the stream."""
        from solution import stream_response
        with patch_stream(["The", " sky", " is", " blue"]):
            chunks = list(stream_response("What color is the sky?"))
        self.assertEqual(chunks, ["The", " sky", " is", " blue"])

    def test_stream_response_with_system_prompt(self):
        """stream_response() passes system prompt to the API when provided."""
        from solution import stream_response
        mock_cm = make_mock_stream(["OK"])
        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_cm

        with patch("solution.get_anthropic_client", return_value=mock_client):
            list(stream_response("prompt", system_prompt="You are helpful."))

        call_kwargs = mock_client.messages.stream.call_args[1]
        self.assertEqual(call_kwargs.get("system"), "You are helpful.")


class TestStreamAndCollect(unittest.TestCase):

    def test_stream_and_collect_returns_dict(self):
        """stream_and_collect() returns a dict."""
        from solution import stream_and_collect
        with patch_stream(["Hello", " world"]):
            result = stream_and_collect("test")
        self.assertIsInstance(result, dict)

    def test_stream_and_collect_has_correct_keys(self):
        """stream_and_collect() dict has 'full_text' and 'chunk_count' keys."""
        from solution import stream_and_collect
        with patch_stream(["Hello", " world"]):
            result = stream_and_collect("test")
        self.assertIn("full_text", result)
        self.assertIn("chunk_count", result)

    def test_stream_and_collect_full_text(self):
        """stream_and_collect() full_text is the concatenation of all chunks."""
        from solution import stream_and_collect
        with patch_stream(["Hello", " world"]):
            result = stream_and_collect("test")
        self.assertEqual(result["full_text"], "Hello world")

    def test_stream_and_collect_chunk_count(self):
        """stream_and_collect() chunk_count matches the number of yielded chunks."""
        from solution import stream_and_collect
        with patch_stream(["one", " two", " three"]):
            result = stream_and_collect("test")
        self.assertEqual(result["chunk_count"], 3)


class TestMeasureTtft(unittest.TestCase):

    def test_measure_ttft_returns_positive_float(self):
        """measure_ttft() returns a positive float (milliseconds)."""
        from solution import measure_ttft
        with patch_stream(["Hello", " world"]):
            ttft = measure_ttft("test prompt")
        self.assertIsInstance(ttft, float)
        self.assertGreaterEqual(ttft, 0.0)

    def test_measure_ttft_returns_negative_one_for_empty_stream(self):
        """measure_ttft() returns -1.0 when the stream yields nothing."""
        from solution import measure_ttft
        with patch_stream([]):
            ttft = measure_ttft("test prompt")
        self.assertEqual(ttft, -1.0)


if __name__ == "__main__":
    unittest.main()
