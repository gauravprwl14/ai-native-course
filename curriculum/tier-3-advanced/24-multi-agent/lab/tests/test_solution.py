"""Tests for Lab 24 — Multi-Agent Systems"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

# LAB_TARGET=solution runs tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def _make_mock_client(response_text: str = "mock response"):
    """Create a mock Anthropic client that returns response_text."""
    mock_content = MagicMock()
    mock_content.text = response_text

    mock_response = MagicMock()
    mock_response.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


class TestBaseAgent(unittest.TestCase):
    def _make_agent(self, response_text="test output"):
        from solution import BaseAgent
        mock_client = _make_mock_client(response_text)
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = BaseAgent(name="TestAgent", system_prompt="You are a test agent.")
        agent.client = mock_client
        return agent

    def test_run_returns_string(self):
        agent = self._make_agent("test output")
        result = agent.run("do something")
        self.assertIsInstance(result, str)

    def test_run_returns_api_response_text(self):
        agent = self._make_agent("specific output text")
        result = agent.run("do something")
        self.assertEqual(result, "specific output text")

    def test_run_calls_api_once(self):
        agent = self._make_agent()
        agent.run("do something")
        agent.client.messages.create.assert_called_once()

    def test_run_passes_task_as_user_message(self):
        agent = self._make_agent()
        agent.run("my test task")
        call_kwargs = agent.client.messages.create.call_args.kwargs
        messages = call_kwargs.get("messages", [])
        user_contents = [m["content"] for m in messages if m.get("role") == "user"]
        self.assertTrue(any("my test task" in c for c in user_contents))

    def test_agent_stores_name(self):
        from solution import BaseAgent
        mock_client = _make_mock_client()
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = BaseAgent(name="MyAgent", system_prompt="prompt")
        self.assertEqual(agent.name, "MyAgent")

    def test_agent_stores_system_prompt(self):
        from solution import BaseAgent
        mock_client = _make_mock_client()
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = BaseAgent(name="MyAgent", system_prompt="custom prompt")
        self.assertEqual(agent.system_prompt, "custom prompt")


class TestResearchAgent(unittest.TestCase):
    def test_is_subclass_of_base_agent(self):
        from solution import ResearchAgent, BaseAgent
        mock_client = _make_mock_client()
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = ResearchAgent()
        self.assertIsInstance(agent, BaseAgent)

    def test_has_name(self):
        from solution import ResearchAgent
        mock_client = _make_mock_client()
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = ResearchAgent()
        self.assertIsNotNone(agent.name)
        self.assertIsInstance(agent.name, str)

    def test_has_system_prompt(self):
        from solution import ResearchAgent
        mock_client = _make_mock_client()
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = ResearchAgent()
        self.assertIsNotNone(agent.system_prompt)
        self.assertGreater(len(agent.system_prompt), 0)


class TestWriterAgent(unittest.TestCase):
    def test_is_subclass_of_base_agent(self):
        from solution import WriterAgent, BaseAgent
        mock_client = _make_mock_client()
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = WriterAgent()
        self.assertIsInstance(agent, BaseAgent)

    def test_has_system_prompt(self):
        from solution import WriterAgent
        mock_client = _make_mock_client()
        with patch("solution.get_anthropic_client", return_value=mock_client):
            agent = WriterAgent()
        self.assertGreater(len(agent.system_prompt), 0)


class TestOrchestrator(unittest.TestCase):
    def _make_orchestrator(self, research_text="research output", article_text="article output"):
        from solution import Orchestrator

        # Create separate mocks for researcher and writer calls
        call_count = [0]
        responses = [research_text, article_text]

        def side_effect(**kwargs):
            mock_content = MagicMock()
            mock_content.text = responses[min(call_count[0], len(responses) - 1)]
            mock_response = MagicMock()
            mock_response.content = [mock_content]
            call_count[0] += 1
            return mock_response

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = side_effect

        with patch("solution.get_anthropic_client", return_value=mock_client):
            orch = Orchestrator()
        # Override clients on sub-agents
        orch.researcher.client = mock_client
        orch.writer.client = mock_client
        return orch, mock_client

    def test_run_returns_dict(self):
        orch, _ = self._make_orchestrator()
        result = orch.run("test topic")
        self.assertIsInstance(result, dict)

    def test_run_returns_topic_key(self):
        orch, _ = self._make_orchestrator()
        result = orch.run("test topic")
        self.assertIn("topic", result)

    def test_run_returns_research_key(self):
        orch, _ = self._make_orchestrator()
        result = orch.run("test topic")
        self.assertIn("research", result)

    def test_run_returns_article_key(self):
        orch, _ = self._make_orchestrator()
        result = orch.run("test topic")
        self.assertIn("article", result)

    def test_run_topic_matches_input(self):
        orch, _ = self._make_orchestrator()
        result = orch.run("electric vehicles")
        self.assertEqual(result["topic"], "electric vehicles")

    def test_run_research_is_string(self):
        orch, _ = self._make_orchestrator()
        result = orch.run("test topic")
        self.assertIsInstance(result["research"], str)

    def test_run_article_is_string(self):
        orch, _ = self._make_orchestrator()
        result = orch.run("test topic")
        self.assertIsInstance(result["article"], str)

    def test_run_calls_api_twice(self):
        orch, mock_client = self._make_orchestrator()
        orch.run("test topic")
        self.assertEqual(mock_client.messages.create.call_count, 2)
