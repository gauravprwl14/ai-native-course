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
        try:
            urllib.request.urlopen(self.base_url + "/api/tags", timeout=3)
            return True
        except (urllib.error.URLError, OSError):
            return False

    def list_models(self) -> list[OllamaModel]:
        """List locally available models."""
        try:
            with urllib.request.urlopen(self.base_url + "/api/tags", timeout=5) as resp:
                data = json.loads(resp.read())
            return [
                OllamaModel(
                    name=m["name"],
                    size=m.get("size", 0),
                    digest=m.get("digest", ""),
                )
                for m in data.get("models", [])
            ]
        except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError):
            return []

    def generate(self, model: str, prompt: str, stream: bool = False) -> str:
        """Generate a response from a model."""
        payload = json.dumps(
            {"model": model, "prompt": prompt, "stream": stream}
        ).encode()

        req = urllib.request.Request(
            self.base_url + "/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            if not stream:
                data = json.loads(resp.read())
                return data["response"]
            else:
                tokens = []
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    chunk = json.loads(line)
                    tokens.append(chunk.get("response", ""))
                    if chunk.get("done", False):
                        break
                return "".join(tokens)

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            payload = json.dumps({"name": model_name, "stream": False}).encode()
            req = urllib.request.Request(
                self.base_url + "/api/pull",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=600):
                pass
            return True
        except (urllib.error.URLError, OSError):
            return False


def get_client_with_fallback(
    base_url: str = OLLAMA_BASE_URL,
) -> tuple[OllamaClient, bool]:
    """Return (client, is_available) for graceful degradation."""
    client = OllamaClient(base_url=base_url)
    available = client.is_available()
    return client, available


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
