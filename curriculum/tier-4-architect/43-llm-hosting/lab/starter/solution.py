import json
import urllib.request
import urllib.error
from dataclasses import dataclass

OLLAMA_BASE_URL = "http://localhost:11434"


@dataclass
class OllamaModel:
    name: str
    size: int
    digest: str


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        # TODO: Make GET request to self.base_url + "/api/tags"
        # TODO: Return True if request succeeds (HTTP 200), False on any error
        pass

    def list_models(self) -> list[OllamaModel]:
        """List locally available models."""
        # TODO: GET /api/tags, parse response JSON
        # TODO: Return list of OllamaModel objects from response["models"]
        # TODO: Each model dict has keys: "name", "size", "digest"
        pass

    def generate(self, model: str, prompt: str, stream: bool = False) -> str:
        """Generate a response from a model.

        Args:
            model: Model name, e.g. "llama3.1:8b-instruct-q4_K_M"
            prompt: The input prompt string
            stream: If True, read response token by token (streaming mode)

        Returns:
            The complete generated response as a string
        """
        # TODO: Build payload dict: {"model": model, "prompt": prompt, "stream": stream}
        # TODO: POST /api/generate with JSON-encoded payload
        # TODO: If stream=False:
        #         parse single JSON response, return response["response"]
        # TODO: If stream=True:
        #         read response body line by line
        #         each line is JSON: {"response": "<token>", "done": false}
        #         concatenate all response["response"] values
        #         stop when response["done"] == True
        #         return the concatenated string
        pass

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry.

        Args:
            model_name: Model tag, e.g. "llama3.1:8b-instruct-q4_K_M"

        Returns:
            True on success, False on any error
        """
        # TODO: POST /api/pull with {"name": model_name, "stream": False}
        # TODO: Return True on HTTP 200, False on urllib.error.URLError or other error
        pass


def get_client_with_fallback(
    base_url: str = OLLAMA_BASE_URL,
) -> tuple[OllamaClient, bool]:
    """Return (client, is_available) for graceful degradation.

    Returns:
        Tuple of (OllamaClient instance, bool indicating if server is available)
    """
    # TODO: Create OllamaClient with base_url
    # TODO: Call client.is_available()
    # TODO: Return (client, True) if available, (client, False) otherwise
    pass


# ---------------------------------------------------------------------------
# Manual smoke test — only runs when Ollama is actually available
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    client, available = get_client_with_fallback()
    print(f"Ollama available: {available}")

    if available:
        models = client.list_models()
        print(f"Models: {[m.name for m in models]}")

        if models:
            model_name = models[0].name
            response = client.generate(model_name, "What is the capital of France?")
            print(f"Response: {response}")
    else:
        print("Ollama not running. Start it with: ollama serve")
