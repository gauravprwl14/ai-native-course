"""Tests for Lab 20: ReAct Agent from Scratch"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock, patch, PropertyMock


def make_end_turn_response(text: str = "The answer is 42."):
    """Build a mock response with stop_reason='end_turn'."""
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [text_block]
    return response


def make_tool_use_response(tool_name: str, tool_input: dict, tool_use_id: str = "tu_123"):
    """Build a mock response with stop_reason='tool_use'."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_use_id

    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [tool_block]
    return response


class TestExecuteTool(unittest.TestCase):
    """Tests for ReActAgent._execute_tool"""

    def _make_agent(self, tool_functions=None):
        from solution import ReActAgent
        tools = []
        tf = tool_functions or {}
        with patch("solution.get_anthropic_client"):
            agent = ReActAgent(tools=tools, tool_functions=tf, max_iterations=5)
        return agent

    def test_execute_tool_returns_string_for_valid_tool(self):
        """_execute_tool returns stringified result for a registered tool."""
        agent = self._make_agent({"add": lambda a, b: a + b})
        result = agent._execute_tool("add", {"a": 2, "b": 3})
        self.assertEqual(result, "5")

    def test_execute_tool_unknown_tool_returns_error_string(self):
        """_execute_tool returns 'Unknown tool:' prefix for unregistered tools."""
        agent = self._make_agent({})
        result = agent._execute_tool("nonexistent", {})
        self.assertIn("Unknown tool:", result)
        self.assertIn("nonexistent", result)

    def test_execute_tool_catches_exception_and_returns_error_string(self):
        """_execute_tool catches exceptions and returns 'Tool error:' prefix."""
        def bad_tool(**kwargs):
            raise ValueError("something went wrong")

        agent = self._make_agent({"bad": bad_tool})
        result = agent._execute_tool("bad", {})
        self.assertIn("Tool error:", result)
        self.assertIn("something went wrong", result)

    def test_execute_tool_result_is_string(self):
        """_execute_tool always returns a str, even for numeric results."""
        agent = self._make_agent({"mul": lambda x, y: x * y})
        result = agent._execute_tool("mul", {"x": 6, "y": 7})
        self.assertIsInstance(result, str)
        self.assertEqual(result, "42")


class TestRun(unittest.TestCase):
    """Tests for ReActAgent.run"""

    def _make_agent(self, tool_functions=None, max_iterations=5):
        from solution import ReActAgent
        tools = [{"name": "calculator", "description": "math", "input_schema": {}}]
        tf = tool_functions or {"calculator": lambda expression: eval(expression)}
        with patch("solution.get_anthropic_client") as mock_client_factory:
            mock_client = MagicMock()
            mock_client_factory.return_value = mock_client
            agent = ReActAgent(tools=tools, tool_functions=tf, max_iterations=max_iterations)
            agent.client = mock_client
        return agent, mock_client

    def test_run_returns_string(self):
        """run() always returns a string."""
        agent, mock_client = self._make_agent()
        mock_client.messages.create.return_value = make_end_turn_response("Done.")
        result = agent.run("What is 2+2?")
        self.assertIsInstance(result, str)

    def test_run_stops_on_end_turn(self):
        """run() returns the model's text when stop_reason is 'end_turn'."""
        agent, mock_client = self._make_agent()
        mock_client.messages.create.return_value = make_end_turn_response("The answer is 4.")
        result = agent.run("What is 2+2?")
        self.assertEqual(result, "The answer is 4.")
        # Should have called the model exactly once
        self.assertEqual(mock_client.messages.create.call_count, 1)

    def test_run_handles_tool_use_and_calls_execute_tool(self):
        """run() calls _execute_tool when stop_reason is 'tool_use'."""
        agent, mock_client = self._make_agent()

        # First response: tool_use; second response: end_turn
        mock_client.messages.create.side_effect = [
            make_tool_use_response("calculator", {"expression": "2+2"}),
            make_end_turn_response("The answer is 4."),
        ]

        with patch.object(agent, "_execute_tool", return_value="4") as mock_exec:
            result = agent.run("What is 2+2?")

        mock_exec.assert_called_once_with("calculator", {"expression": "2+2"})
        self.assertEqual(result, "The answer is 4.")

    def test_run_returns_max_iterations_message_when_limit_exceeded(self):
        """run() returns a failure message when max_iterations is reached."""
        agent, mock_client = self._make_agent(max_iterations=3)

        # Always return tool_use to force the agent to exhaust its iterations
        mock_client.messages.create.return_value = make_tool_use_response(
            "calculator", {"expression": "1+1"}
        )

        with patch.object(agent, "_execute_tool", return_value="2"):
            result = agent.run("Loop forever")

        self.assertIn("max iterations", result.lower())
        self.assertEqual(mock_client.messages.create.call_count, 3)

    def test_run_appends_tool_result_to_messages(self):
        """run() appends the tool_result message so the model sees the observation."""
        agent, mock_client = self._make_agent()

        mock_client.messages.create.side_effect = [
            make_tool_use_response("calculator", {"expression": "9*9"}, "tu_abc"),
            make_end_turn_response("81"),
        ]

        with patch.object(agent, "_execute_tool", return_value="81"):
            agent.run("What is 9*9?")

        # Second call to messages.create should include a tool_result message
        second_call_messages = mock_client.messages.create.call_args_list[1][1]["messages"]
        tool_result_message = second_call_messages[-1]
        self.assertEqual(tool_result_message["role"], "user")
        self.assertEqual(tool_result_message["content"][0]["type"], "tool_result")
        self.assertEqual(tool_result_message["content"][0]["tool_use_id"], "tu_abc")
        self.assertEqual(tool_result_message["content"][0]["content"], "81")


if __name__ == "__main__":
    unittest.main()
