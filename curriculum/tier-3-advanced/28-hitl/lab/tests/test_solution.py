"""Tests for Lab 28: Human-in-the-Loop (HITL)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock

from solution import should_escalate, request_approval, HITLAgent, REQUIRES_APPROVAL, CONFIDENCE_THRESHOLD


class TestShouldEscalate(unittest.TestCase):
    """Tests for should_escalate()"""

    def test_high_risk_action_always_escalates(self):
        """Actions in REQUIRES_APPROVAL always escalate, even with high confidence."""
        for action in REQUIRES_APPROVAL:
            with self.subTest(action=action):
                self.assertTrue(should_escalate(action, 1.0))

    def test_safe_action_high_confidence_no_escalation(self):
        """Safe actions with high confidence do not escalate."""
        self.assertFalse(should_escalate("read_file", 0.95))
        self.assertFalse(should_escalate("search_web", 1.0))

    def test_low_confidence_escalates_even_for_safe_action(self):
        """Any action below CONFIDENCE_THRESHOLD escalates."""
        self.assertTrue(should_escalate("read_file", CONFIDENCE_THRESHOLD - 0.01))
        self.assertTrue(should_escalate("list_files", 0.0))

    def test_exactly_at_threshold_does_not_escalate(self):
        """Confidence exactly at CONFIDENCE_THRESHOLD should NOT escalate for safe actions."""
        self.assertFalse(should_escalate("read_file", CONFIDENCE_THRESHOLD))

    def test_returns_bool(self):
        """should_escalate returns a bool."""
        result = should_escalate("read_file", 0.9)
        self.assertIsInstance(result, bool)


class TestRequestApproval(unittest.TestCase):
    """Tests for request_approval()"""

    def test_returns_true_on_y(self):
        """Returns True when human types 'y'."""
        mock_input = MagicMock(return_value="y")
        result = request_approval("send_email", "Send promo", get_input=mock_input)
        self.assertTrue(result)

    def test_returns_true_on_yes(self):
        """Returns True when human types 'yes'."""
        mock_input = MagicMock(return_value="yes")
        result = request_approval("delete_file", "Delete logs", get_input=mock_input)
        self.assertTrue(result)

    def test_returns_false_on_n(self):
        """Returns False when human types 'n'."""
        mock_input = MagicMock(return_value="n")
        result = request_approval("make_payment", "Pay $500", get_input=mock_input)
        self.assertFalse(result)

    def test_get_input_is_called_once(self):
        """get_input is called exactly once per request_approval call."""
        mock_input = MagicMock(return_value="y")
        request_approval("send_email", "context", get_input=mock_input)
        mock_input.assert_called_once()


class TestHITLAgent(unittest.TestCase):
    """Tests for HITLAgent.execute_action()"""

    def _make_agent(self, user_response="y"):
        mock_input = MagicMock(return_value=user_response)
        agent = HITLAgent(get_input=mock_input)
        return agent, mock_input

    def test_safe_action_executes_without_asking(self):
        """Safe, high-confidence actions execute without calling get_input."""
        agent, mock_input = self._make_agent()
        result = agent.execute_action("read_file", "Read config.json", confidence=0.95)
        self.assertTrue(result["executed"])
        self.assertTrue(result["approved"])
        mock_input.assert_not_called()

    def test_high_risk_action_asks_for_approval(self):
        """High-risk actions call get_input for approval."""
        agent, mock_input = self._make_agent(user_response="y")
        result = agent.execute_action("send_email", "Send newsletter", confidence=0.99)
        self.assertTrue(result["approved"])
        self.assertTrue(result["executed"])
        mock_input.assert_called_once()

    def test_rejected_action_not_executed(self):
        """When human rejects, executed=False and approved=False."""
        agent, mock_input = self._make_agent(user_response="n")
        result = agent.execute_action("delete_file", "Delete all logs", confidence=0.99)
        self.assertFalse(result["approved"])
        self.assertFalse(result["executed"])

    def test_action_log_records_all_actions(self):
        """action_log contains an entry for every execute_action call."""
        agent, _ = self._make_agent(user_response="y")
        agent.execute_action("read_file", "Read", confidence=0.95)
        agent.execute_action("send_email", "Email", confidence=0.95)
        self.assertEqual(len(agent.action_log), 2)

    def test_result_dict_has_required_keys(self):
        """Result dict contains 'action', 'approved', and 'executed' keys."""
        agent, _ = self._make_agent(user_response="y")
        result = agent.execute_action("read_file", "context", confidence=0.95)
        self.assertIn("action", result)
        self.assertIn("approved", result)
        self.assertIn("executed", result)


if __name__ == "__main__":
    unittest.main()
