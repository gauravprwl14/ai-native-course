# LLM Gateway Fallback

**Category:** system-design
**Difficulty:** Expert
**Key Concepts:** multi-provider gateway, circuit breaker, fallback routing, provider health checks, latency vs reliability trade-off
**Time:** 40–45 min

---

## Problem Statement

Your application uses Claude claude-3-5-sonnet-20241022 exclusively. On a Tuesday at 2pm, Anthropic has an outage — 503 responses for 45 minutes. Your application goes down for 45 minutes. 8,000 users can't use it.

Design a multi-provider fallback system that:
- Keeps your application online during any single provider outage
- Adds less than 2 seconds of latency overhead for the 99.9% case (Anthropic is healthy)
- Requires no change to calling code — the gateway is transparent
- Handles the fallback automatically, with no manual intervention

You have access to Anthropic, OpenAI, and a self-hosted Ollama instance.

---

## What Makes This Hard

The naive fallback — "try Anthropic, if it fails, try OpenAI" — adds 2–10 seconds of wait time to **every request** during the detection window. If Anthropic is returning 503s, each request waits for the Anthropic timeout before attempting OpenAI. At 200ms timeout, this is acceptable. At the default 30-second HTTP timeout, you've just added 30 seconds to every request.

But even with a 200ms timeout, you're adding 200ms latency to every request while Anthropic is down (to detect the failure). That's the **detection window problem**: you need to know Anthropic is down before sending the request there, not after the timeout.

The core tension: **detecting failures requires experiencing them, but experiencing failures means users wait for the timeout.**

The solution — the circuit breaker pattern — solves this by separating failure detection from request routing. A background health probe detects failures without impacting user requests. The circuit state is shared across all instances. When the circuit opens, requests route to the fallback with zero wait.

A second non-obvious challenge: **model mapping**. Claude Sonnet and GPT-4o are roughly equivalent quality tiers. But the APIs have different interfaces (different max_tokens, different system prompt handling, different tool call formats). The gateway must normalize these differences transparently.

---

## Naive Approach

**Try Anthropic first. If it errors, try OpenAI.**

```python
async def call_with_fallback(prompt: str, system: str) -> str:
    try:
        response = await anthropic_client.messages.create(
            model="claude-claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            timeout=30.0  # Default timeout
        )
        return response.content[0].text
    except Exception:
        # Fall back to OpenAI
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            timeout=30.0
        )
        return response.choices[0].message.content
```

**Why this fails:**

1. **30-second detection window.** Every request waits 30 seconds for Anthropic's timeout before trying OpenAI. Users see a 30-second hang before getting a response.
2. **Repeated failures.** Every request during the outage hits Anthropic (and fails), then hits OpenAI. You're paying for 2× API calls during the entire outage window.
3. **No shared state.** If you have 100 gateway instances, each one independently discovers Anthropic is down by experiencing a timeout. You multiply the wasted requests by 100.
4. **Recovery is manual.** When Anthropic comes back up, traffic continues routing to OpenAI until you manually re-enable it or restart the service.
5. **No observability.** You don't know when the outage started, how many requests were affected, or when recovery occurred.

---

## Expert Approach

**The circuit breaker pattern with background health probes.**

**Circuit breaker states:**

```
CLOSED (normal)
  → All requests go to primary (Anthropic)
  → Monitor for failures
  → 3+ failures in 10 seconds → open circuit

OPEN (outage detected)
  → All requests go to fallback (OpenAI) immediately, zero wait
  → Background health probe runs every 30 seconds
  → Probe succeeds → move to HALF_OPEN

HALF_OPEN (testing recovery)
  → Route 1 request to primary
  → Success → CLOSED (primary restored)
  → Failure → OPEN (still down)
```

**Background health probe:**

Send a minimal test request every 30 seconds to each provider. This is the circuit state update mechanism — not user requests. The health probe costs ~$0.001/hour per provider. The trade-off: 30-second delay before detecting recovery. Acceptable for a 45-minute outage.

**Shared circuit state (Redis):**

All gateway instances share circuit state via Redis. When one instance detects Anthropic is down (3 failures in 10s window), it opens the circuit. All other instances immediately stop sending to Anthropic — without independently experiencing failures.

**Model mapping:**

```
Claude claude-3-5-sonnet-20241022 → GPT-4o         (same quality tier)
Claude claude-3-5-haiku-20241022  → GPT-4o-mini    (same quality tier)
Claude claude-3-opus-20240229  → GPT-4o         (Opus is higher, but GPT-4o is closest available)
```

**Request replay:**

Buffer the last 60 seconds of failed requests. When the circuit opens and fallback is available, replay them. Users who hit the detection window get their answers with a short delay instead of an error.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import asyncio
import time
import json
import hashlib
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable
import redis.asyncio as redis
import anthropic
import openai

# --- Circuit breaker state ---

class CircuitState(str, Enum):
    CLOSED = "closed"       # Normal: route to primary
    OPEN = "open"           # Outage: route to fallback
    HALF_OPEN = "half_open" # Testing recovery: probe primary with 1 request


@dataclass
class CircuitConfig:
    failure_threshold: int = 3        # Failures before opening
    failure_window_seconds: int = 10  # Window to count failures
    probe_interval_seconds: int = 30  # How often to probe in OPEN state
    half_open_timeout: int = 60       # How long to wait in HALF_OPEN before re-probing


# --- Shared circuit breaker (Redis-backed) ---

class CircuitBreaker:
    """
    Redis-backed circuit breaker. State is shared across all gateway instances.
    Uses Redis for durability and cross-instance coordination.
    """

    def __init__(self, redis_client: redis.Redis, provider_name: str, config: CircuitConfig):
        self.redis = redis_client
        self.provider = provider_name
        self.config = config
        self.state_key = f"circuit:{provider_name}:state"
        self.failures_key = f"circuit:{provider_name}:failures"
        self.last_probe_key = f"circuit:{provider_name}:last_probe"

    async def get_state(self) -> CircuitState:
        state = await self.redis.get(self.state_key)
        if state is None:
            return CircuitState.CLOSED
        return CircuitState(state.decode() if isinstance(state, bytes) else state)

    async def record_failure(self):
        """Record a failure. Open circuit if threshold reached."""
        pipeline = self.redis.pipeline()
        # Add failure with current timestamp to a sorted set
        now = time.time()
        pipeline.zadd(self.failures_key, {str(now): now})
        # Remove failures outside the window
        pipeline.zremrangebyscore(self.failures_key, 0, now - self.config.failure_window_seconds)
        pipeline.expire(self.failures_key, self.config.failure_window_seconds * 2)
        await pipeline.execute()

        # Count recent failures
        recent_failures = await self.redis.zcard(self.failures_key)
        if recent_failures >= self.config.failure_threshold:
            await self._open()

    async def record_success(self):
        """Record a success. If HALF_OPEN, close the circuit."""
        state = await self.get_state()
        if state == CircuitState.HALF_OPEN:
            await self._close()
        # Clear failure window on success
        await self.redis.delete(self.failures_key)

    async def _open(self):
        await self.redis.set(self.state_key, CircuitState.OPEN.value)
        print(f"[CIRCUIT BREAKER] {self.provider} circuit OPENED — routing to fallback")

    async def _close(self):
        await self.redis.set(self.state_key, CircuitState.CLOSED.value)
        await self.redis.delete(self.failures_key)
        print(f"[CIRCUIT BREAKER] {self.provider} circuit CLOSED — restored to primary")

    async def half_open(self):
        await self.redis.set(self.state_key, CircuitState.HALF_OPEN.value)
        print(f"[CIRCUIT BREAKER] {self.provider} circuit HALF-OPEN — testing recovery")

    async def should_probe(self) -> bool:
        """Check if enough time has passed to probe the provider again."""
        last_probe = await self.redis.get(self.last_probe_key)
        if last_probe is None:
            return True
        last_probe_time = float(last_probe.decode() if isinstance(last_probe, bytes) else last_probe)
        return time.time() - last_probe_time > self.config.probe_interval_seconds

    async def record_probe(self):
        await self.redis.set(self.last_probe_key, str(time.time()), ex=3600)


# --- Request buffer (for replay on recovery) ---

class RequestBuffer:
    """
    Buffers failed requests for replay when fallback becomes available.
    Keeps a rolling 60-second window of requests.
    """

    def __init__(self, redis_client: redis.Redis, max_age_seconds: int = 60):
        self.redis = redis_client
        self.max_age = max_age_seconds
        self.buffer_key = "request_buffer"

    async def add(self, request_id: str, request_data: dict):
        now = time.time()
        await self.redis.zadd(
            self.buffer_key,
            {json.dumps({"id": request_id, "data": request_data, "ts": now}): now}
        )
        # Clean up old entries
        await self.redis.zremrangebyscore(self.buffer_key, 0, now - self.max_age)

    async def get_pending(self) -> list[dict]:
        cutoff = time.time() - self.max_age
        entries = await self.redis.zrangebyscore(self.buffer_key, cutoff, "+inf")
        return [json.loads(e.decode() if isinstance(e, bytes) else e) for e in entries]

    async def clear(self):
        await self.redis.delete(self.buffer_key)


# --- Provider adapters (normalize different APIs) ---

@dataclass
class LLMRequest:
    """Normalized request format — provider-agnostic."""
    model_tier: str  # "sonnet", "haiku", "opus"
    system: Optional[str]
    messages: list[dict]  # [{"role": "user", "content": "..."}]
    max_tokens: int = 1024
    temperature: float = 0.7

@dataclass
class LLMResponse:
    """Normalized response format — provider-agnostic."""
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float


# Model mapping: tier → {provider: model_name}
MODEL_MAP = {
    "sonnet": {
        "anthropic": "claude-claude-3-5-sonnet-20241022",
        "openai": "gpt-4o",
    },
    "haiku": {
        "anthropic": "claude-claude-3-5-haiku-20241022",
        "openai": "gpt-4o-mini",
    },
    "opus": {
        "anthropic": "claude-claude-3-opus-20240229",
        "openai": "gpt-4o",  # Closest available
    },
}


async def call_anthropic(request: LLMRequest, anthropic_client: anthropic.AsyncAnthropic) -> LLMResponse:
    model_name = MODEL_MAP[request.model_tier]["anthropic"]
    start = time.time()

    response = await anthropic_client.messages.create(
        model=model_name,
        max_tokens=request.max_tokens,
        system=request.system or "",
        messages=request.messages,
    )

    return LLMResponse(
        content=response.content[0].text,
        provider="anthropic",
        model=model_name,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_ms=(time.time() - start) * 1000,
    )


async def call_openai(request: LLMRequest, openai_client: openai.AsyncOpenAI) -> LLMResponse:
    model_name = MODEL_MAP[request.model_tier]["openai"]
    start = time.time()

    # Normalize: OpenAI uses messages with system role, Anthropic uses separate system param
    openai_messages = []
    if request.system:
        openai_messages.append({"role": "system", "content": request.system})
    openai_messages.extend(request.messages)

    response = await openai_client.chat.completions.create(
        model=model_name,
        max_tokens=request.max_tokens,
        messages=openai_messages,
    )

    return LLMResponse(
        content=response.choices[0].message.content,
        provider="openai",
        model=model_name,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        latency_ms=(time.time() - start) * 1000,
    )


# --- The gateway ---

class LLMGateway:
    """
    Multi-provider gateway with circuit breaker pattern.
    Transparent to callers — same interface regardless of which provider is active.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        anthropic_client: anthropic.AsyncAnthropic,
        openai_client: openai.AsyncOpenAI,
    ):
        self.redis = redis_client
        self.anthropic_client = anthropic_client
        self.openai_client = openai_client
        self.circuit = CircuitBreaker(redis_client, "anthropic", CircuitConfig())
        self.buffer = RequestBuffer(redis_client)

    async def complete(self, request: LLMRequest, request_id: str = "") -> LLMResponse:
        """
        Complete a request. Transparently handles fallback.
        """
        state = await self.circuit.get_state()

        if state == CircuitState.CLOSED:
            return await self._try_primary(request, request_id)
        elif state == CircuitState.OPEN:
            # Check if it's time to probe
            if await self.circuit.should_probe():
                await self.circuit.half_open()
                return await self._try_primary_probe(request, request_id)
            else:
                return await self._call_fallback(request)
        else:  # HALF_OPEN
            return await self._try_primary_probe(request, request_id)

    async def _try_primary(self, request: LLMRequest, request_id: str) -> LLMResponse:
        """Call primary provider (Anthropic). On failure, record and route to fallback."""
        try:
            response = await asyncio.wait_for(
                call_anthropic(request, self.anthropic_client),
                timeout=10.0  # Short timeout — circuit opens on 3 failures in 10s
            )
            await self.circuit.record_success()
            return response
        except Exception as e:
            print(f"[GATEWAY] Anthropic failure: {e}")
            await self.circuit.record_failure()

            # Buffer this request for potential replay
            if request_id:
                await self.buffer.add(request_id, {
                    "model_tier": request.model_tier,
                    "system": request.system,
                    "messages": request.messages,
                    "max_tokens": request.max_tokens,
                })

            # Route to fallback immediately
            return await self._call_fallback(request)

    async def _try_primary_probe(self, request: LLMRequest, request_id: str) -> LLMResponse:
        """
        Half-open probe: try primary with this real request.
        Success → close circuit. Failure → reopen.
        """
        await self.circuit.record_probe()
        try:
            response = await asyncio.wait_for(
                call_anthropic(request, self.anthropic_client),
                timeout=10.0
            )
            await self.circuit.record_success()  # Closes the circuit
            return response
        except Exception as e:
            print(f"[GATEWAY] Probe failed — Anthropic still down: {e}")
            await self.circuit._open()  # Reopen
            return await self._call_fallback(request)

    async def _call_fallback(self, request: LLMRequest) -> LLMResponse:
        """Call fallback provider (OpenAI)."""
        try:
            response = await call_openai(request, self.openai_client)
            print(f"[GATEWAY] Served via fallback (OpenAI/{response.model})")
            return response
        except Exception as e:
            # Both providers failed — raise to caller
            raise RuntimeError(f"All providers failed. Last error: {e}")


# --- Background health probe ---

class HealthProbeWorker:
    """
    Runs continuously in the background.
    Probes each provider every 30 seconds.
    Updates circuit state without impacting user requests.
    """

    def __init__(
        self,
        circuit: CircuitBreaker,
        anthropic_client: anthropic.AsyncAnthropic,
        interval_seconds: int = 30,
    ):
        self.circuit = circuit
        self.anthropic_client = anthropic_client
        self.interval = interval_seconds
        self.running = False

    async def run(self):
        self.running = True
        while self.running:
            await self._probe()
            await asyncio.sleep(self.interval)

    async def _probe(self):
        """Send a minimal test request. Does not affect user traffic."""
        state = await self.circuit.get_state()
        if state == CircuitState.HALF_OPEN:
            return  # Let the gateway handle HALF_OPEN probing via real requests

        try:
            await asyncio.wait_for(
                self.anthropic_client.messages.create(
                    model="claude-claude-3-5-haiku-20241022",  # Cheapest model for probes
                    max_tokens=5,
                    messages=[{"role": "user", "content": "ping"}]
                ),
                timeout=5.0
            )
            if state == CircuitState.OPEN:
                # Provider recovered — move to half-open to validate with a real request
                await self.circuit.half_open()
                print("[HEALTH PROBE] Anthropic appears healthy — moving to HALF_OPEN")

        except Exception as e:
            if state == CircuitState.CLOSED:
                # Provider may be down — record failure
                await self.circuit.record_failure()
            print(f"[HEALTH PROBE] Anthropic probe failed: {e}")


if __name__ == "__main__":
    async def demo():
        r = redis.Redis(host="localhost", port=6379, decode_responses=False)
        anthropic_async = anthropic.AsyncAnthropic()
        openai_async = openai.AsyncOpenAI()

        gateway = LLMGateway(r, anthropic_async, openai_async)

        # Start health probe in background
        probe_worker = HealthProbeWorker(
            gateway.circuit,
            anthropic_async,
            interval_seconds=30
        )
        probe_task = asyncio.create_task(probe_worker.run())

        # Make a request through the gateway
        request = LLMRequest(
            model_tier="sonnet",
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": "What is 2 + 2?"}],
            max_tokens=50,
        )

        try:
            response = await gateway.complete(request, request_id="req-demo-001")
            print(f"Response: {response.content}")
            print(f"Provider: {response.provider} ({response.model})")
            print(f"Latency: {response.latency_ms:.0f}ms")
        except RuntimeError as e:
            print(f"All providers failed: {e}")

        probe_worker.running = False
        probe_task.cancel()
        await r.aclose()

    asyncio.run(demo())
```

</details>

---

## Interview Version

**Opening (20 seconds):** "The problem with naive fallback is the detection window. Every request waits for the Anthropic timeout before trying OpenAI. During a 45-minute outage at 8,000 users, that's 8,000 requests each waiting 10–30 seconds. The circuit breaker separates failure detection from request routing. Once the circuit opens, fallback is instant — zero wait."

**Draw the state machine:**
```
CLOSED ─────────── 3 failures in 10s ──────────→ OPEN
                                                    │
CLOSED ←── success ── HALF_OPEN ←── probe ok ──────┘
                          │
                     probe fails
                          │
                        OPEN
```

**The key insight about probes:** "The health probe is the trick. It sends a test request every 30 seconds as a background job — not a user request. The probe costs $0.001/hour. It means we know Anthropic is down within 30 seconds, without any user experiencing the detection timeout."

**Model mapping:** "Claude Sonnet maps to GPT-4o. Haiku maps to GPT-4o-mini. The gateway normalizes the different API schemas (Anthropic uses a separate `system` param, OpenAI embeds it as a system message). Callers never know which provider served them."

**During the actual 45-minute outage:** "First 3 failures open the circuit (< 10 seconds). For the remaining 44 minutes and 50 seconds, every request routes directly to OpenAI. Zero downtime. The circuit closes automatically when the health probe succeeds after Anthropic recovers."

---

## Follow-up Questions

1. Your health probe runs every 30 seconds. Anthropic has a 2-minute partial outage (some regions return 503, some are fine). Some gateway instances detect the failure, open the circuit, and route to OpenAI. Other instances don't detect it and keep routing to Anthropic (where 50% of requests fail). How do you ensure circuit state is consistent across all instances when failures are partial?
2. Your model mapping sends Claude Opus requests to GPT-4o during an outage. GPT-4o is a different quality tier for some tasks — users who rely on Opus-level reasoning may notice degraded output. How would you communicate to users that they're receiving fallback responses, and should the quality downgrade change your auto-fallback policy?
3. The request replay buffer holds 60 seconds of failed requests. When the circuit opens and fallback starts serving, you replay these buffered requests. But some requests are not idempotent (e.g., "send this email"). How do you design the replay buffer to handle non-idempotent actions safely?
