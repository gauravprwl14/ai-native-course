# Agent Cost Explosion

**Category:** agents
**Difficulty:** Hard
**Key Concepts:** cost attribution, per-request budget, circuit breaker, anomaly detection
**Time:** 35–45 min

---

## Problem Statement

Your agent is in production. Testing showed $0.05/request average cost. After three weeks:

- **Expected monthly bill:** $3,000 (based on test costs × volume)
- **Actual monthly bill:** $12,000

Investigation reveals:

```
Cost distribution across 60,000 requests/month:
  58,800 requests (98%): $0.04–0.07 each → $2,940 total
  1,200 requests (2%):   $4.00–12.00 each → $9,060 total
```

The 2% anomaly requests share a pattern: they exhaust `max_iterations=50` before reaching a decision. The agent iterates 40–50 tool calls doing variations of the same action before giving up.

Normal requests complete in 3–8 tool calls. These runaway requests do 40–50.

**How do you fix the cost explosion without breaking the 98% normal case?**

---

## What Makes This Hard

The naive fix is `max_iterations=10`. But your agent legitimately handles complex tasks that require 12–18 steps (e.g., "research three vendors, compare pricing, draft a recommendation memo"). Setting `max_iterations=10` breaks these.

The hard part: the distinction between "this is a legitimate 15-step workflow" and "this agent is stuck in a loop on step 4" is not visible from the iteration count alone. Both can reach iteration 15.

Three distinct behaviors need different responses:

1. **Tight loop** — same tool call repeated 5 times with identical args. Detectable and blockable immediately.
2. **Semantic drift loop** — tool calls vary slightly but are semantically equivalent (same intent, different phrasing). Harder to detect.
3. **Escalating confusion** — agent tries increasingly desperate strategies (file not found → try parent directory → try absolute path → try creating the file → ...). This is not a loop — it's productive work that happens to take many steps.

The fix that handles case 1 without harming case 3 requires per-request budget management, not iteration caps.

---

## Naive Approach

```python
MAX_ITERATIONS = 10  # Reduced from 50

async def run_agent(task: str) -> str:
    messages = [{"role": "user", "content": task}]
    for i in range(MAX_ITERATIONS):
        response = call_llm(messages)
        if response.stop_reason == "end_turn":
            return extract_text(response)
        tool_result = execute_tool(response.tool_use)
        messages.append(tool_result)
    return "Max iterations reached"
```

**Why this fails:**

1. Cuts off legitimate 12–18 step workflows. Users report "the agent gives up too early."
2. Treats all requests identically — no awareness that some tasks are inherently longer.
3. The $4–12 runaway requests are caused by loops, not by task complexity. A hard iteration cap penalizes complex tasks but only accidentally catches loops.
4. "Max iterations reached" with no useful output — the user's task was abandoned, not completed.
5. Doesn't prevent the same loop pattern from recurring. You need detection, not just a ceiling.

---

## Expert Approach

**Four mechanisms — each targets a different failure mode:**

**Mechanism 1: Per-request token budget with percentile tracking**

Track the token cost of each request. Maintain a rolling P95 of recent requests. When a request exceeds `5× P95 cost`, trigger a warning injection. At `10× P95`, hard stop.

This is self-calibrating: as your agent evolves and handles longer tasks, the budget automatically adjusts. You're not setting a fixed cap — you're detecting statistical anomalies.

**Mechanism 2: Exponential cost gates (soft → warn → stop)**

Three gates per request:
- `$0.50` — inject a "you're spending more than usual, are you stuck?" message
- `$1.00` — inject a "make a final decision with what you have" message
- `$2.00` — hard stop, return partial results

The messages at each gate give the model a chance to self-correct before the hard stop.

**Mechanism 3: Loop signature detection**

Hash `(tool_name, key_argument)` for each tool call. If the same hash appears 3+ consecutive times — or 4+ times total in one request — inject: "You have already tried X three times. Make a final decision with the information you have."

This handles tight loops without affecting workflows where the same tool is legitimately used multiple times (e.g., `read_file` called on 10 different files).

**Mechanism 4: Offline cost attribution + weekly review**

Log every request that costs over `$0.50`. Run a weekly analysis on the top 20 most expensive requests. Identify the loop patterns. Fix the underlying cause (bad tool description, ambiguous task framing, missing termination condition) rather than just capping it.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import json
import time
import hashlib
import anthropic
from dataclasses import dataclass, field
from collections import Counter, deque
from typing import Any, Optional

client = anthropic.Anthropic()

# --- Cost tracking ---

# Approximate costs per token (update as pricing changes)
INPUT_COST_PER_TOKEN = 3e-6   # $3 per 1M input tokens (Sonnet)
OUTPUT_COST_PER_TOKEN = 15e-6  # $15 per 1M output tokens (Sonnet)

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN)


# --- Rolling percentile tracker ---

class CostPercentileTracker:
    """Tracks rolling request costs to detect anomalies."""

    def __init__(self, window_size: int = 1000):
        self.costs: deque = deque(maxlen=window_size)

    def record(self, cost: float):
        self.costs.append(cost)

    def percentile(self, p: float) -> Optional[float]:
        if not self.costs:
            return None
        sorted_costs = sorted(self.costs)
        idx = int(len(sorted_costs) * p / 100)
        return sorted_costs[min(idx, len(sorted_costs) - 1)]

    def is_anomaly(self, cost: float, multiplier: float = 5.0) -> bool:
        p95 = self.percentile(95)
        if p95 is None or p95 == 0:
            return cost > 1.0  # Fallback if no history
        return cost > p95 * multiplier


# Global tracker — shared across requests
cost_tracker = CostPercentileTracker()


# --- Per-request state ---

@dataclass
class RequestBudget:
    # Hard dollar gates
    warn_threshold: float = 0.50    # First warning
    force_decide_threshold: float = 1.00  # Force a decision
    hard_stop_threshold: float = 2.00    # Terminate

    # Soft iteration gates
    max_iterations: int = 50

    # Loop detection
    loop_detection_window: int = 3   # Consecutive identical calls
    loop_total_threshold: int = 4    # Total identical calls per request

    # State
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    tool_call_hashes: list[str] = field(default_factory=list)
    recent_tool_hashes: deque = field(default_factory=lambda: deque(maxlen=5))
    warn_injected: bool = False
    force_decide_injected: bool = False
    request_id: str = ""
    start_time: float = field(default_factory=time.time)

    @property
    def current_cost(self) -> float:
        return estimate_cost(self.total_input_tokens, self.total_output_tokens)

    def record_usage(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens


def make_tool_hash(tool_name: str, tool_input: dict) -> str:
    """Hash a tool call for loop detection. Uses only the most significant argument."""
    # Take the first string value as the "key argument" — avoids over-hashing complex inputs
    key_arg = next(
        (v for v in tool_input.values() if isinstance(v, str)),
        str(list(tool_input.values())[:1])
    )
    canonical = json.dumps({"tool": tool_name, "key": key_arg[:100]}, sort_keys=True)
    return hashlib.md5(canonical.encode()).hexdigest()


def check_loop(budget: RequestBudget, tool_hash: str) -> tuple[bool, str]:
    """Detect loop conditions. Returns (is_loop, reason)."""
    # Check consecutive identical calls
    recent = list(budget.recent_tool_hashes)
    if len(recent) >= budget.loop_detection_window:
        if all(h == tool_hash for h in recent[-budget.loop_detection_window:]):
            return True, f"Same tool called {budget.loop_detection_window} consecutive times"

    # Check total identical calls across the request
    total_count = Counter(budget.tool_call_hashes)[tool_hash]
    if total_count >= budget.loop_total_threshold:
        return True, f"Same tool call pattern repeated {total_count + 1} times in this request"

    return False, ""


def check_cost_gates(budget: RequestBudget, messages: list[dict]) -> list[dict]:
    """
    Check cost thresholds and inject guidance messages.
    Returns the (potentially modified) messages list.
    """
    cost = budget.current_cost

    if cost >= budget.hard_stop_threshold:
        # Hard stop — don't continue
        raise CostLimitExceeded(
            f"Request cost ${cost:.4f} exceeded hard limit ${budget.hard_stop_threshold}. "
            f"Terminating to prevent runaway spend."
        )

    if cost >= budget.force_decide_threshold and not budget.force_decide_injected:
        budget.force_decide_injected = True
        messages = messages + [{
            "role": "user",
            "content": (
                f"[COST ALERT: This request has cost ${cost:.3f}. "
                f"You MUST make a final decision now using only the information you already have. "
                f"Do not call any more tools. Write your final answer immediately.]"
            )
        }]

    elif cost >= budget.warn_threshold and not budget.warn_injected:
        budget.warn_injected = True
        messages = messages + [{
            "role": "user",
            "content": (
                f"[NOTE: This request has used ${cost:.3f} so far, which is more than usual. "
                f"If you have been trying the same approach repeatedly, consider making a decision "
                f"with what you have rather than continuing to search.]"
            )
        }]

    return messages


class CostLimitExceeded(Exception):
    pass


# --- Main agent loop ---

TOOLS = [
    {
        "name": "search",
        "description": "Search for information",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file's contents",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
]


def execute_tool(tool_name: str, tool_input: dict) -> Any:
    """Stub tool execution — replace with real implementations."""
    if tool_name == "search":
        return f"Search results for: {tool_input['query']}"
    elif tool_name == "read_file":
        return f"Contents of {tool_input['path']}: [file data]"
    elif tool_name == "write_file":
        return f"Written to {tool_input['path']}"
    return "Tool executed"


def run_agent(task: str, request_id: str = "") -> dict[str, Any]:
    """
    Cost-controlled agent loop with loop detection, cost gates, and anomaly logging.
    """
    budget = RequestBudget(request_id=request_id or str(time.time()))
    messages = [{"role": "user", "content": task}]
    loop_events = []
    blocked_calls = 0

    try:
        for iteration in range(budget.max_iterations):
            # Check cost gates and potentially inject guidance messages
            messages = check_cost_gates(budget, messages)

            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                tools=TOOLS,
                messages=messages
            )

            # Track token usage
            budget.record_usage(
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                final_text = next(
                    (b.text for b in response.content if hasattr(b, "text")), ""
                )
                # Record cost for percentile tracking
                cost_tracker.record(budget.current_cost)
                return {
                    "result": final_text,
                    "cost": budget.current_cost,
                    "iterations": iteration + 1,
                    "loop_events": loop_events,
                    "blocked_calls": blocked_calls,
                    "status": "success",
                }

            if response.stop_reason != "tool_use":
                break

            # Process tool calls
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input = block.input
                tool_hash = make_tool_hash(tool_name, tool_input)

                # Loop detection
                is_loop, loop_reason = check_loop(budget, tool_hash)
                if is_loop:
                    blocked_calls += 1
                    event = f"Iter {iteration + 1}: BLOCKED {tool_name} — {loop_reason}"
                    loop_events.append(event)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": (
                            f"[BLOCKED: {loop_reason}. "
                            f"You have already tried this approach multiple times. "
                            f"Make a final decision with the information you already have.]"
                        ),
                        "is_error": True,
                    })
                    continue

                # Record the call
                budget.tool_call_hashes.append(tool_hash)
                budget.recent_tool_hashes.append(tool_hash)

                result = execute_tool(tool_name, tool_input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

            messages.append({"role": "user", "content": tool_results})

    except CostLimitExceeded as e:
        # Log for offline review
        log_expensive_request(budget, task, str(e))
        cost_tracker.record(budget.current_cost)
        return {
            "result": f"Request terminated: {e}",
            "cost": budget.current_cost,
            "iterations": -1,
            "loop_events": loop_events,
            "blocked_calls": blocked_calls,
            "status": "cost_limit_exceeded",
        }

    cost_tracker.record(budget.current_cost)
    return {
        "result": "Max iterations reached",
        "cost": budget.current_cost,
        "iterations": budget.max_iterations,
        "loop_events": loop_events,
        "blocked_calls": blocked_calls,
        "status": "max_iterations",
    }


def log_expensive_request(budget: RequestBudget, task: str, reason: str):
    """Log expensive requests for offline review."""
    # In production: write to a database or structured log
    print(
        f"[EXPENSIVE REQUEST LOG] "
        f"id={budget.request_id} "
        f"cost=${budget.current_cost:.4f} "
        f"input_tokens={budget.total_input_tokens} "
        f"output_tokens={budget.total_output_tokens} "
        f"duration={time.time() - budget.start_time:.1f}s "
        f"reason={reason!r} "
        f"task={task[:100]!r}"
    )


# --- Weekly cost report ---

def generate_cost_report(request_logs: list[dict]) -> dict:
    """
    Analyze request costs to identify loop patterns.
    Run weekly on your request log database.
    """
    costs = [r["cost"] for r in request_logs]
    if not costs:
        return {}

    sorted_costs = sorted(costs, reverse=True)
    expensive = [r for r in request_logs if r["cost"] > 0.50]

    return {
        "total_requests": len(request_logs),
        "total_cost": sum(costs),
        "p50_cost": sorted_costs[len(sorted_costs) // 2],
        "p95_cost": sorted_costs[int(len(sorted_costs) * 0.05)],
        "p99_cost": sorted_costs[int(len(sorted_costs) * 0.01)],
        "expensive_request_count": len(expensive),
        "expensive_request_total_cost": sum(r["cost"] for r in expensive),
        "top_expensive_tasks": [r["task"][:100] for r in sorted(expensive, key=lambda x: x["cost"], reverse=True)[:10]],
    }


if __name__ == "__main__":
    # Normal request
    result = run_agent(
        "Search for information about FastAPI and summarize its key features.",
        request_id="req-001"
    )
    print(f"Status: {result['status']}")
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Iterations: {result['iterations']}")
    if result["loop_events"]:
        print("Loop events:")
        for e in result["loop_events"]:
            print(f"  {e}")

    print(f"\nCost tracker P95: ${cost_tracker.percentile(95)}")
    print(f"Is anomaly check (x5 P95): {cost_tracker.is_anomaly(result['cost'])}")
```

</details>

---

## Interview Version

**Opening (20 seconds):** "98% of requests cost $0.05. 2% cost $4–12. The 2% is generating 75% of your bill. The fix for the 98% is: do nothing — don't change anything that affects normal behavior. The fix for the 2% is: detect the loop pattern and stop it before it reaches iteration 50."

**Draw the cost gate stack:**
```
Per-request:
  ├─ Loop detection: same tool hash 3x consecutive → BLOCK + message
  ├─ $0.50: inject "are you stuck?" warning
  ├─ $1.00: inject "make a final decision now"
  └─ $2.00: hard stop

Global:
  └─ Rolling P95 tracker: cost > 5× P95 → flag for review
```

**Why not just `max_iterations=10`?** "A 15-step legitimate workflow hits the wall at step 10. The agent didn't loop — it was doing useful work. The loop detection is surgical: it blocks the same tool being called with the same arguments 3 times, while allowing 15 different tool calls to proceed normally."

**Close with math:** "2% of requests at avg $8 each vs $0.05 = $7.95 wasted per affected request. At 60k requests/month: 1,200 runaway requests × $7.95 = $9,540/month. Fix the 2% and the bill drops from $12k to $3k."

---

## Follow-up Questions

1. The cost gate injects a "make a final decision now" message at $1.00. But the model might produce a poor, incomplete answer in response to this forced termination. How do you communicate to the user that the result was truncated due to cost constraints, and what options do you give them?
2. Your loop detection hashes `(tool_name, first_string_arg)`. This catches `search("AI market size")` repeated 3 times. But it won't catch a semantic loop where the agent alternates between `search("AI market")` and `search("artificial intelligence industry")` forever. How would you extend the detection to catch semantic loops?
3. The offline weekly review identifies the top 10 most expensive request patterns. One pattern is: users asking "research everything about X and write a comprehensive report" — this legitimately takes 20+ steps and costs $0.80. How do you handle tasks where high cost is expected and appropriate?
