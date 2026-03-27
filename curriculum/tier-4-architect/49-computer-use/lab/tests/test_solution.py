"""Tests for Lab 49 — Browser Agent (Computer Use Stub)"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call
import os

_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


def _make_state(url="http://example.com", title="Test Page", text="Hello world"):
    from solution import BrowserState
    return BrowserState(url=url, title=title, visible_text=text)


class TestParseAction(unittest.TestCase):
    def test_parse_click_action(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: click\nTARGET: the Submit button\nTEXT: \nREASONING: Submit the form"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.action_type, "click")

    def test_parse_click_target(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: click\nTARGET: the Submit button\nTEXT: \nREASONING: Submit the form"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.target, "the Submit button")

    def test_parse_type_action(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: type\nTARGET: username field\nTEXT: admin@example.com\nREASONING: Enter credentials"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.action_type, "type")

    def test_parse_type_text(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: type\nTARGET: username field\nTEXT: admin@example.com\nREASONING: Enter credentials"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.text, "admin@example.com")

    def test_parse_done_action(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: done\nTARGET: \nTEXT: \nREASONING: goal achieved"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.action_type, "done")

    def test_parse_navigate_action(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: navigate\nTARGET: http://example.com/login\nTEXT: \nREASONING: go to login"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.action_type, "navigate")
        self.assertEqual(action.target, "http://example.com/login")

    def test_parse_reasoning(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: click\nTARGET: button\nTEXT: \nREASONING: because it is there"
        action = parse_action_from_llm_response(response)
        self.assertIn("because it is there", action.reasoning)

    def test_parse_invalid_returns_error(self):
        from solution import parse_action_from_llm_response
        action = parse_action_from_llm_response("this is not valid")
        self.assertEqual(action.action_type, "error")

    def test_parse_empty_string_returns_error(self):
        from solution import parse_action_from_llm_response
        action = parse_action_from_llm_response("")
        self.assertEqual(action.action_type, "error")

    def test_parse_missing_action_returns_error(self):
        from solution import parse_action_from_llm_response
        response = "TARGET: button\nTEXT: \nREASONING: no action"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.action_type, "error")

    def test_parse_handles_colon_in_value(self):
        from solution import parse_action_from_llm_response
        response = "ACTION: navigate\nTARGET: http://example.com:8080/path\nTEXT: \nREASONING: navigate with port"
        action = parse_action_from_llm_response(response)
        self.assertEqual(action.action_type, "navigate")
        self.assertIn("http://example.com:8080/path", action.target)


class TestFormatPrompt(unittest.TestCase):
    def test_prompt_contains_goal(self):
        from solution import format_prompt
        state = _make_state()
        prompt = format_prompt("find the login page", state, [])
        self.assertIn("find the login page", prompt)

    def test_prompt_contains_url(self):
        from solution import format_prompt
        state = _make_state(url="http://mysite.com/home")
        prompt = format_prompt("goal", state, [])
        self.assertIn("http://mysite.com/home", prompt)

    def test_prompt_contains_title(self):
        from solution import format_prompt
        state = _make_state(title="My Special Page")
        prompt = format_prompt("goal", state, [])
        self.assertIn("My Special Page", prompt)

    def test_prompt_contains_visible_text(self):
        from solution import format_prompt
        state = _make_state(text="Unique visible content here")
        prompt = format_prompt("goal", state, [])
        self.assertIn("Unique visible content here", prompt)

    def test_prompt_truncates_visible_text_to_500(self):
        from solution import format_prompt
        long_text = "A" * 1000
        state = _make_state(text=long_text)
        prompt = format_prompt("goal", state, [])
        # The 501st+ characters should not be in the prompt
        # We allow a bit of slack for edge cases
        self.assertNotIn("A" * 600, prompt)

    def test_prompt_no_history_shows_none(self):
        from solution import format_prompt
        state = _make_state()
        prompt = format_prompt("goal", state, [])
        # Should indicate no history in some form
        self.assertIn("none", prompt.lower())

    def test_prompt_contains_recent_history(self):
        from solution import format_prompt, AgentStep, AgentAction
        state = _make_state()
        history = [
            AgentStep(state=state, action=AgentAction(action_type="navigate"), step_number=0),
            AgentStep(state=state, action=AgentAction(action_type="click"), step_number=1),
        ]
        prompt = format_prompt("goal", state, history)
        self.assertIn("navigate", prompt)
        self.assertIn("click", prompt)

    def test_prompt_limits_history_to_last_3(self):
        from solution import format_prompt, AgentStep, AgentAction
        state = _make_state()
        history = [
            AgentStep(state=state, action=AgentAction(action_type="step0"), step_number=0),
            AgentStep(state=state, action=AgentAction(action_type="step1"), step_number=1),
            AgentStep(state=state, action=AgentAction(action_type="step2"), step_number=2),
            AgentStep(state=state, action=AgentAction(action_type="step3"), step_number=3),
            AgentStep(state=state, action=AgentAction(action_type="step4"), step_number=4),
        ]
        prompt = format_prompt("goal", state, history)
        # step0 and step1 should NOT be in the last-3 history
        self.assertNotIn("step0", prompt)
        self.assertNotIn("step1", prompt)
        # step2, step3, step4 should be present
        self.assertIn("step2", prompt)

    def test_prompt_contains_format_instructions(self):
        from solution import format_prompt
        state = _make_state()
        prompt = format_prompt("goal", state, [])
        # Prompt should mention the response format
        self.assertIn("ACTION", prompt)
        self.assertIn("REASONING", prompt)

    def test_prompt_returns_string(self):
        from solution import format_prompt
        state = _make_state()
        result = format_prompt("goal", state, [])
        self.assertIsInstance(result, str)


class TestRunAgent(unittest.TestCase):
    def _make_done_llm(self):
        return lambda p: "ACTION: done\nTARGET: \nTEXT: \nREASONING: goal reached"

    def _make_executor(self):
        return lambda state, action: _make_state(url="http://example.com/new")

    def test_run_returns_list(self):
        from solution import run_agent
        steps = run_agent("goal", _make_state(), self._make_done_llm(), self._make_executor())
        self.assertIsInstance(steps, list)

    def test_run_stops_on_done(self):
        from solution import run_agent
        steps = run_agent("goal", _make_state(), self._make_done_llm(), self._make_executor())
        self.assertEqual(steps[-1].action.action_type, "done")

    def test_run_stops_on_error(self):
        from solution import run_agent
        error_llm = lambda p: "ACTION: error\nTARGET: \nTEXT: \nREASONING: cannot proceed"
        steps = run_agent("goal", _make_state(), error_llm, self._make_executor())
        self.assertEqual(steps[-1].action.action_type, "error")

    def test_run_respects_max_steps(self):
        from solution import run_agent
        # LLM always returns click (never done) — should stop at max_steps
        click_llm = lambda p: "ACTION: click\nTARGET: button\nTEXT: \nREASONING: keep clicking"
        steps = run_agent("goal", _make_state(), click_llm, self._make_executor(), max_steps=5)
        self.assertLessEqual(len(steps), 5)

    def test_run_calls_llm_each_step(self):
        from solution import run_agent
        llm_mock = MagicMock(return_value="ACTION: done\nTARGET: \nTEXT: \nREASONING: done")
        run_agent("goal", _make_state(), llm_mock, self._make_executor())
        llm_mock.assert_called()

    def test_run_calls_executor_on_non_done_action(self):
        from solution import run_agent
        responses = iter([
            "ACTION: click\nTARGET: button\nTEXT: \nREASONING: click",
            "ACTION: done\nTARGET: \nTEXT: \nREASONING: done",
        ])
        executor_mock = MagicMock(return_value=_make_state())
        run_agent("goal", _make_state(), lambda p: next(responses), executor_mock)
        executor_mock.assert_called_once()

    def test_run_does_not_call_executor_on_done(self):
        from solution import run_agent
        executor_mock = MagicMock(return_value=_make_state())
        run_agent("goal", _make_state(), self._make_done_llm(), executor_mock)
        executor_mock.assert_not_called()

    def test_run_step_numbers_are_sequential(self):
        from solution import run_agent
        responses = iter([
            "ACTION: click\nTARGET: a\nTEXT: \nREASONING: r",
            "ACTION: click\nTARGET: b\nTEXT: \nREASONING: r",
            "ACTION: done\nTARGET: \nTEXT: \nREASONING: done",
        ])
        steps = run_agent("goal", _make_state(), lambda p: next(responses), self._make_executor())
        for i, step in enumerate(steps):
            self.assertEqual(step.step_number, i)

    def test_run_step_contains_state(self):
        from solution import run_agent, BrowserState
        initial = _make_state(url="http://start.com")
        steps = run_agent("goal", initial, self._make_done_llm(), self._make_executor())
        self.assertIsInstance(steps[0].state, BrowserState)

    def test_run_first_step_uses_initial_state(self):
        from solution import run_agent
        initial = _make_state(url="http://initial.com")
        steps = run_agent("goal", initial, self._make_done_llm(), self._make_executor())
        self.assertEqual(steps[0].state.url, "http://initial.com")

    def test_run_passes_prompt_to_llm(self):
        from solution import run_agent
        received = {}
        def capturing_llm(prompt):
            received["prompt"] = prompt
            return "ACTION: done\nTARGET: \nTEXT: \nREASONING: done"
        run_agent("my special goal", _make_state(), capturing_llm, self._make_executor())
        self.assertIn("my special goal", received.get("prompt", ""))

    def test_run_multi_step_accumulates_history(self):
        from solution import run_agent
        responses = iter([
            "ACTION: navigate\nTARGET: http://a.com\nTEXT: \nREASONING: go",
            "ACTION: click\nTARGET: button\nTEXT: \nREASONING: click",
            "ACTION: done\nTARGET: \nTEXT: \nREASONING: done",
        ])
        steps = run_agent("goal", _make_state(), lambda p: next(responses), self._make_executor())
        self.assertEqual(len(steps), 3)
        types = [s.action.action_type for s in steps]
        self.assertEqual(types, ["navigate", "click", "done"])

    def test_run_executor_receives_current_state(self):
        from solution import run_agent, BrowserState
        state_a = _make_state(url="http://a.com")
        state_b = BrowserState(url="http://b.com", title="B", visible_text="page B")
        received_states = []

        def tracking_executor(state, action):
            received_states.append(state.url)
            return state_b

        responses = iter([
            "ACTION: click\nTARGET: x\nTEXT: \nREASONING: r",
            "ACTION: done\nTARGET: \nTEXT: \nREASONING: done",
        ])
        run_agent("goal", state_a, lambda p: next(responses), tracking_executor)
        self.assertEqual(received_states[0], "http://a.com")


if __name__ == "__main__":
    unittest.main()
