# Lab 20: Build a ReAct Agent from Scratch

## Problem Statement

Implement the `ReActAgent` class that drives the Reasoning + Acting (ReAct) loop.

A ReAct agent loops through three phases until the task is done:
1. **Think** — call the model with the current message history
2. **Act** — execute the tool the model requested
3. **Observe** — append the tool result back to the conversation

The loop exits when the model produces a final answer (`stop_reason == "end_turn"`) or when the iteration limit is hit.

## Your Task

Fill in the three `NotImplementedError` stubs in `starter/solution.py`:

### `_execute_tool(tool_name, tool_input) -> str`

Safely execute a registered tool. Must:
- Return `f"Unknown tool: {tool_name}"` if the tool is not registered
- Try calling `self.tool_functions[tool_name](**tool_input)` and return `str(result)`
- Catch any exception and return `f"Tool error: {e}"`

### `run(task) -> str`

Drive the ReAct loop. Must:
- Initialize `messages = [{"role": "user", "content": task}]`
- Loop up to `self.max_iterations` times:
  - Call `self.client.messages.create(model=MODEL, max_tokens=1024, tools=self.tools, messages=messages)`
  - If `stop_reason == "end_turn"`: extract and return the text from `response.content`
  - If `stop_reason == "tool_use"`:
    - Find the `tool_use` block in `response.content`
    - Call `self._execute_tool(tool_block.name, tool_block.input)`
    - Append the assistant turn: `{"role": "assistant", "content": response.content}`
    - Append the tool result: `{"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": result}]}`
- After the loop, return `"Agent reached max iterations without completing the task."`

## Example

```python
import math
from starter.solution import ReActAgent

tools = [
    {
        "name": "calculator",
        "description": "Evaluate a math expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    }
]

tool_functions = {
    "calculator": lambda expression: eval(expression, {"__builtins__": {}}, {"math": math})
}

agent = ReActAgent(tools=tools, tool_functions=tool_functions, max_iterations=5)
answer = agent.run("What is the square root of 256?")
print(answer)  # "The square root of 256 is 16."
```

## Running Tests

```bash
cd curriculum/tier-2-builder/20-agentic-loop/lab
pytest tests/ -v
```
