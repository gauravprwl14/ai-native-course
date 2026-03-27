# Tool Call Loop

**Category:** agents
**Difficulty:** Hard
**Key Concepts:** agent loop control, tool call budget, convergence detection, max iterations guard
**Time:** 30–45 min

---

## Problem Statement

You deploy a ReAct agent with 5 tools:
- `web_search(query: str) → list[str]`
- `parse_html(url: str) → str`
- `summarize(text: str) → str`
- `write_file(path: str, content: str) → bool`
- `read_file(path: str) → str`

In production monitoring you observe:

- **Expected cost per request:** $0.02
- **Actual cost per request (P95):** $0.12
- **Requests hitting max_tokens:** 8% (should be ~0%)
- **Tool call pattern on failing requests:**
  ```
  web_search("market size AI") → results
  parse_html("https://example.com/ai-market") → content
  web_search("AI market 2024 size") → results  ← nearly identical to call 1
  parse_html("https://example.com/ai-market") → content  ← exact duplicate
  web_search("artificial intelligence market research") → results
  parse_html("https://example.com/ai-market") → content  ← exact duplicate again
  [... continues until max_tokens]
  ```

The agent is looping. `max_iterations=50` is set but the agent hits `max_tokens` before reaching it. How do you fix this without breaking legitimate long-running tasks?

---

## What Makes This Hard

The obvious fix is `max_iterations=5`. But your agent legitimately handles tasks that require 8–12 steps (e.g., "research 5 competitors, summarize each, write a report"). Setting max_iterations=5 breaks these.

The non-obvious challenge: loops have two forms that need different detection:

1. **Exact duplicate loops:** `parse_html("https://example.com")` called 3 times with identical args. Detectable by hashing.
2. **Semantic loops:** `web_search("AI market size")` followed by `web_search("AI market research 2024")` — different args, same semantic intent, both return similar results. Harder to detect.

A second subtlety: the root cause is often not a runaway loop per se, but the model failing to synthesize what it already found. The model keeps searching because it doesn't realize it already has enough information. The fix needs to address this at the reasoning level, not just cut off tool calls.

---

## Naive Approach

```python
MAX_ITERATIONS = 5

async def run_agent(task: str) -> str:
    messages = [{"role": "user", "content": task}]
    for i in range(MAX_ITERATIONS):
        response = call_llm(messages)
        if response.stop_reason == "end_turn":
            return response.content
        tool_result = execute_tool(response.tool_use)
        messages.append(tool_result)
    return "Task incomplete — max iterations reached"
```

**Why this fails:**

1. Cuts off legitimate 8-step tasks at step 5. Users report "incomplete answers."
2. Doesn't distinguish between a productive 5-step task and a looping 5-step task.
3. The final message "Task incomplete — max iterations reached" provides no useful output.
4. No logging or visibility into why the loop happened, so you can't fix the underlying cause.

---

## Expert Approach

Four mechanisms working together:

**Mechanism 1: Exact duplicate detection (hash-based)**

Hash each tool call (tool name + args). If the same hash appears more than N times, the agent is looping.

```python
from hashlib import md5
from collections import Counter

def make_tool_call_hash(tool_name: str, tool_args: dict) -> str:
    canonical = json.dumps({"tool": tool_name, "args": tool_args}, sort_keys=True)
    return md5(canonical.encode()).hexdigest()

def check_exact_loop(tool_call_history: list[str], current_hash: str, threshold: int = 2) -> bool:
    counts = Counter(tool_call_history)
    return counts[current_hash] >= threshold
```

**Mechanism 2: Per-tool rate limiting**

Each tool has a per-request call budget. `web_search` can only be called 5 times per request. `parse_html` can only be called 10 times.

```python
TOOL_BUDGETS = {
    "web_search": 5,
    "parse_html": 10,
    "summarize": 5,
    "write_file": 3,
    "read_file": 20,
}

def check_tool_budget(tool_name: str, call_counts: dict[str, int]) -> bool:
    budget = TOOL_BUDGETS.get(tool_name, 10)
    return call_counts.get(tool_name, 0) < budget
```

**Mechanism 3: Convergence injection**

If the last N tool calls are all the same type (search → search → search), force the agent to synthesize what it has:

```python
def should_force_synthesis(recent_tools: list[str], window: int = 3) -> bool:
    if len(recent_tools) < window:
        return False
    # All recent calls are information-gathering (not writing/finalizing)
    gathering_tools = {"web_search", "parse_html", "read_file"}
    return all(t in gathering_tools for t in recent_tools[-window:])

def inject_synthesis_message(messages: list[dict]) -> list[dict]:
    return messages + [{
        "role": "user",
        "content": "You have gathered sufficient information. Stop searching and synthesize what you have found into a final answer. Do not call any more search tools."
    }]
```

**Mechanism 4: Reasoning trace audit**

Include the agent's reasoning in tool call detection. If the agent says "I need to search for X" but a previous tool result already contains X, flag it:

```python
# Include in system prompt:
LOOP_PREVENTION_INSTRUCTION = """
Before calling any tool, check:
1. Have I already called this exact tool with these exact arguments? If yes, use the result I already have.
2. Have I already retrieved information that answers this sub-question? If yes, proceed without another search.
3. Do I have enough information to answer the user's question? If yes, write the final answer now.
"""
```

**The root cause insight:** Loops usually happen because the agent doesn't recognize that it already has the information it needs. The synthesis injection (Mechanism 3) addresses this directly — it forces the agent to consolidate, even if it would otherwise keep searching.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import json
import anthropic
from hashlib import md5
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any

client = anthropic.Anthropic()

TOOL_BUDGETS = {
    "web_search": 5,
    "parse_html": 8,
    "summarize": 5,
    "write_file": 3,
    "read_file": 15,
}

GATHERING_TOOLS = {"web_search", "parse_html", "read_file"}

SYSTEM_PROMPT = """You are a research agent. You have access to tools to gather and process information.

CRITICAL RULES to avoid loops:
1. Before calling any tool, check if you already have the result from a previous call with the same arguments.
2. If you called web_search 3 times on the same topic and got similar results, stop searching — you have enough.
3. After gathering information, always ask yourself: "Do I have enough to answer the question?" If yes, write the answer.
4. Never call the same tool with the same arguments more than once.
"""

@dataclass
class AgentState:
    tool_call_hashes: list[str] = field(default_factory=list)
    tool_call_counts: dict[str, int] = field(default_factory=dict)
    recent_tools: deque = field(default_factory=lambda: deque(maxlen=4))
    total_iterations: int = 0
    max_iterations: int = 30
    synthesis_injected: bool = False


def make_call_hash(tool_name: str, tool_input: dict) -> str:
    canonical = json.dumps({"tool": tool_name, "args": tool_input}, sort_keys=True)
    return md5(canonical.encode()).hexdigest()


def check_loop_conditions(state: AgentState, tool_name: str, tool_input: dict) -> tuple[bool, str]:
    """Returns (should_block, reason)."""
    call_hash = make_call_hash(tool_name, tool_input)

    # Check exact duplicate
    hash_count = Counter(state.tool_call_hashes)[call_hash]
    if hash_count >= 2:
        return True, f"Exact duplicate: {tool_name} called with same args {hash_count + 1} times"

    # Check per-tool budget
    current_count = state.tool_call_counts.get(tool_name, 0)
    budget = TOOL_BUDGETS.get(tool_name, 10)
    if current_count >= budget:
        return True, f"Budget exceeded: {tool_name} called {current_count}/{budget} times"

    return False, ""


def should_force_synthesis(state: AgentState, synthesis_window: int = 3) -> bool:
    if len(state.recent_tools) < synthesis_window:
        return False
    if state.synthesis_injected:
        return False
    recent = list(state.recent_tools)[-synthesis_window:]
    return all(t in GATHERING_TOOLS for t in recent)


# Simulated tool implementations
def execute_tool(tool_name: str, tool_input: dict) -> Any:
    """Stub — replace with real implementations."""
    if tool_name == "web_search":
        return [f"Result for: {tool_input.get('query', '')}"]
    elif tool_name == "parse_html":
        return f"Parsed content from {tool_input.get('url', '')}"
    elif tool_name == "summarize":
        return f"Summary of: {tool_input.get('text', '')[:50]}..."
    elif tool_name == "write_file":
        return True
    elif tool_name == "read_file":
        return f"Contents of {tool_input.get('path', '')}"
    return None


TOOLS = [
    {"name": "web_search", "description": "Search the web", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "parse_html", "description": "Parse a webpage", "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "summarize", "description": "Summarize text", "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "write_file", "description": "Write a file", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "read_file", "description": "Read a file", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
]


def run_agent(task: str) -> dict[str, Any]:
    state = AgentState()
    messages = [{"role": "user", "content": task}]
    loop_events = []

    while state.total_iterations < state.max_iterations:
        state.total_iterations += 1

        # Check if synthesis should be forced
        if should_force_synthesis(state):
            state.synthesis_injected = True
            messages.append({
                "role": "user",
                "content": "You have gathered sufficient information. Stop searching and write your final answer now based on what you have found."
            })
            loop_events.append(f"Iteration {state.total_iterations}: Synthesis forced (consecutive gather pattern detected)")

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = next((b.text for b in response.content if hasattr(b, "text")), "")
            return {
                "result": final_text,
                "iterations": state.total_iterations,
                "tool_calls": dict(state.tool_call_counts),
                "loop_events": loop_events,
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

            # Check for loop conditions
            is_loop, reason = check_loop_conditions(state, tool_name, tool_input)
            if is_loop:
                loop_events.append(f"Iteration {state.total_iterations}: BLOCKED {tool_name} — {reason}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"[BLOCKED] {reason}. Use information already retrieved to formulate your answer.",
                    "is_error": True,
                })
                continue

            # Execute tool and track state
            call_hash = make_call_hash(tool_name, tool_input)
            state.tool_call_hashes.append(call_hash)
            state.tool_call_counts[tool_name] = state.tool_call_counts.get(tool_name, 0) + 1
            state.recent_tools.append(tool_name)

            result = execute_tool(tool_name, tool_input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result) if not isinstance(result, str) else result,
            })

        messages.append({"role": "user", "content": tool_results})

    return {
        "result": "Max iterations reached",
        "iterations": state.total_iterations,
        "tool_calls": dict(state.tool_call_counts),
        "loop_events": loop_events,
    }


if __name__ == "__main__":
    result = run_agent("Research the AI market size in 2024 and write a one-paragraph summary.")
    print(f"Result: {result['result'][:200]}")
    print(f"Iterations used: {result['iterations']}")
    print(f"Tool calls: {result['tool_calls']}")
    if result['loop_events']:
        print("Loop events detected:")
        for event in result['loop_events']:
            print(f"  {event}")
```

</details>

---

## Interview Version

**Opening (20 seconds):** "The $0.12 vs $0.02 cost is the diagnostic. The agent is making 6x more tool calls than expected. The question is how to detect loops without breaking legitimate long tasks."

**Draw the detection stack:**
```
Each tool call:
  ├─ Hash(tool_name + args) → already seen 2+ times? → BLOCK
  ├─ tool_call_counts[tool_name] >= budget? → BLOCK
  └─ last 3 calls all in {search, parse, read}? → INJECT SYNTHESIS MSG

Global:
  └─ total_iterations >= 30? → FORCE STOP
```

**Key insight:** "Max iterations is the coarse failsafe. The smart detection is at the tool level — exact duplicate hashing catches tight loops, per-tool budgets catch open-ended search spirals, synthesis injection addresses the root cause (model doesn't realize it has enough info)."

**Cost framing:** "8% of requests at $0.12 instead of $0.02 = $0.10 waste per affected request. At 1,000 requests/day, that's $0.10 × 80 affected requests × 30 days = $240/month from undetected loops."

---

## Follow-up Questions

1. Semantic loops are harder to detect than exact duplicates. Describe an approach to detect `web_search("AI market size")` and `web_search("artificial intelligence market research 2024")` as semantically equivalent, and what trade-offs this approach introduces.
2. Your loop detection BLOCKS a tool call and returns an error message. But the model might then call a different tool in the same spirit, creating a different loop. How would you detect this second-order behavior?
3. The synthesis injection message ("stop searching and write your answer") changes the model's behavior. What's the risk of injecting this message too aggressively (low window size), and how would you tune the threshold?
