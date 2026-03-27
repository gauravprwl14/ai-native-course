# Lab 46 — Build a Mini AI Gateway

## Goal

Build a simplified AI gateway in pure Python that handles routing, rate limiting, caching, cost calculation, and audit logging. No real API calls are made — all providers are simulated with mock functions.

## Tasks

### Task 1: RateLimiter.is_allowed

Implement a sliding window rate limiter that checks whether an API key is within its requests-per-minute quota.

- Track a list of request timestamps per key
- Evict timestamps older than 60 seconds
- Reject (return False) if the key already has `rpm` or more requests in the window
- Accept (return True) and record the timestamp otherwise

### Task 2: AIGateway.register_provider

Register a callable handler under a provider name. The handler signature is:
```
handler(model: str, prompt: str, max_tokens: int) -> tuple[str, int, int]
# Returns: (response_text, input_tokens, output_tokens)
```

### Task 3: AIGateway._get_provider

Given a model name, determine the provider using `MODEL_PROVIDER_MAP`. Check if the model name starts with any of the map's keys and return the corresponding provider. Default to `"openai"` if no match is found.

### Task 4: AIGateway._calculate_cost

Calculate the USD cost for a request given provider name, input token count, and output token count. Use `MODEL_PRICING` for rates (per 1M tokens). Fall back to OpenAI pricing if the provider is not in the pricing table.

### Task 5: AIGateway.route

The main gateway entry point. In order:
1. Check rate limit — raise `ValueError("Rate limit exceeded")` if denied
2. Compute cache key from `md5(model:prompt)`
3. If cache hit, return cached response with `cached=True` and write a log entry
4. Determine provider
5. Call the registered provider handler
6. Calculate cost
7. Build and cache `GatewayResponse`
8. Write a `RequestLog` entry to `self.logs`
9. Return the response

### Task 6: AIGateway.get_cost_by_key

Return a dict mapping each API key to its total cost (sum of `cost_usd` from all log entries for that key).

## Running Tests

```bash
cd curriculum/tier-4-architect/46-ai-gateway/lab
pytest tests/ -v
```

## Files

- `starter/solution.py` — fill in the TODOs
- `solution/solution.py` — reference implementation
- `tests/test_solution.py` — test suite (no real API calls)
