"""Lab 21: Full AI Agent"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from dataclasses import dataclass, field
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

AGENT_SYSTEM_PROMPT = """You are a research and analysis assistant.

## Capabilities
You have access to the following tools:
- web_search: Search the web for current information
- calculator: Evaluate mathematical expressions
- read_file: Read the contents of a local file
- take_note: Save a note to your scratchpad

## Constraints
- Do not fabricate facts. If you cannot find an answer with the available tools, say so.
- For calculations, always use the calculator tool rather than computing in your head.
- Keep your answers concise and factual.

## Behavior
- Use take_note to record key findings as you work.
- Break complex tasks into smaller steps.
- When your research is complete, provide a clear final answer.
"""


@dataclass
class AgentResult:
    """Structured return type for a completed agent run."""
    success: bool
    answer: str
    steps_taken: int
    tool_calls: list[dict] = field(default_factory=list)
    error: str | None = None

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{status}] {self.answer} ({self.steps_taken} steps)"


class FullAgent:
    def __init__(self, max_iterations: int = 10, max_consecutive_errors: int = 3):
        """
        Initialize the full agent with all four tools built in.

        # TODO:
        # self.max_iterations = max_iterations
        # self.max_consecutive_errors = max_consecutive_errors
        # self.client = get_anthropic_client()
        # self.notes = []
        # self.tool_functions = {
        #     "web_search":  lambda query: f"[Mock search] Results for: {query}",
        #     "calculator":  self._safe_calc,
        #     "read_file":   lambda path: f"[Mock file] Contents of: {path}",
        #     "take_note":   self._take_note,
        # }
        # self.tool_definitions = [...]  # See problem.md for schemas
        """
        raise NotImplementedError("Implement __init__")

    def _safe_calc(self, expression: str) -> str:
        """Evaluate a math expression safely."""
        try:
            result = eval(expression, {"__builtins__": {}}, {"math": math})
            return str(result)
        except Exception as e:
            return f"Calculation error: {e}"

    def _take_note(self, note: str) -> str:
        """Append a note to self.notes and return confirmation."""
        # TODO: self.notes.append(note); return f"Note saved: {note}"
        raise NotImplementedError("Implement _take_note")

    def get_notes(self) -> list[str]:
        """Return all notes taken during the agent run."""
        # TODO: return self.notes
        raise NotImplementedError("Implement get_notes")

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """
        Execute a registered tool safely.

        # TODO:
        # if tool_name not in self.tool_functions:
        #     return f"Unknown tool: {tool_name}"
        # try:
        #     return str(self.tool_functions[tool_name](**tool_input))
        # except Exception as e:
        #     return f"Tool error: {e}"
        """
        raise NotImplementedError("Implement _execute_tool")

    def run(self, task: str) -> AgentResult:
        """
        Run the full ReAct loop with error budget. Returns AgentResult.

        # TODO:
        # messages = [{"role": "user", "content": task}]
        # consecutive_errors = 0
        # tool_calls = []
        # steps = 0
        #
        # for i in range(self.max_iterations):
        #     steps += 1
        #     response = self.client.messages.create(
        #         model=MODEL,
        #         max_tokens=1024,
        #         system=AGENT_SYSTEM_PROMPT,
        #         tools=self.tool_definitions,
        #         messages=messages,
        #     )
        #
        #     if response.stop_reason == "end_turn":
        #         answer = ""
        #         for block in response.content:
        #             if hasattr(block, "text"):
        #                 answer = block.text
        #                 break
        #         return AgentResult(success=True, answer=answer, steps_taken=steps, tool_calls=tool_calls)
        #
        #     if response.stop_reason == "tool_use":
        #         tool_block = next(b for b in response.content if b.type == "tool_use")
        #         result = self._execute_tool(tool_block.name, tool_block.input)
        #
        #         tool_calls.append({"tool": tool_block.name, "input": tool_block.input, "result": result})
        #
        #         if result.startswith("Error:") or result.startswith("Unknown tool:") or result.startswith("Tool error:"):
        #             consecutive_errors += 1
        #             if consecutive_errors >= self.max_consecutive_errors:
        #                 return AgentResult(
        #                     success=False,
        #                     answer=f"Agent aborted: {self.max_consecutive_errors} consecutive tool errors.",
        #                     steps_taken=steps,
        #                     tool_calls=tool_calls,
        #                     error=result,
        #                 )
        #         else:
        #             consecutive_errors = 0
        #
        #         messages.append({"role": "assistant", "content": response.content})
        #         messages.append({
        #             "role": "user",
        #             "content": [{"type": "tool_result", "tool_use_id": tool_block.id, "content": result}]
        #         })
        #
        # return AgentResult(
        #     success=False,
        #     answer="Agent reached max iterations without completing the task.",
        #     steps_taken=steps,
        #     tool_calls=tool_calls,
        #     error="max_iterations_exceeded",
        # )
        raise NotImplementedError("Implement run")


# ---------------------------------------------------------------------------
# Quick manual test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    agent = FullAgent(max_iterations=5)
    result = agent.run("What is the square root of 1024?")
    print(result)
    if agent.get_notes():
        print("Notes:", agent.get_notes())
