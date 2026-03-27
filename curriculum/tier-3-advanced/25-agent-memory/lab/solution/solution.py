"""Lab 25: Agent with Persistent Memory — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import json
import math
from pathlib import Path as FilePath
from utils import get_anthropic_client, get_openai_client

MODEL = "claude-3-haiku-20240307"
EMBEDDING_MODEL = "text-embedding-3-small"


class MemoryStore:
    def __init__(self, storage_path: str = None):
        self.memories: dict[str, dict] = {}  # key -> {"value": str, "embedding": list}
        self.storage_path = storage_path
        if storage_path and FilePath(storage_path).exists():
            self._load()

    def save(self, key: str, value: str) -> None:
        """Save a memory with its embedding."""
        embedding = self._embed(value)
        self.memories[key] = {"value": value, "embedding": embedding}
        self._persist()

    def get(self, key: str) -> str | None:
        """Get exact memory by key. Returns None if key is not found."""
        return self.memories.get(key, {}).get("value")

    def search(self, query: str, top_k: int = 3) -> list[tuple[str, str]]:
        """
        Semantic search over memories.
        Returns list of (key, value) tuples sorted by cosine similarity descending.
        """
        if not self.memories:
            return []
        query_vec = self._embed(query)
        scored = [
            (key, data["value"], self._cosine_sim(query_vec, data["embedding"]))
            for key, data in self.memories.items()
        ]
        scored.sort(key=lambda x: x[2], reverse=True)
        return [(k, v) for k, v, _ in scored[:top_k]]

    def summarize_old(self) -> str:
        """Ask the LLM to summarise all stored memories."""
        lines = [f"{k}: {v['value']}" for k, v in self.memories.items()]
        text = "\n".join(lines)
        client = get_anthropic_client()
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Summarise these agent memories in 3-5 concise bullet points, "
                        f"preserving key facts:\n\n{text}"
                    ),
                }
            ],
        )
        return response.content[0].text

    def _embed(self, text: str) -> list[float]:
        client = get_openai_client()
        return client.embeddings.create(model=EMBEDDING_MODEL, input=text).data[0].embedding

    def _cosine_sim(self, v1: list[float], v2: list[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        m1 = math.sqrt(sum(a ** 2 for a in v1))
        m2 = math.sqrt(sum(b ** 2 for b in v2))
        return dot / (m1 * m2) if m1 and m2 else 0.0

    def _load(self):
        with open(self.storage_path) as f:
            self.memories = json.load(f)

    def _persist(self):
        if self.storage_path:
            with open(self.storage_path, "w") as f:
                json.dump(self.memories, f)


class MemoryAgent:
    def __init__(self, memory_store: MemoryStore = None):
        self.store = memory_store or MemoryStore()
        self.client = get_anthropic_client()

    def chat(self, message: str, top_k: int = 3) -> str:
        """Retrieve relevant memories, build system prompt, call LLM, return reply."""
        memories = self.store.search(message, top_k=top_k)
        if memories:
            bullet_list = "\n".join(f"- {k}: {v}" for k, v in memories)
            system = f"You are a helpful assistant.\nRelevant memories:\n{bullet_list}"
        else:
            system = "You are a helpful assistant."

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": message}],
        )
        return response.content[0].text


if __name__ == "__main__":
    store = MemoryStore()
    store.save("user_name", "Alice")
    store.save("project", "Building a fraud detection pipeline")
    store.save("bug_yesterday", "Fixed a race condition in the async queue")
    store.save("preference", "Prefers concise answers, no Java examples")

    print("Exact get:", store.get("user_name"))
    print("\nSemantic search for 'bug':")
    for key, value in store.search("bug", top_k=2):
        print(f"  [{key}] {value}")

    agent = MemoryAgent(store)
    print("\nAgent response:")
    print(agent.chat("What bug was I fixing recently?"))
