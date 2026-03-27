"""Lab 19: Tool Use / Function Calling — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def define_tools() -> list[dict]:
    """
    Return tool definitions for get_weather and calculate.
    """
    return [
        {
            "name": "get_weather",
            "description": "Get the current weather for a given city. Call this when the user asks about weather conditions in a location.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city name, e.g. 'London' or 'Tokyo'"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "name": "calculate",
            "description": "Evaluate a mathematical expression and return the numeric result. Supports standard math operations and functions like sqrt, sin, cos, pi.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A Python math expression to evaluate, e.g. '2 ** 32' or 'sqrt(144)' or '3.14 * 10 ** 2'"
                    }
                },
                "required": ["expression"]
            }
        }
    ]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool and return the result as a string.
    """
    if tool_name == "get_weather":
        location = tool_input.get("location", "Unknown")
        return f"The weather in {location} is 72°F and sunny."

    elif tool_name == "calculate":
        expression = tool_input.get("expression", "")
        try:
            result = eval(expression, {"__builtins__": {}}, math.__dict__)
            return str(result)
        except Exception:
            return "Error: invalid expression"

    else:
        return f"Unknown tool: {tool_name}"


def run_agent(user_message: str, max_iterations: int = 10) -> str:
    """
    Run the agent loop: send message, handle tool calls, get final answer.
    Returns final text response.
    """
    client = get_anthropic_client()
    messages = [{"role": "user", "content": user_message}]
    tools = define_tools()

    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return response.content[0].text

        if response.stop_reason == "tool_use":
            tool_use_block = next(b for b in response.content if b.type == "tool_use")
            tool_result = execute_tool(tool_use_block.name, tool_use_block.input)

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": tool_result
                }]
            })

    return "Max iterations reached"
