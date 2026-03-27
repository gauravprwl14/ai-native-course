# Lab 21: Build a Multi-tool Agent

## Problem Statement

Build `FullAgent` — a complete AI agent with four tools, a system prompt, an error budget, and a structured `AgentResult` return type.

## Your Task

Implement everything in `starter/solution.py`. The file has `NotImplementedError` stubs with `# TODO:` guidance.

### `AgentResult` dataclass

Fields:
- `success: bool` — True if agent completed normally, False if aborted
- `answer: str` — the final answer text (or abort message)
- `steps_taken: int` — number of ReAct iterations used
- `tool_calls: list[dict]` — each entry: `{"tool": name, "input": input_dict, "result": result_str}`
- `error: str | None` — error message if aborted, None otherwise

### Four Tools

| Tool | Signature | Behavior |
|------|-----------|----------|
| `web_search` | `(query: str) -> str` | Return `f"[Mock search] Results for: {query}"` |
| `calculator` | `(expression: str) -> str` | `eval(expression)` in a safe namespace; return str(result) or error |
| `read_file` | `(path: str) -> str` | Return `f"[Mock file] Contents of: {path}"` |
| `take_note` | `(note: str) -> str` | Append to `self.notes`; return `f"Note saved: {note}"` |

### `FullAgent._execute_tool(tool_name, tool_input) -> str`

Same contract as Ch20: check registry, try/except, return result or error string.

### `FullAgent.run(task) -> AgentResult`

The full ReAct loop with error budget:
1. Initialize `messages`, `consecutive_errors = 0`, `tool_calls = []`, `steps = 0`
2. Loop up to `self.max_iterations`:
   - Increment `steps`
   - Call the model with system prompt, tools, messages
   - If `stop_reason == "end_turn"`: return `AgentResult(success=True, answer=text, steps_taken=steps, tool_calls=tool_calls)`
   - If `stop_reason == "tool_use"`:
     - Execute the tool, append to `tool_calls`
     - Update `consecutive_errors`: reset to 0 on success, increment on error
     - If `consecutive_errors >= self.max_consecutive_errors`: return `AgentResult(success=False, ...)`
     - Append messages
3. After loop: return `AgentResult(success=False, answer="Agent reached max iterations...", ...)`

## Running Tests

```bash
cd curriculum/tier-2-builder/21-ai-agent/lab
pytest tests/ -v
```
