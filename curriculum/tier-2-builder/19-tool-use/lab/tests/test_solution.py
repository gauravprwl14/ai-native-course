"""Tests for Lab 19 — Tool Use / Function Calling"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))


class TestDefineTools:
    def test_returns_list_of_two_dicts(self):
        """define_tools returns a list of exactly 2 dicts."""
        from solution import define_tools

        result = define_tools()
        assert isinstance(result, list)
        assert len(result) == 2
        for tool in result:
            assert isinstance(tool, dict)

    def test_each_tool_has_required_keys(self):
        """Each tool definition has 'name', 'description', and 'input_schema' keys."""
        from solution import define_tools

        tools = define_tools()
        required_keys = {"name", "description", "input_schema"}
        for tool in tools:
            assert required_keys.issubset(tool.keys()), (
                f"Tool {tool.get('name', '?')} is missing keys: {required_keys - tool.keys()}"
            )

    def test_tool_names_are_get_weather_and_calculate(self):
        """The two tools are named 'get_weather' and 'calculate'."""
        from solution import define_tools

        tools = define_tools()
        names = {t["name"] for t in tools}
        assert "get_weather" in names
        assert "calculate" in names

    def test_get_weather_has_location_parameter(self):
        """get_weather tool defines a 'location' parameter in its input_schema."""
        from solution import define_tools

        tools = define_tools()
        weather_tool = next(t for t in tools if t["name"] == "get_weather")
        assert "location" in weather_tool["input_schema"].get("properties", {})

    def test_calculate_has_expression_parameter(self):
        """calculate tool defines an 'expression' parameter in its input_schema."""
        from solution import define_tools

        tools = define_tools()
        calc_tool = next(t for t in tools if t["name"] == "calculate")
        assert "expression" in calc_tool["input_schema"].get("properties", {})


class TestExecuteTool:
    def test_get_weather_returns_string_with_location(self):
        """execute_tool get_weather returns a string containing the location name."""
        from solution import execute_tool

        result = execute_tool("get_weather", {"location": "Tokyo"})
        assert isinstance(result, str)
        assert "Tokyo" in result

    def test_calculate_returns_correct_result(self):
        """execute_tool calculate evaluates '2+2' and returns '4'."""
        from solution import execute_tool

        result = execute_tool("calculate", {"expression": "2+2"})
        assert result == "4"

    def test_calculate_handles_invalid_expression(self):
        """execute_tool calculate returns an error string for invalid expressions."""
        from solution import execute_tool

        result = execute_tool("calculate", {"expression": "1/0"})
        assert isinstance(result, str)
        assert "error" in result.lower() or "Error" in result

    def test_calculate_handles_syntax_error(self):
        """execute_tool calculate returns an error string for syntax errors."""
        from solution import execute_tool

        result = execute_tool("calculate", {"expression": "not valid python @@@@"})
        assert isinstance(result, str)
        assert "error" in result.lower() or "Error" in result

    def test_unknown_tool_returns_error_string(self):
        """execute_tool returns an error string for unknown tool names."""
        from solution import execute_tool

        result = execute_tool("nonexistent_tool", {})
        assert isinstance(result, str)
        assert len(result) > 0


class TestRunAgent:
    def _make_end_turn_response(self, text: str):
        """Build a mock end_turn response."""
        content_block = MagicMock()
        content_block.type = "text"
        content_block.text = text
        response = MagicMock()
        response.stop_reason = "end_turn"
        response.content = [content_block]
        return response

    def _make_tool_use_response(self, tool_name: str, tool_input: dict, tool_id: str = "toolu_01"):
        """Build a mock tool_use response."""
        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = tool_name
        tool_block.input = tool_input
        tool_block.id = tool_id
        response = MagicMock()
        response.stop_reason = "tool_use"
        response.content = [tool_block]
        return response

    def test_run_agent_returns_string(self):
        """run_agent returns a string."""
        from solution import run_agent

        end_turn = self._make_end_turn_response("The answer is 42.")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = end_turn
            mock_client_fn.return_value = mock_client

            result = run_agent("What is 6 times 7?")

        assert isinstance(result, str)

    def test_run_agent_stops_on_end_turn(self):
        """run_agent returns the model text when stop_reason is end_turn."""
        from solution import run_agent

        end_turn = self._make_end_turn_response("The weather in London is 72°F and sunny.")

        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = end_turn
            mock_client_fn.return_value = mock_client

            result = run_agent("What's the weather in London?")

        assert "London" in result or "weather" in result.lower() or "72" in result

    def test_run_agent_handles_tool_use_and_calls_execute_tool(self):
        """run_agent calls execute_tool when stop_reason is tool_use."""
        from solution import run_agent

        tool_use = self._make_tool_use_response("get_weather", {"location": "Berlin"}, "toolu_abc")
        end_turn = self._make_end_turn_response("The weather in Berlin is 72°F and sunny.")

        with patch("solution.get_anthropic_client") as mock_client_fn, \
             patch("solution.execute_tool", return_value="The weather in Berlin is 72°F and sunny.") as mock_execute:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [tool_use, end_turn]
            mock_client_fn.return_value = mock_client

            result = run_agent("What's the weather in Berlin?")

        mock_execute.assert_called_once_with("get_weather", {"location": "Berlin"})
        assert isinstance(result, str)

    def test_run_agent_respects_max_iterations(self):
        """run_agent returns a fallback message when max_iterations is exceeded."""
        from solution import run_agent

        # Always return tool_use to trigger the max_iterations guard
        tool_use = self._make_tool_use_response("get_weather", {"location": "Nowhere"}, "toolu_loop")

        with patch("solution.get_anthropic_client") as mock_client_fn, \
             patch("solution.execute_tool", return_value="mock result"):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = tool_use
            mock_client_fn.return_value = mock_client

            result = run_agent("loop forever", max_iterations=3)

        assert isinstance(result, str)
        # Should have stopped after 3 iterations
        assert mock_client.messages.create.call_count <= 3
