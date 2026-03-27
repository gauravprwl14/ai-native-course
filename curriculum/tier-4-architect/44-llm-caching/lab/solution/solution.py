import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class CacheEntry:
    value: str
    created_at: float
    ttl_seconds: float


class ExactCache:
    def __init__(self, ttl_seconds: float = 3600):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, CacheEntry] = {}

    def _make_key(self, prompt: str, model: str, **params) -> str:
        payload = {"model": model, "prompt": prompt, **dict(sorted(params.items()))}
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def get(self, prompt: str, model: str, **params) -> Optional[str]:
        key = self._make_key(prompt, model, **params)
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() - entry.created_at >= entry.ttl_seconds:
            del self._store[key]
            return None
        return entry.value

    def set(self, prompt: str, model: str, value: str, **params) -> None:
        key = self._make_key(prompt, model, **params)
        self._store[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl_seconds=self.ttl_seconds,
        )


class CachedLLMClient:
    def __init__(self, llm_caller: Callable, cache: ExactCache):
        self.llm_caller = llm_caller
        self.cache = cache
        self.hits = 0
        self.misses = 0

    def generate(self, prompt: str, model: str = "claude-3-haiku-20240307", **params) -> str:
        cached = self.cache.get(prompt, model, **params)
        if cached is not None:
            self.hits += 1
            return cached
        self.misses += 1
        response = self.llm_caller(prompt, model, **params)
        self.cache.set(prompt, model, response, **params)
        return response

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Manual smoke test — demonstrates expected behaviour
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    call_count = 0

    def mock_llm(prompt: str, model: str, **params) -> str:
        global call_count
        call_count += 1
        return f"Response to: {prompt}"

    cache = ExactCache(ttl_seconds=60)
    client = CachedLLMClient(llm_caller=mock_llm, cache=cache)

    r1 = client.generate("Hello", "gpt-4")
    r2 = client.generate("Hello", "gpt-4")   # cache hit
    r3 = client.generate("World", "gpt-4")

    print(f"LLM calls made: {call_count}")  # 2
    print(f"Hit rate: {client.hit_rate:.2f}")  # 0.33
    print(f"r1 == r2: {r1 == r2}")  # True
