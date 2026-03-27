"""
Lab 46 — AI Gateway (Reference Solution)
------------------------------------------
Fully working implementation of the AI gateway lab.
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
        now = time.time()
        window_start = now - 60.0

        # Evict timestamps outside the sliding window
        self._windows[key] = [
            t for t in self._windows[key] if t > window_start
        ]

        if len(self._windows[key]) >= self.rpm:
            return False

        self._windows[key].append(now)
        return True


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
        self._providers[name] = handler

    def _get_provider(self, model: str) -> str:
        """Determine provider from model name prefix."""
        for prefix, provider in MODEL_PROVIDER_MAP.items():
            if model.startswith(prefix):
                return provider
        return "openai"

    def _calculate_cost(
        self, provider: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost in USD."""
        pricing = MODEL_PRICING.get(provider, MODEL_PRICING["openai"])
        return (
            input_tokens * pricing["input"] + output_tokens * pricing["output"]
        ) / 1_000_000

    def route(self, request: GatewayRequest) -> GatewayResponse:
        """Route request through gateway with rate limiting, caching, and logging."""
        # 1. Rate limit check
        if not self.rate_limiter.is_allowed(request.key):
            raise ValueError("Rate limit exceeded")

        # 2. Cache lookup
        cache_key = hashlib.md5(
            f"{request.model}:{request.prompt}".encode()
        ).hexdigest()

        if cache_key in self._cache:
            cached_resp = self._cache[cache_key]
            # Return a copy with cached=True
            resp = GatewayResponse(
                model=cached_resp.model,
                response=cached_resp.response,
                input_tokens=cached_resp.input_tokens,
                output_tokens=cached_resp.output_tokens,
                cost_usd=cached_resp.cost_usd,
                provider=cached_resp.provider,
                cached=True,
            )
            self.logs.append(RequestLog(
                timestamp=time.time(),
                key=request.key,
                model=request.model,
                provider=resp.provider,
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
                cost_usd=resp.cost_usd,
                cached=True,
            ))
            return resp

        # 3. Determine provider and call handler
        provider = self._get_provider(request.model)
        handler = self._providers[provider]
        response_text, input_tokens, output_tokens = handler(
            request.model, request.prompt, request.max_tokens
        )

        # 4. Calculate cost
        cost_usd = self._calculate_cost(provider, input_tokens, output_tokens)

        # 5. Build response
        resp = GatewayResponse(
            model=request.model,
            response=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            provider=provider,
            cached=False,
        )

        # 6. Store in cache
        self._cache[cache_key] = resp

        # 7. Log
        self.logs.append(RequestLog(
            timestamp=time.time(),
            key=request.key,
            model=request.model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            cached=False,
        ))

        return resp

    def get_cost_by_key(self) -> dict[str, float]:
        """Return total cost per API key."""
        totals: dict[str, float] = defaultdict(float)
        for log_entry in self.logs:
            totals[log_entry.key] += log_entry.cost_usd
        return dict(totals)


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    def mock_provider(model: str, prompt: str, max_tokens: int):
        return ("This is a mock response.", 100, 50)

    gw = AIGateway(rate_limiter=RateLimiter(requests_per_minute=5))
    gw.register_provider("anthropic", mock_provider)
    gw.register_provider("openai", mock_provider)
    gw.register_provider("local", mock_provider)

    r1 = gw.route(GatewayRequest(key="team-a", model="claude-sonnet", prompt="Hello world"))
    print(f"Response 1: provider={r1.provider}, cached={r1.cached}, cost=${r1.cost_usd:.6f}")

    r2 = gw.route(GatewayRequest(key="team-b", model="claude-sonnet", prompt="Hello world"))
    print(f"Response 2: provider={r2.provider}, cached={r2.cached}, cost=${r2.cost_usd:.6f}")

    r3 = gw.route(GatewayRequest(key="team-a", model="gpt-4o", prompt="What is 2+2?"))
    print(f"Response 3: provider={r3.provider}, cached={r3.cached}, cost=${r3.cost_usd:.6f}")

    costs = gw.get_cost_by_key()
    print(f"\nCost by key: {costs}")
    print(f"Total logs: {len(gw.logs)}")
