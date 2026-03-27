"""Tests for Lab 21: Full AI Agent"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock, patch


def make_end_turn_response(text: str = "The answer is 32."):
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [text_block]
    return response


def make_tool_use_response(tool_name: str, tool_input: dict, tool_use_id: str = "tu_001"):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = tool_use_id

    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [tool_block]
    return response


def make_agent(max_iterations=5, max_consecutive_errors=3):
    from solution import FullAgent
    with patch("solution.get_anthropic_client") as mock_factory:
        mock_client = MagicMock()
        mock_factory.return_value = mock_client
        agent = FullAgent(max_iterations=max_iterations, max_consecutive_errors=max_consecutive_errors)
        agent.client = mock_client
    return agent, mock_client


class TestExecuteTool(unittest.TestCase):

    def test_calculator_returns_correct_result(self):
        """_execute_tool with calculator returns the evaluated result."""
        agent, _ = make_agent()
        result = agent._execute_tool("calculator", {"expression": "2 ** 8"})
        self.assertEqual(result, "256")

    def test_unknown_tool_returns_error(self):
        """_execute_tool returns error string for unregistered tool names."""
        agent, _ = make_agent()
        result = agent._execute_tool("does_not_exist", {})
        self.assertIn("Unknown tool", result)

    def test_execute_tool_catches_exceptions(self):
        """_execute_tool catches exceptions and returns an error string."""
        agent, _ = make_agent()
        # Calculator with bad expression should not raise, should return error string
        result = agent._execute_tool("calculator", {"expression": "1/0"})
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_take_note_stores_note_and_returns_confirmation(self):
        """take_note stores the note and returns a confirmation string."""
        agent, _ = make_agent()
        result = agent._execute_tool("take_note", {"note": "Important finding"})
        self.assertIsInstance(result, str)
        self.assertIn("Note saved", result)
        self.assertIn("Important finding", agent.get_notes())

    def test_get_notes_returns_list(self):
        """get_notes returns the list of notes in order."""
        agent, _ = make_agent()
        agent._execute_tool("take_note", {"note": "first"})
        agent._execute_tool("take_note", {"note": "second"})
        notes = agent.get_notes()
        self.assertEqual(notes, ["first", "second"])


class TestRun(unittest.TestCase):

    def test_run_returns_agent_result(self):
        """run() returns an AgentResult instance."""
        from solution import AgentResult
        agent, mock_client = make_agent()
        mock_client.messages.create.return_value = make_end_turn_response("Done.")
        result = agent.run("What is 2+2?")
        self.assertIsInstance(result, AgentResult)

    def test_run_success_on_end_turn(self):
        """run() returns AgentResult with success=True when model produces end_turn."""
        agent, mock_client = make_agent()
        mock_client.messages.create.return_value = make_end_turn_response("42")
        result = agent.run("What is the answer?")
        self.assertTrue(result.success)
        self.assertEqual(result.answer, "42")

    def test_run_failure_on_max_iterations(self):
        """run() returns AgentResult with success=False when max_iterations exceeded."""
        agent, mock_client = make_agent(max_iterations=3)
        mock_client.messages.create.return_value = make_tool_use_response(
            "calculator", {"expression": "1+1"}
        )
        with patch.object(agent, "_execute_tool", return_value="2"):
            result = agent.run("loop forever")
        self.assertFalse(result.success)
        self.assertIn("max iterations", result.answer.lower())

    def test_run_failure_on_error_budget_exceeded(self):
        """run() returns AgentResult with success=False when consecutive errors hit budget."""
        agent, mock_client = make_agent(max_iterations=10, max_consecutive_errors=3)
        mock_client.messages.create.return_value = make_tool_use_response(
            "calculator", {"expression": "bad"}
        )
        with patch.object(agent, "_execute_tool", return_value="Error: bad expression"):
            result = agent.run("do something broken")
        self.assertFalse(result.success)
        self.assertEqual(mock_client.messages.create.call_count, 3)

    def test_run_tool_calls_recorded(self):
        """run() records each tool call in AgentResult.tool_calls."""
        agent, mock_client = make_agent()
        mock_client.messages.create.side_effect = [
            make_tool_use_response("calculator", {"expression": "3*3"}, "tu_1"),
            make_end_turn_response("9"),
        ]
        with patch.object(agent, "_execute_tool", return_value="9"):
            result = agent.run("What is 3 squared?")
        self.assertEqual(len(result.tool_calls), 1)
        self.assertEqual(result.tool_calls[0]["tool"], "calculator")
        self.assertEqual(result.tool_calls[0]["result"], "9")


if __name__ == "__main__":
    unittest.main()
