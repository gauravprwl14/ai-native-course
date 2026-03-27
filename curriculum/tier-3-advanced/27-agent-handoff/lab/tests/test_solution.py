"""Tests for Lab 27: Router → Specialist Agents"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock, patch, call


def _make_llm_response(text: str) -> MagicMock:
    """Build a mock Anthropic response returning the given text."""
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    return response


# ---------------------------------------------------------------------------
# classify_intent
# ---------------------------------------------------------------------------

class TestClassifyIntent(unittest.TestCase):
    """Tests for classify_intent()"""

    INTENTS = {
        "code": "Programming and software questions",
        "database": "SQL and database questions",
        "general": "Everything else",
    }

    @patch("solution.get_anthropic_client")
    def test_returns_valid_label(self, mock_get_client):
        """classify_intent() returns a label present in the intents dict."""
        from solution import classify_intent

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response("code")

        result = classify_intent("How do I sort a list in Python?", self.INTENTS)

        self.assertIn(result, self.INTENTS)

    @patch("solution.get_anthropic_client")
    def test_returns_general_for_unknown_label(self, mock_get_client):
        """classify_intent() returns 'general' when the LLM returns an unrecognised label."""
        from solution import classify_intent

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # LLM returns a label not in intents
        mock_client.messages.create.return_value = _make_llm_response("cooking")

        result = classify_intent("How do I make pasta?", self.INTENTS)

        self.assertEqual(result, "general")

    @patch("solution.get_anthropic_client")
    def test_includes_message_in_prompt(self, mock_get_client):
        """classify_intent() includes the user message in the LLM prompt."""
        from solution import classify_intent

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.messages.create.return_value = _make_llm_response("database")

        classify_intent("unique_message_marker_abc", self.INTENTS)

        call_content = str(mock_client.messages.create.call_args)
        self.assertIn("unique_message_marker_abc", call_content)

    @patch("solution.get_anthropic_client")
    def test_handles_whitespace_in_llm_response(self, mock_get_client):
        """classify_intent() strips whitespace from the LLM's response."""
        from solution import classify_intent

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # LLM returns label with extra whitespace
        mock_client.messages.create.return_value = _make_llm_response("  code  \n")

        result = classify_intent("Python question", self.INTENTS)

        self.assertEqual(result, "code")


# ---------------------------------------------------------------------------
# route_and_execute
# ---------------------------------------------------------------------------

class TestRouteAndExecute(unittest.TestCase):
    """Tests for route_and_execute()"""

    @patch("solution.classify_intent")
    def test_calls_matching_agent(self, mock_classify):
        """route_and_execute() calls the agent matching the classified intent."""
        from solution import route_and_execute

        mock_classify.return_value = "code"
        code_agent = MagicMock(return_value="Here is the code answer.")
        general_agent = MagicMock(return_value="General answer.")
        agents = {"code": code_agent, "general": general_agent}

        result = route_and_execute("How do I sort a list?", agents)

        code_agent.assert_called_once()
        general_agent.assert_not_called()
        self.assertEqual(result, "Here is the code answer.")

    @patch("solution.classify_intent")
    def test_falls_back_to_general_when_no_match(self, mock_classify):
        """route_and_execute() uses the 'general' agent when intent has no matching specialist."""
        from solution import route_and_execute

        mock_classify.return_value = "medical"  # not in agents
        general_agent = MagicMock(return_value="General fallback answer.")
        agents = {"code": MagicMock(), "general": general_agent}

        result = route_and_execute("What vitamins should I take?", agents)

        general_agent.assert_called_once()
        self.assertEqual(result, "General fallback answer.")

    @patch("solution.classify_intent")
    def test_passes_conversation_history_to_agent(self, mock_classify):
        """route_and_execute() passes conversation_history to the agent callable."""
        from solution import route_and_execute

        mock_classify.return_value = "code"
        code_agent = MagicMock(return_value="Answer with context.")
        agents = {"code": code_agent, "general": MagicMock()}

        history = [{"role": "user", "content": "Prior message"}]
        route_and_execute("Follow-up question", agents, conversation_history=history)

        args = code_agent.call_args
        # Second argument should be the history
        passed_history = args[0][1] if args[0] else args[1].get("context", args[1].get("conversation_history"))
        # Verify history was passed (either positionally or by kwarg)
        call_str = str(code_agent.call_args)
        self.assertIn("Prior message", call_str)

    @patch("solution.classify_intent")
    def test_returns_string(self, mock_classify):
        """route_and_execute() returns a string."""
        from solution import route_and_execute

        mock_classify.return_value = "general"
        general_agent = MagicMock(return_value="Some answer.")
        agents = {"general": general_agent}

        result = route_and_execute("Any question", agents)

        self.assertIsInstance(result, str)


# ---------------------------------------------------------------------------
# AgentRouter
# ---------------------------------------------------------------------------

class TestAgentRouter(unittest.TestCase):
    """Tests for AgentRouter"""

    def _make_router(self, specialist_responses: dict[str, str] = None):
        """Build an AgentRouter with mock specialists."""
        from solution import AgentRouter

        if specialist_responses is None:
            specialist_responses = {"code": "Code answer.", "general": "General answer."}

        specialists = {
            label: MagicMock(return_value=reply)
            for label, reply in specialist_responses.items()
        }
        intents = {label: f"{label} questions" for label in specialists}
        return AgentRouter(specialists=specialists, intents=intents), specialists

    @patch("solution.classify_intent")
    def test_chat_returns_string(self, mock_classify):
        """AgentRouter.chat() returns a non-empty string."""
        from solution import AgentRouter

        mock_classify.return_value = "general"
        router, specialists = self._make_router()

        result = router.chat("Hello")

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("solution.classify_intent")
    def test_chat_routes_to_correct_specialist(self, mock_classify):
        """AgentRouter.chat() calls the specialist matching the classified intent."""
        from solution import AgentRouter

        mock_classify.return_value = "code"
        router, specialists = self._make_router({"code": "Code answer.", "general": "General."})

        router.chat("Write a sort function")

        specialists["code"].assert_called_once()
        specialists["general"].assert_not_called()

    @patch("solution.classify_intent")
    def test_chat_appends_to_history(self, mock_classify):
        """AgentRouter.chat() appends user and assistant turns to history after each call."""
        from solution import AgentRouter

        mock_classify.return_value = "general"
        router, _ = self._make_router()

        router.chat("First message")
        router.chat("Second message")

        self.assertEqual(len(router.history), 4)  # 2 user + 2 assistant turns

    @patch("solution.classify_intent")
    def test_chat_uses_fallback_for_unknown_intent(self, mock_classify):
        """AgentRouter.chat() uses the fallback when no specialist matches the intent."""
        from solution import AgentRouter

        mock_classify.return_value = "medical"  # no specialist for this
        fallback = MagicMock(return_value="Fallback response.")
        router = AgentRouter(
            specialists={"code": MagicMock(return_value="Code.")},
            intents={"code": "code questions", "medical": "medical questions"},
            fallback=fallback,
        )

        result = router.chat("What is the dosage for aspirin?")

        fallback.assert_called_once()
        self.assertEqual(result, "Fallback response.")

    @patch("solution.classify_intent")
    def test_chat_passes_history_to_specialist(self, mock_classify):
        """AgentRouter.chat() passes accumulated history to the specialist on each call."""
        from solution import AgentRouter

        mock_classify.return_value = "code"
        code_agent = MagicMock(return_value="Answer.")
        router = AgentRouter(
            specialists={"code": code_agent, "general": MagicMock(return_value="G.")},
            intents={"code": "code questions", "general": "general"},
        )

        router.chat("First turn")
        router.chat("Second turn")

        # Second call should pass the history from the first turn
        second_call_args = code_agent.call_args_list[1]
        call_str = str(second_call_args)
        self.assertIn("First turn", call_str)


if __name__ == "__main__":
    unittest.main()
