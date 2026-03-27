"""Lab 20: ReAct Agent from Scratch"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


class ReActAgent:
    def __init__(self, tools: list[dict], tool_functions: dict, max_iterations: int = 10):
        """
        Initialize the ReAct agent.

        Args:
            tools: list of Anthropic tool definition dicts (name, description, input_schema)
            tool_functions: dict mapping tool_name -> callable
            max_iterations: safety limit — stop after this many think-act-observe cycles
        """
        self.tools = tools
        self.tool_functions = tool_functions
        self.max_iterations = max_iterations
        self.client = get_anthropic_client()

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """
        Execute a registered tool safely.

        Returns the tool result as a string, or an error string if:
        - the tool is not registered
        - the tool raises an exception

        # TODO:
        # if tool_name not in self.tool_functions:
        #     return f"Unknown tool: {tool_name}"
        # try:
        #     return str(self.tool_functions[tool_name](**tool_input))
        # except Exception as e:
        #     return f"Tool error: {e}"
        """
        raise NotImplementedError("Implement _execute_tool")

    def run(self, task: str) -> str:
        """
        Run the ReAct loop for a given task.

        Loop:
          1. Call the model with current message history
          2. If stop_reason == "end_turn": extract text and return it
          3. If stop_reason == "tool_use":
             a. Find the tool_use block in response.content
             b. Call _execute_tool(tool_block.name, tool_block.input)
             c. Append assistant turn (full response.content) to messages
             d. Append tool_result message to messages
          4. After max_iterations, return a graceful failure message

        # TODO:
        # messages = [{"role": "user", "content": task}]
        # for i in range(self.max_iterations):
        #     response = self.client.messages.create(
        #         model=MODEL,
        #         max_tokens=1024,
        #         tools=self.tools,
        #         messages=messages,
        #     )
        #     if response.stop_reason == "end_turn":
        #         for block in response.content:
        #             if hasattr(block, "text"):
        #                 return block.text
        #         return ""
        #     if response.stop_reason == "tool_use":
        #         tool_block = next(b for b in response.content if b.type == "tool_use")
        #         result = self._execute_tool(tool_block.name, tool_block.input)
        #         messages.append({"role": "assistant", "content": response.content})
        #         messages.append({
        #             "role": "user",
        #             "content": [{
        #                 "type": "tool_result",
        #                 "tool_use_id": tool_block.id,
        #                 "content": result,
        #             }]
        #         })
        # return "Agent reached max iterations without completing the task."
        raise NotImplementedError("Implement run")


# ---------------------------------------------------------------------------
# Quick manual test (run: python solution.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tools = [
        {
            "name": "calculator",
            "description": "Evaluate a mathematical expression and return the result.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A Python math expression, e.g. '2 ** 10' or 'math.sqrt(144)'"
                    }
                },
                "required": ["expression"]
            }
        }
    ]

    tool_functions = {
        "calculator": lambda expression: eval(
            expression, {"__builtins__": {}}, {"math": math}
        )
    }

    agent = ReActAgent(tools=tools, tool_functions=tool_functions, max_iterations=5)
    answer = agent.run("What is 2 to the power of 10, multiplied by 3?")
    print(f"Answer: {answer}")
