"""
Lab 46 — AI Gateway
--------------------
Build a simplified AI gateway with routing, rate limiting, caching,
cost tracking, and audit logging.

Fill in every TODO to complete this lab.

Run: python solution.py
Test: cd .. && pytest tests/ -v
"""

import time
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Optional
from collections import defaultdict


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class GatewayRequest:
    key: str          # API key / team identifier
    model: str
    prompt: str
    max_tokens: int = 1000


@dataclass
class GatewayResponse:
    model: str
    response: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    provider: str
    cached: bool = False


@dataclass
class RequestLog:
    timestamp: float
    key: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    cached: bool


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL_PROVIDER_MAP = {
    "claude": "anthropic",
    "gpt":    "openai",
    "llama":  "local",
}

MODEL_PRICING = {
    # per 1 million tokens
    "anthropic": {"input": 3.0,  "output": 15.0},
    "openai":    {"input": 5.0,  "output": 15.0},
    "local":     {"input": 0.0,  "output": 0.0},
}


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if key is within rate limit. Returns True if allowed."""
        # TODO: Get current time
        # TODO: Filter self._windows[key] to only timestamps within last 60 seconds
        # TODO: If len(filtered) >= self.rpm, return False
        # TODO: Append current time to self._windows[key], return True
        pass


# ---------------------------------------------------------------------------
# AI Gateway
# ---------------------------------------------------------------------------

class AIGateway:
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.logs: list[RequestLog] = []
        self._providers: dict[str, Callable] = {}
        self._cache: dict[str, GatewayResponse] = {}

    def register_provider(self, name: str, handler: Callable) -> None:
        """Register a provider handler.
        handler(model, prompt, max_tokens) -> (response_text, input_tokens, output_tokens)
        """
        # TODO: Store handler in self._providers[name]
        pass

    def _get_provider(self, model: str) -> str:
        """Determine provider from model name prefix."""
        # TODO: Iterate MODEL_PROVIDER_MAP items
        # TODO: If model.startswith(prefix), return the mapped provider name
        # TODO: Default to "openai" if no prefix matches
        pass

    def _calculate_cost(
        self, provider: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost in USD."""
        # TODO: Look up pricing for provider in MODEL_PRICING
        #       (fall back to MODEL_PRICING["openai"] if provider not found)
        # TODO: Return (input_tokens * input_price + output_tokens * output_price) / 1_000_000
        pass

    def route(self, request: GatewayRequest) -> GatewayResponse:
        """Route request through gateway with rate limiting, caching, and logging."""
        # TODO: Check rate limit via self.rate_limiter.is_allowed(request.key)
        #       Raise ValueError("Rate limit exceeded") if denied

        # TODO: Compute cache key:
        #       cache_key = hashlib.md5(f"{request.model}:{request.prompt}".encode()).hexdigest()

        # TODO: If cache_key in self._cache:
        #       - Get cached response
        #       - Write a RequestLog with cached=True
        #       - Return the cached response (set cached=True on it)

        # TODO: Determine provider via self._get_provider(request.model)

        # TODO: Call self._providers[provider](request.model, request.prompt, request.max_tokens)
        #       which returns (response_text, input_tokens, output_tokens)

        # TODO: Calculate cost via self._calculate_cost(provider, input_tokens, output_tokens)

        # TODO: Build GatewayResponse

        # TODO: Store response in self._cache[cache_key]

        # TODO: Append RequestLog to self.logs

        # TODO: Return response
        pass

    def get_cost_by_key(self) -> dict[str, float]:
        """Return total cost per API key."""
        # TODO: Sum cost_usd from self.logs, grouped by log.key
        # TODO: Return dict[key, total_cost]
        pass


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    def mock_provider(model: str, prompt: str, max_tokens: int):
        """Simulate a provider returning a response with token counts."""
        return ("This is a mock response.", 100, 50)

    gw = AIGateway(rate_limiter=RateLimiter(requests_per_minute=5))
    gw.register_provider("anthropic", mock_provider)
    gw.register_provider("openai", mock_provider)
    gw.register_provider("local", mock_provider)

    # First call
    r1 = gw.route(GatewayRequest(key="team-a", model="claude-sonnet", prompt="Hello world"))
    print(f"Response 1: provider={r1.provider}, cached={r1.cached}, cost=${r1.cost_usd:.6f}")

    # Second identical call — should be cached
    r2 = gw.route(GatewayRequest(key="team-b", model="claude-sonnet", prompt="Hello world"))
    print(f"Response 2: provider={r2.provider}, cached={r2.cached}, cost=${r2.cost_usd:.6f}")

    # Different model
    r3 = gw.route(GatewayRequest(key="team-a", model="gpt-4o", prompt="What is 2+2?"))
    print(f"Response 3: provider={r3.provider}, cached={r3.cached}, cost=${r3.cost_usd:.6f}")

    # Cost report
    costs = gw.get_cost_by_key()
    print(f"\nCost by key: {costs}")
    print(f"Total logs: {len(gw.logs)}")
