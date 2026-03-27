# Chapter 44 Lab — Two-Level LLM Cache

## Goal

Build an in-memory caching layer for LLM responses using exact matching. The cache uses a SHA256 key derived from the full request (model + prompt + params), supports TTL-based expiry, and tracks hit/miss statistics.

## Tasks

1. **`ExactCache._make_key(prompt, model, **params)`** — Create a deterministic SHA256 key from the request. Serialize `{"model": model, "prompt": prompt, ...sorted_params}` to JSON with `sort_keys=True`, then return the SHA256 hex digest.

2. **`ExactCache.get(prompt, model, **params)`** — Look up the key in `self._store`. If found, check if the entry has not expired (`time.time() - entry.created_at < self.ttl_seconds`). Return `entry.value` if valid, `None` if expired or missing.

3. **`ExactCache.set(prompt, model, value, **params)`** — Create a `CacheEntry` with `value`, `created_at=time.time()`, and `ttl_seconds=self.ttl_seconds`. Store in `self._store[key]`.

4. **`CachedLLMClient.generate(prompt, model, **params)`** — Check the cache first. On a hit, increment `self.hits` and return the cached value. On a miss, increment `self.misses`, call `self.llm_caller(prompt, model, **params)`, store the result in the cache, and return it.

5. **`CachedLLMClient.hit_rate`** (property) — Return `self.hits / (self.hits + self.misses)`. Return `0.0` if no requests have been made yet.

## Constraints

- Use only Python standard library (`hashlib`, `json`, `time`).
- The `llm_caller` is a callable injected at construction — do not hardcode any specific LLM client.
- Tests use mock callables — no API keys required.

## Expected Behaviour

```python
calls = []

def mock_llm(prompt, model, **params):
    calls.append(prompt)
    return f"Answer: {prompt}"

cache = ExactCache(ttl_seconds=60)
client = CachedLLMClient(llm_caller=mock_llm, cache=cache)

r1 = client.generate("Hello", "gpt-4")     # miss
r2 = client.generate("Hello", "gpt-4")     # hit
r3 = client.generate("Goodbye", "gpt-4")   # miss

assert len(calls) == 2        # only 2 real LLM calls
assert r1 == r2               # same cached response
assert client.hit_rate == 1/3
```

## Files

| File | Purpose |
|------|---------|
| `starter/solution.py` | Skeleton with `# TODO:` comments |
| `solution/solution.py` | Reference implementation |
| `tests/test_solution.py` | Pytest tests (mocked, no real LLM) |
