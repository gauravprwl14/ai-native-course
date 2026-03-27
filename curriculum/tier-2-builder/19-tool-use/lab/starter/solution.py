"""Lab 19: Tool Use / Function Calling"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import json
import math
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def define_tools() -> list[dict]:
    """
    Return tool definitions for get_weather and calculate.
    # TODO: Return list of two tool definition dicts with name, description, input_schema.
    # get_weather: takes "location" (string) parameter
    # calculate: takes "expression" (string) parameter - a math expression to evaluate
    """
    raise NotImplementedError("Implement define_tools")


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool and return the result as a string.
    # TODO:
    # if tool_name == "get_weather":
    #   return f"The weather in {tool_input['location']} is 72°F and sunny." (mock)
    # elif tool_name == "calculate":
    #   try: result = eval(tool_input["expression"], {"__builtins__": {}}, math.__dict__)
    #         return str(result)
    #   except: return "Error: invalid expression"
    # else: return f"Unknown tool: {tool_name}"
    """
    raise NotImplementedError("Implement execute_tool")


def run_agent(user_message: str, max_iterations: int = 10) -> str:
    """
    Run the agent loop: send message, handle tool calls, get final answer.
    Returns final text response.
    # TODO:
    # client = get_anthropic_client()
    # messages = [{"role": "user", "content": user_message}]
    # tools = define_tools()
    # for _ in range(max_iterations):
    #   response = client.messages.create(model=MODEL, max_tokens=1024, tools=tools, messages=messages)
    #   if response.stop_reason == "end_turn": return response.content[0].text
    #   if response.stop_reason == "tool_use":
    #     # find tool_use block, execute tool, append tool_result
    #     tool_use_block = next(b for b in response.content if b.type == "tool_use")
    #     tool_result = execute_tool(tool_use_block.name, tool_use_block.input)
    #     messages.append({"role": "assistant", "content": response.content})
    #     messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use_block.id, "content": tool_result}]})
    # return "Max iterations reached"
    """
    raise NotImplementedError("Implement run_agent")
