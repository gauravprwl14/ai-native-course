"""Lab 25: Agent with Persistent Memory"""
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
        """
        Save a memory with its embedding.

        # TODO:
        # 1. Embed the value using self._embed(value)
        # 2. Store in self.memories[key] = {"value": value, "embedding": embedding}
        # 3. If self.storage_path is set, call self._persist()
        """
        raise NotImplementedError("Implement save")

    def get(self, key: str) -> str | None:
        """
        Get exact memory by key. Returns None if key is not found.

        # TODO:
        # return self.memories.get(key, {}).get("value")
        """
        raise NotImplementedError("Implement get")

    def search(self, query: str, top_k: int = 3) -> list[tuple[str, str]]:
        """
        Semantic search over memories.
        Returns list of (key, value) tuples sorted by cosine similarity descending.

        # TODO:
        # 1. If self.memories is empty, return []
        # 2. Embed the query using self._embed(query)
        # 3. Compute cosine similarity between query embedding and each memory embedding
        # 4. Sort by similarity descending
        # 5. Return the top_k (key, value) pairs as a list of tuples
        """
        raise NotImplementedError("Implement search")

    def summarize_old(self) -> str:
        """
        Ask the LLM to summarise all stored memories.
        Returns the summary string.

        # TODO:
        # 1. Build a text block from all memories:
        #    lines = [f"{k}: {v['value']}" for k, v in self.memories.items()]
        #    text = "\n".join(lines)
        # 2. Call get_anthropic_client() and create a message asking for a bullet-point summary
        # 3. Return the response text
        """
        raise NotImplementedError("Implement summarize_old")

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
        """
        An agent that retrieves relevant memories before each LLM call.

        # TODO:
        # Set self.store = memory_store or MemoryStore()
        # Set self.client = get_anthropic_client()
        """
        raise NotImplementedError("Implement __init__")

    def chat(self, message: str, top_k: int = 3) -> str:
        """
        Retrieve relevant memories, build a system prompt, call the LLM, return the reply.

        # TODO:
        # 1. Search for relevant memories: memories = self.store.search(message, top_k=top_k)
        # 2. Build system prompt — if memories exist, list them as bullet points:
        #    system = "You are a helpful assistant.\nRelevant memories:\n" + bullet_list
        #    Otherwise: system = "You are a helpful assistant."
        # 3. Call self.client.messages.create(model=MODEL, max_tokens=1024,
        #      system=system, messages=[{"role": "user", "content": message}])
        # 4. Return response.content[0].text
        """
        raise NotImplementedError("Implement chat")


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
