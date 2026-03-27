import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

from solution import OllamaClient, OllamaModel, get_client_with_fallback, OLLAMA_BASE_URL


def _make_response(body: bytes, status: int = 200) -> MagicMock:
    """Create a mock urllib response context manager."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.status = status
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _make_streaming_response(lines: list[dict]) -> MagicMock:
    """Create a mock response that iterates over NDJSON lines."""
    encoded = [json.dumps(line).encode() + b"\n" for line in lines]
    mock_resp = MagicMock()
    mock_resp.__iter__ = lambda s: iter(encoded)
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestIsAvailable(unittest.TestCase):
    def test_returns_true_when_server_responds(self):
        with patch("urllib.request.urlopen", return_value=_make_response(b"{}")):
            client = OllamaClient()
            self.assertTrue(client.is_available())

    def test_returns_false_when_connection_refused(self):
        import urllib.error
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            client = OllamaClient()
            self.assertFalse(client.is_available())


class TestListModels(unittest.TestCase):
    def test_returns_model_objects(self):
        body = json.dumps(
            {
                "models": [
                    {"name": "llama3.1:8b", "size": 4_000_000_000, "digest": "sha256:abc"},
                    {"name": "mistral:7b", "size": 3_500_000_000, "digest": "sha256:def"},
                ]
            }
        ).encode()
        with patch("urllib.request.urlopen", return_value=_make_response(body)):
            client = OllamaClient()
            models = client.list_models()

        self.assertEqual(len(models), 2)
        self.assertIsInstance(models[0], OllamaModel)
        self.assertEqual(models[0].name, "llama3.1:8b")
        self.assertEqual(models[0].size, 4_000_000_000)
        self.assertEqual(models[0].digest, "sha256:abc")

    def test_returns_empty_list_on_empty_models(self):
        body = json.dumps({"models": []}).encode()
        with patch("urllib.request.urlopen", return_value=_make_response(body)):
            client = OllamaClient()
            models = client.list_models()
        self.assertEqual(models, [])


class TestGenerate(unittest.TestCase):
    def test_non_streaming_returns_response_field(self):
        body = json.dumps({"response": "Paris", "done": True}).encode()
        with patch("urllib.request.urlopen", return_value=_make_response(body)):
            client = OllamaClient()
            result = client.generate("llama3.1:8b", "Capital of France?", stream=False)
        self.assertEqual(result, "Paris")

    def test_streaming_concatenates_tokens(self):
        lines = [
            {"response": "The ", "done": False},
            {"response": "answer ", "done": False},
            {"response": "is 42", "done": True},
        ]
        with patch(
            "urllib.request.urlopen",
            return_value=_make_streaming_response(lines),
        ):
            client = OllamaClient()
            result = client.generate("llama3.1:8b", "What is 6x7?", stream=True)
        self.assertEqual(result, "The answer is 42")

    def test_generate_sends_correct_payload(self):
        body = json.dumps({"response": "ok", "done": True}).encode()
        with patch("urllib.request.urlopen", return_value=_make_response(body)) as mock_open:
            client = OllamaClient()
            client.generate("llama3.1:8b", "Hello", stream=False)
            call_args = mock_open.call_args
            # First arg is the Request object
            request_obj = call_args[0][0]
            sent_data = json.loads(request_obj.data.decode())
            self.assertEqual(sent_data["model"], "llama3.1:8b")
            self.assertEqual(sent_data["prompt"], "Hello")
            self.assertEqual(sent_data["stream"], False)


class TestPullModel(unittest.TestCase):
    def test_returns_true_on_success(self):
        body = json.dumps({"status": "success"}).encode()
        with patch("urllib.request.urlopen", return_value=_make_response(body)):
            client = OllamaClient()
            result = client.pull_model("llama3.1:8b-instruct-q4_K_M")
        self.assertTrue(result)

    def test_returns_false_on_connection_error(self):
        import urllib.error
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            client = OllamaClient()
            result = client.pull_model("llama3.1:8b")
        self.assertFalse(result)


class TestGetClientWithFallback(unittest.TestCase):
    def test_returns_available_true_when_server_up(self):
        with patch("urllib.request.urlopen", return_value=_make_response(b"{}")):
            client, available = get_client_with_fallback()
        self.assertIsInstance(client, OllamaClient)
        self.assertTrue(available)

    def test_returns_available_false_when_server_down(self):
        import urllib.error
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            client, available = get_client_with_fallback()
        self.assertIsInstance(client, OllamaClient)
        self.assertFalse(available)

    def test_custom_base_url_is_used(self):
        with patch("urllib.request.urlopen", return_value=_make_response(b"{}")):
            client, _ = get_client_with_fallback("http://myserver:11434")
        self.assertEqual(client.base_url, "http://myserver:11434")


if __name__ == "__main__":
    unittest.main()
