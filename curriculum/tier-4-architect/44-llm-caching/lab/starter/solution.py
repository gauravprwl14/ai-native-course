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
        # TODO: Create a dict with keys: "model", "prompt", plus all **params sorted by key
        # TODO: Serialize to JSON with sort_keys=True
        # TODO: Return the SHA256 hex digest of the serialized string
        pass

    def get(self, prompt: str, model: str, **params) -> Optional[str]:
        # TODO: Compute the cache key using _make_key()
        # TODO: Look up the key in self._store
        # TODO: If not found, return None
        # TODO: If found, check if entry is still valid:
        #         time.time() - entry.created_at < self.ttl_seconds
        # TODO: If valid, return entry.value
        # TODO: If expired, delete from self._store and return None
        pass

    def set(self, prompt: str, model: str, value: str, **params) -> None:
        # TODO: Compute the cache key using _make_key()
        # TODO: Create a CacheEntry with value, created_at=time.time(), ttl_seconds=self.ttl_seconds
        # TODO: Store the entry in self._store[key]
        pass


class CachedLLMClient:
    def __init__(self, llm_caller: Callable, cache: ExactCache):
        self.llm_caller = llm_caller
        self.cache = cache
        self.hits = 0
        self.misses = 0

    def generate(self, prompt: str, model: str = "claude-3-haiku-20240307", **params) -> str:
        # TODO: Call self.cache.get(prompt, model, **params)
        # TODO: If cache hit (result is not None):
        #         increment self.hits
        #         return the cached value
        # TODO: If cache miss:
        #         increment self.misses
        #         call self.llm_caller(prompt, model, **params) to get the response
        #         store response in cache: self.cache.set(prompt, model, response, **params)
        #         return the response
        pass

    @property
    def hit_rate(self) -> float:
        # TODO: Return self.hits / (self.hits + self.misses)
        # TODO: Return 0.0 if no requests have been made (avoid ZeroDivisionError)
        pass


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
    r2 = client.generate("Hello", "gpt-4")   # should be a cache hit
    r3 = client.generate("World", "gpt-4")

    print(f"LLM calls made: {call_count}")  # Expected: 2
    print(f"Hit rate: {client.hit_rate:.2f}")  # Expected: 0.33
    print(f"r1 == r2: {r1 == r2}")  # Expected: True
