# Parallel Tool Race Condition

**Category:** agents
**Difficulty:** Expert
**Key Concepts:** tool execution ordering, read-after-write consistency, tool dependency graph, optimistic vs pessimistic concurrency
**Time:** 35–45 min

---

## Problem Statement

You parallelized tool execution in your agent to improve latency. Your agent now executes all tool calls from a single LLM response concurrently using `asyncio.gather()`.

In development and load testing, everything works correctly. In production with real traffic:

- **Failure rate:** 0.3% of requests return inconsistent state
- **Error pattern:** The `read_user_profile` tool returns a profile that was immediately overwritten by `update_user_profile` in the same tool call batch
- **Symptom:** Agent says "Your name is Alice" and then two sentences later "I've updated your name to Bob" — but both operations happened in the same parallel batch, and the read returned stale data

**Concrete scenario:**
```
LLM response triggers 3 tool calls simultaneously:
  T1: read_user_profile(user_id=123)    → returns {"name": "Alice", ...}
  T2: update_user_profile(user_id=123, name="Bob")  → writes "Bob"
  T3: read_account_balance(user_id=123) → returns $150.00

T1 and T2 run concurrently. T1 reads before T2 writes, returns stale "Alice".
LLM gets: name=Alice (stale) AND confirmation that name was updated to Bob.
LLM output is incoherent.
```

How do you architect around this without serializing all tool calls (which eliminates the performance benefit of parallelism)?

---

## What Makes This Hard

The naive fix — serialize everything — is correct for correctness but throws away the performance improvement. If you've parallelized tool calls to cut latency from 3s to 1s, full serialization is a regression.

The non-obvious challenge: you need to identify which tools can safely run in parallel and which must be ordered, and do this automatically without hardcoding every tool pair.

The key insight is that this is a well-studied problem in databases: read-after-write (RAW) hazards. Two operations on the same resource where one writes must be serialized. Two reads on the same resource can always parallelize. Two writes on independent resources can parallelize. The solution is to classify tools and detect conflicts dynamically.

The second non-obvious challenge: this isn't just about the same tool. `read_user_profile` and `update_user_profile` touch the same underlying resource (`user_profile:123`). The conflict detection needs to be at the resource level, not the tool level.

---

## Naive Approach

```python
# Attempt 1: Full serialization
async def execute_tools_serialized(tool_calls: list[ToolCall]) -> list[ToolResult]:
    results = []
    for call in tool_calls:
        result = await execute_tool(call)
        results.append(result)
    return results
```

**Why this fails (as a complete solution):**

The parallelization was done for a reason — it cut latency from 3s to 1s when 3 tools could run concurrently. Full serialization brings latency back to 3s. At 500 requests/day with users waiting for responses, this is a meaningful regression.

The correct insight is that you don't need to serialize *everything* — only operations that conflict.

```python
# Attempt 2: Serialize only when a write tool is present
async def execute_tools_naive_v2(tool_calls: list[ToolCall]) -> list[ToolResult]:
    has_write = any(is_write_tool(call.name) for call in tool_calls)
    if has_write:
        return await execute_tools_serialized(tool_calls)
    return await asyncio.gather(*[execute_tool(c) for c in tool_calls])
```

**Why this still fails:** Two write tools operating on different resources are safe to parallelize. `update_user_profile(123)` and `update_account_settings(456)` — different users, no conflict. This approach over-serializes.

---

## Expert Approach

**Step 1: Classify tools by operation type and resource**

Each tool declares:
1. Its operation type: `READ`, `WRITE`, or `READ_WRITE`
2. Its resource scope: a function that extracts the resource identifier(s) it touches

```python
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any

class OpType(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"

@dataclass
class ToolMetadata:
    op_type: OpType
    resource_fn: Callable[[dict], list[str]]  # extracts resource IDs from args

TOOL_METADATA = {
    "read_user_profile": ToolMetadata(
        op_type=OpType.READ,
        resource_fn=lambda args: [f"user_profile:{args['user_id']}"]
    ),
    "update_user_profile": ToolMetadata(
        op_type=OpType.WRITE,
        resource_fn=lambda args: [f"user_profile:{args['user_id']}"]
    ),
    "read_account_balance": ToolMetadata(
        op_type=OpType.READ,
        resource_fn=lambda args: [f"account:{args['user_id']}"]
    ),
    "transfer_funds": ToolMetadata(
        op_type=OpType.READ_WRITE,
        resource_fn=lambda args: [f"account:{args['from_id']}", f"account:{args['to_id']}"]
    ),
}
```

**Step 2: Build a dependency graph for a batch of tool calls**

Two tool calls conflict if:
1. They touch the same resource AND
2. At least one of them is a WRITE or READ_WRITE operation

```python
def build_conflict_graph(tool_calls: list[ToolCall]) -> dict[int, set[int]]:
    """
    Returns adjacency list of conflicting tool call indices.
    Conflicting calls must not execute in parallel.
    """
    conflicts = {i: set() for i in range(len(tool_calls))}

    for i, call_a in enumerate(tool_calls):
        meta_a = TOOL_METADATA.get(call_a.name)
        if not meta_a:
            continue
        resources_a = set(meta_a.resource_fn(call_a.args))

        for j, call_b in enumerate(tool_calls):
            if i >= j:
                continue
            meta_b = TOOL_METADATA.get(call_b.name)
            if not meta_b:
                continue
            resources_b = set(meta_b.resource_fn(call_b.args))

            shared_resources = resources_a & resources_b
            if not shared_resources:
                continue  # different resources, no conflict

            # Read-read: safe to parallelize
            if meta_a.op_type == OpType.READ and meta_b.op_type == OpType.READ:
                continue

            # Any other combination involving a write: conflict
            conflicts[i].add(j)
            conflicts[j].add(i)

    return conflicts
```

**Step 3: Partition into independent groups (parallel rounds)**

Tool calls with no conflicts can run in the same round. Tool calls that conflict must run in separate rounds, with the WRITE operations ordered first (write-before-read ensures freshness).

```python
def partition_into_rounds(tool_calls: list[ToolCall], conflicts: dict[int, set[int]]) -> list[list[int]]:
    """
    Returns ordered rounds. Each round can be parallelized internally.
    Rounds must execute sequentially.
    """
    # Writes first — ensure reads see fresh data
    writes = [i for i, c in enumerate(tool_calls)
               if TOOL_METADATA.get(c.name, ToolMetadata(OpType.READ, lambda a: [])).op_type != OpType.READ]
    reads = [i for i in range(len(tool_calls)) if i not in writes]

    rounds = []
    if writes:
        rounds.append(writes)
    if reads:
        rounds.append(reads)
    return rounds
```

**Step 4: Execute rounds**

```python
async def execute_tools_safe(tool_calls: list[ToolCall]) -> list[ToolResult]:
    conflicts = build_conflict_graph(tool_calls)
    rounds = partition_into_rounds(tool_calls, conflicts)

    all_results = {}
    for round_indices in rounds:
        # All calls in this round are safe to parallelize
        tasks = [execute_tool(tool_calls[i]) for i in round_indices]
        round_results = await asyncio.gather(*tasks)
        for i, result in zip(round_indices, round_results):
            all_results[i] = result

    # Return results in original order
    return [all_results[i] for i in range(len(tool_calls))]
```

**Performance result:**
- Case: 3 tools (1 write + 2 reads, all different resources): 2 rounds but reads still parallel → latency = write_time + read_time (not write + read1 + read2)
- Case: 3 tools (1 write + 2 reads, reads share resource with write): 2 rounds → write first, then reads in parallel
- Case: 3 independent reads: 1 round, fully parallel
- Full serialization only happens when every tool conflicts with every other tool

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, NamedTuple


class OpType(Enum):
    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"


@dataclass
class ToolMetadata:
    op_type: OpType
    resource_fn: Callable[[dict], list[str]]


class ToolCall(NamedTuple):
    id: str
    name: str
    args: dict


class ToolResult(NamedTuple):
    tool_use_id: str
    content: Any
    is_error: bool = False


TOOL_METADATA: dict[str, ToolMetadata] = {
    "read_user_profile": ToolMetadata(
        op_type=OpType.READ,
        resource_fn=lambda args: [f"user_profile:{args['user_id']}"]
    ),
    "update_user_profile": ToolMetadata(
        op_type=OpType.WRITE,
        resource_fn=lambda args: [f"user_profile:{args['user_id']}"]
    ),
    "read_account_balance": ToolMetadata(
        op_type=OpType.READ,
        resource_fn=lambda args: [f"account:{args['user_id']}"]
    ),
    "update_account_balance": ToolMetadata(
        op_type=OpType.WRITE,
        resource_fn=lambda args: [f"account:{args['user_id']}"]
    ),
    "transfer_funds": ToolMetadata(
        op_type=OpType.READ_WRITE,
        resource_fn=lambda args: [f"account:{args['from_id']}", f"account:{args['to_id']}"]
    ),
    "send_email": ToolMetadata(
        op_type=OpType.WRITE,
        resource_fn=lambda args: [f"email_queue:{args.get('to', 'unknown')}"]
    ),
    "read_preferences": ToolMetadata(
        op_type=OpType.READ,
        resource_fn=lambda args: [f"preferences:{args['user_id']}"]
    ),
}


def conflicts(call_a: ToolCall, call_b: ToolCall) -> bool:
    meta_a = TOOL_METADATA.get(call_a.name)
    meta_b = TOOL_METADATA.get(call_b.name)

    if not meta_a or not meta_b:
        # Unknown tools: assume conflict (safe default)
        return True

    resources_a = set(meta_a.resource_fn(call_a.args))
    resources_b = set(meta_b.resource_fn(call_b.args))

    if not (resources_a & resources_b):
        return False  # different resources, always safe

    # Same resource: read-read is safe; any write creates a conflict
    return not (meta_a.op_type == OpType.READ and meta_b.op_type == OpType.READ)


def plan_execution(tool_calls: list[ToolCall]) -> list[list[int]]:
    """
    Returns ordered rounds. Each round is a list of indices into tool_calls.
    All tools in a round can execute concurrently.
    Rounds must execute sequentially.

    Strategy: writes before reads (ensures reads see fresh data).
    Within writes: serialize conflicting writes, parallelize non-conflicting.
    Within reads: parallelize freely (reads don't conflict with reads).
    """
    n = len(tool_calls)

    write_indices = [
        i for i in range(n)
        if TOOL_METADATA.get(tool_calls[i].name, ToolMetadata(OpType.READ, lambda a: [])).op_type != OpType.READ
    ]
    read_indices = [i for i in range(n) if i not in write_indices]

    rounds = []

    # Partition writes into non-conflicting groups
    if write_indices:
        write_rounds: list[list[int]] = []
        for idx in write_indices:
            placed = False
            for round_group in write_rounds:
                # Can add to this group if no conflict with anyone already in it
                if not any(conflicts(tool_calls[idx], tool_calls[j]) for j in round_group):
                    round_group.append(idx)
                    placed = True
                    break
            if not placed:
                write_rounds.append([idx])
        rounds.extend(write_rounds)

    # All reads can go in a single parallel round
    if read_indices:
        rounds.append(read_indices)

    return rounds


async def simulate_tool_execution(call: ToolCall) -> ToolResult:
    """Stub implementation — replace with real tool dispatch."""
    await asyncio.sleep(0.1)  # simulate network call
    return ToolResult(
        tool_use_id=call.id,
        content=f"Result of {call.name}({call.args})"
    )


async def execute_tools_safe(tool_calls: list[ToolCall]) -> list[ToolResult]:
    """
    Execute tool calls with automatic conflict detection.
    Conflicting tools are serialized; non-conflicting tools run in parallel.
    """
    rounds = plan_execution(tool_calls)
    all_results: dict[int, ToolResult] = {}

    for round_idx, round_indices in enumerate(rounds):
        round_calls = [tool_calls[i] for i in round_indices]
        round_results = await asyncio.gather(
            *[simulate_tool_execution(c) for c in round_calls],
            return_exceptions=True
        )
        for i, result in zip(round_indices, round_results):
            if isinstance(result, Exception):
                all_results[i] = ToolResult(tool_use_id=tool_calls[i].id, content=str(result), is_error=True)
            else:
                all_results[i] = result

    return [all_results[i] for i in range(len(tool_calls))]


# Demonstration
async def main():
    # Scenario 1: The race condition case — read + write on same user
    print("=== Scenario 1: Read/Write conflict on same user ===")
    batch_1 = [
        ToolCall("t1", "read_user_profile", {"user_id": 123}),
        ToolCall("t2", "update_user_profile", {"user_id": 123, "name": "Bob"}),
        ToolCall("t3", "read_account_balance", {"user_id": 123}),
    ]
    rounds_1 = plan_execution(batch_1)
    print(f"Execution plan: {rounds_1}")
    print(f"Round 1 (writes): {[batch_1[i].name for i in rounds_1[0]]}")
    print(f"Round 2 (reads):  {[batch_1[i].name for i in rounds_1[1]]}")
    # Expected: update_user_profile in round 1, both reads in round 2

    print()
    print("=== Scenario 2: All independent reads ===")
    batch_2 = [
        ToolCall("t1", "read_user_profile", {"user_id": 123}),
        ToolCall("t2", "read_account_balance", {"user_id": 123}),
        ToolCall("t3", "read_preferences", {"user_id": 123}),
    ]
    rounds_2 = plan_execution(batch_2)
    print(f"Execution plan: {rounds_2}")
    print("All 3 tools in single parallel round — no conflict")

    print()
    print("=== Scenario 3: Writes to different users — safe to parallelize ===")
    batch_3 = [
        ToolCall("t1", "update_user_profile", {"user_id": 111, "name": "Alice"}),
        ToolCall("t2", "update_user_profile", {"user_id": 222, "name": "Bob"}),
        ToolCall("t3", "read_account_balance", {"user_id": 111}),
    ]
    rounds_3 = plan_execution(batch_3)
    print(f"Execution plan: {rounds_3}")
    # Both writes can parallelize (different users), then read after


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

---

## Interview Version

**Opening (20 seconds):** "0.3% failure rate from a race condition — reads returning stale data that was immediately overwritten. The naive fix is full serialization but that kills our latency gains. The right fix is to detect conflicts at the resource level and only serialize what needs to be."

**Draw the classification matrix:**

```
           Tool B: READ    Tool B: WRITE
Tool A:
  READ      PARALLEL        SERIALIZE (B writes first)
  WRITE     SERIALIZE       SERIALIZE
```

**Draw the execution plan for the failing scenario:**

```
Before fix (all parallel):
  [read_user_profile, update_user_profile, read_account_balance] → race condition

After fix:
  Round 1 (parallel): [update_user_profile]       ← writes first
  Round 2 (parallel): [read_user_profile,          ← reads after
                        read_account_balance]
```

**Key insight:** "The fix preserves most of the parallelism. Reads still parallelize freely. Independent writes parallelize. Only reads that could see stale data from a write in the same batch are delayed. In most batches, that's a 1-round overhead, not full serialization."

---

## Follow-up Questions

1. Your tool metadata registry requires every tool author to declare `op_type` and `resource_fn`. What happens when a new tool is added without these declarations? Design a safe default policy and explain its trade-offs.
2. `transfer_funds` touches two resources: `account:from_id` and `account:to_id`. If another tool in the same batch reads `account:from_id`, your system correctly serializes them. But what if the same user is both sender and receiver (transferring to themselves)? Walk through how your conflict detection handles this edge case.
3. You implement this fix and the 0.3% failure rate drops to 0.01%. Investigate: what could explain the remaining 0.01%? List at least three possible causes.
