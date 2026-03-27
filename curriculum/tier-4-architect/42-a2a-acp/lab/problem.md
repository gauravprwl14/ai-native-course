# Lab 42 — Agent Delegation System

## Problem Statement

You will implement a simplified A2A-style (Agent-to-Agent) agent delegation system in pure Python. No external dependencies. The goal is to understand the core mechanics of agent discovery and task delegation.

---

### Class 1: `AgentCard`

A dataclass representing an agent's capabilities manifest.

**Fields:**
- `name: str` — unique agent identifier
- `description: str` — human-readable description of what this agent does
- `capabilities: list[str]` — list of capability tags (e.g., `["research", "fact-finding"]`)
- `endpoint: str` — how to reach the agent (default `"local"` for in-process agents)

---

### Class 2: `TaskResult`

A dataclass representing the result of a delegated task.

**Fields:**
- `agent_name: str` — which agent handled the task
- `task: str` — the task description that was delegated
- `result: str` — the agent's output
- `success: bool` — whether the task completed successfully

---

### Class 3: `AgentRegistry`

A central registry where agents register themselves and orchestrators discover them.

#### `__init__(self)`
Initialise with empty `_agents` dict and empty `_handlers` dict.

#### `register(self, card: AgentCard, handler) -> None`
- Store `card` in `self._agents` keyed by `card.name`
- Store `handler` in `self._handlers` keyed by `card.name`

#### `discover(self, capability: str) -> list[AgentCard]`
Return a list of `AgentCard` objects where `capability` is in `card.capabilities`.
Return an empty list if no agents match.

#### `get_handler(self, agent_name: str)`
Return the handler callable for `agent_name`.
Raise `KeyError` if `agent_name` is not registered.

---

### Function: `delegate_task(task: str, required_capability: str, registry: AgentRegistry) -> TaskResult`

Find the best agent for the task and delegate to it.

**Steps:**
1. Call `registry.discover(required_capability)` to get candidate agents
2. If no candidates, return:
   ```python
   TaskResult(agent_name="none", task=task, result="No agent found", success=False)
   ```
3. Pick `candidates[0]` (first match — simplest selection strategy)
4. Get the handler: `handler = registry.get_handler(chosen.name)`
5. Call `handler(task)` to get the result string
6. Return `TaskResult(agent_name=chosen.name, task=task, result=result, success=True)`

---

### Function: `compose_multi_agent(tasks: list[tuple[str, str]], registry: AgentRegistry) -> list[TaskResult]`

Delegate multiple tasks to appropriate agents in sequence.

**Steps:**
1. For each `(task, capability)` tuple in `tasks`, call `delegate_task(task, capability, registry)`
2. Collect and return all `TaskResult` objects as a list

---

## Mock Agents (for testing and manual use)

```python
registry = AgentRegistry()

registry.register(
    AgentCard(
        name="ResearchAgent",
        description="Searches for and summarises factual information",
        capabilities=["research", "fact-finding"],
    ),
    handler=lambda task: f"[Research] Key facts about: {task}"
)

registry.register(
    AgentCard(
        name="SummaryAgent",
        description="Creates concise summaries of longer content",
        capabilities=["summarise", "writing"],
    ),
    handler=lambda task: f"[Summary] {task[:30]}..."
)
```

---

## Files

| File | Description |
|------|-------------|
| `starter/solution.py` | Fill in the `# TODO` comments |
| `solution/solution.py` | Reference implementation |
| `tests/test_solution.py` | Automated tests (no real agents or API calls) |

## How to Run

```bash
# Run your implementation
cd curriculum/tier-4-architect/42-a2a-acp/lab/starter
python solution.py

# Run tests
cd curriculum/tier-4-architect/42-a2a-acp/lab
pytest tests/ -v
```
