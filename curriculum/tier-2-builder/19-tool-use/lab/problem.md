# Lab 19: Tool Use / Function Calling

## Problem Statement

You are building a two-tool agent using the Anthropic tool use API. The agent can look up mock weather data and evaluate mathematical expressions. Your job is to implement the tool definitions, the tool execution logic, and the full agent loop.

## Functions to Implement

### `define_tools() -> list[dict]`

Return a list of two tool definition dicts, each with the following structure:

```python
{
    "name": str,           # unique tool name
    "description": str,    # what the tool does (used by the model to decide when to call it)
    "input_schema": {      # JSON Schema object
        "type": "object",
        "properties": {...},
        "required": [...]
    }
}
```

Tool 1 — `get_weather`:
- Description: get current weather for a city
- Parameters: `location` (string, required)

Tool 2 — `calculate`:
- Description: evaluate a mathematical expression
- Parameters: `expression` (string, required) — a math expression like `"2 ** 32"` or `"sqrt(144)"`

### `execute_tool(tool_name: str, tool_input: dict) -> str`

Execute the named tool and return the result as a string.

- `get_weather`: return `f"The weather in {tool_input['location']} is 72°F and sunny."`
- `calculate`: evaluate `tool_input["expression"]` using `eval` with:
  - `{"__builtins__": {}}` as globals (no builtins for safety)
  - `math.__dict__` as locals (so `sqrt`, `pi`, etc. are available)
  - On any exception: return `"Error: invalid expression"`
- Unknown tool: return `f"Unknown tool: {tool_name}"`

### `run_agent(user_message: str, max_iterations: int = 10) -> str`

Run the full tool use loop:

1. Create `messages = [{"role": "user", "content": user_message}]`
2. Get tools from `define_tools()`
3. Loop up to `max_iterations` times:
   a. Call `client.messages.create(model=MODEL, max_tokens=1024, tools=tools, messages=messages)`
   b. If `stop_reason == "end_turn"`: return `response.content[0].text`
   c. If `stop_reason == "tool_use"`:
      - Find the `tool_use` block: `next(b for b in response.content if b.type == "tool_use")`
      - Execute the tool: `tool_result = execute_tool(tool_block.name, tool_block.input)`
      - Append assistant content: `messages.append({"role": "assistant", "content": response.content})`
      - Append tool result: `messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": tool_result}]})`
4. If the loop ends without `end_turn`: return `"Max iterations reached"`

## Acceptance Criteria

- `define_tools()` returns a list of exactly 2 dicts
- Each dict has `name`, `description`, and `input_schema` keys
- `execute_tool("get_weather", {"location": "Tokyo"})` contains "Tokyo"
- `execute_tool("calculate", {"expression": "2+2"})` returns `"4"`
- `execute_tool("calculate", {"expression": "1/0"})` returns an error string (does not crash)
- `run_agent(message)` returns a string
- `run_agent` stops at `end_turn` and returns the final text

## Running Tests

```bash
cd curriculum/tier-2-builder/19-tool-use/lab
pytest tests/ -v
```
