"""Tests for Lab 23 — Planning & Task Decomposition"""

import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch
from dataclasses import fields

# LAB_TARGET=solution runs tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


def _make_mock_client(response_text: str):
    """Create a mock Anthropic client that returns response_text."""
    mock_content = MagicMock()
    mock_content.text = response_text

    mock_response = MagicMock()
    mock_response.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    return mock_client


SAMPLE_PLAN = [
    {"id": "task-1", "description": "Research the topic", "depends_on": []},
    {"id": "task-2", "description": "Write a summary", "depends_on": ["task-1"]},
    {"id": "task-3", "description": "Review and finalise", "depends_on": ["task-2"]},
]


class TestTaskResultDataclass(unittest.TestCase):
    def test_taskresult_has_task_id_field(self):
        from solution import TaskResult
        field_names = [f.name for f in fields(TaskResult)]
        self.assertIn("task_id", field_names)

    def test_taskresult_has_success_field(self):
        from solution import TaskResult
        field_names = [f.name for f in fields(TaskResult)]
        self.assertIn("success", field_names)

    def test_taskresult_has_output_field(self):
        from solution import TaskResult
        field_names = [f.name for f in fields(TaskResult)]
        self.assertIn("output", field_names)

    def test_taskresult_has_error_field(self):
        from solution import TaskResult
        field_names = [f.name for f in fields(TaskResult)]
        self.assertIn("error", field_names)

    def test_taskresult_instantiates_correctly(self):
        from solution import TaskResult
        r = TaskResult(task_id="task-1", success=True, output="done")
        self.assertEqual(r.task_id, "task-1")
        self.assertTrue(r.success)
        self.assertEqual(r.output, "done")


class TestGeneratePlan(unittest.TestCase):
    def _run_generate_plan(self, goal: str, context: str = ""):
        from solution import generate_plan
        plan_json = json.dumps(SAMPLE_PLAN)
        mock_client = _make_mock_client(plan_json)
        with patch("solution.get_anthropic_client", return_value=mock_client):
            return generate_plan(goal, context)

    def test_returns_a_list(self):
        result = self._run_generate_plan("Write a report")
        self.assertIsInstance(result, list)

    def test_each_item_is_a_dict(self):
        result = self._run_generate_plan("Write a report")
        for item in result:
            self.assertIsInstance(item, dict)

    def test_each_task_has_id_key(self):
        result = self._run_generate_plan("Write a report")
        for item in result:
            self.assertIn("id", item)

    def test_each_task_has_description_key(self):
        result = self._run_generate_plan("Write a report")
        for item in result:
            self.assertIn("description", item)

    def test_each_task_has_depends_on_key(self):
        result = self._run_generate_plan("Write a report")
        for item in result:
            self.assertIn("depends_on", item)

    def test_calls_api_with_temperature_zero(self):
        from solution import generate_plan
        mock_client = _make_mock_client(json.dumps(SAMPLE_PLAN))
        with patch("solution.get_anthropic_client", return_value=mock_client):
            generate_plan("test goal")
        call_kwargs = mock_client.messages.create.call_args
        # temperature should be 0 (passed as kwarg or positional)
        kwargs = call_kwargs.kwargs if call_kwargs.kwargs else {}
        args_dict = dict(zip(["model", "max_tokens", "temperature", "messages"], call_kwargs.args))
        temperature = kwargs.get("temperature", args_dict.get("temperature"))
        self.assertEqual(temperature, 0)


class TestExecuteTask(unittest.TestCase):
    def _run_execute_task(self, task, available_results):
        from solution import execute_task
        mock_client = _make_mock_client("Task output text")
        with patch("solution.get_anthropic_client", return_value=mock_client):
            return execute_task(task, available_results)

    def test_returns_task_result(self):
        from solution import TaskResult
        task = {"id": "task-1", "description": "Do something", "depends_on": []}
        result = self._run_execute_task(task, {})
        self.assertIsInstance(result, TaskResult)

    def test_success_true_for_no_dependency_task(self):
        task = {"id": "task-1", "description": "Do something", "depends_on": []}
        result = self._run_execute_task(task, {})
        self.assertTrue(result.success)

    def test_task_id_matches_input(self):
        task = {"id": "task-1", "description": "Do something", "depends_on": []}
        result = self._run_execute_task(task, {})
        self.assertEqual(result.task_id, "task-1")

    def test_output_is_string(self):
        task = {"id": "task-1", "description": "Do something", "depends_on": []}
        result = self._run_execute_task(task, {})
        self.assertIsInstance(result.output, str)

    def test_fails_when_dependency_not_met(self):
        from solution import TaskResult
        task = {"id": "task-2", "description": "Use prior result", "depends_on": ["task-1"]}
        # task-1 not in available_results
        result = self._run_execute_task(task, {})
        self.assertFalse(result.success)

    def test_fails_when_dependency_failed(self):
        from solution import TaskResult
        prior = TaskResult(task_id="task-1", success=False, output="", error="API error")
        task = {"id": "task-2", "description": "Use prior result", "depends_on": ["task-1"]}
        result = self._run_execute_task(task, {"task-1": prior})
        self.assertFalse(result.success)


class TestExecutePlan(unittest.TestCase):
    def test_returns_list(self):
        from solution import execute_plan
        mock_client = _make_mock_client("output")
        with patch("solution.get_anthropic_client", return_value=mock_client):
            results = execute_plan(SAMPLE_PLAN)
        self.assertIsInstance(results, list)

    def test_returns_one_result_per_task(self):
        from solution import execute_plan
        mock_client = _make_mock_client("output")
        with patch("solution.get_anthropic_client", return_value=mock_client):
            results = execute_plan(SAMPLE_PLAN)
        self.assertEqual(len(results), len(SAMPLE_PLAN))

    def test_all_results_are_task_result_instances(self):
        from solution import execute_plan, TaskResult
        mock_client = _make_mock_client("output")
        with patch("solution.get_anthropic_client", return_value=mock_client):
            results = execute_plan(SAMPLE_PLAN)
        for r in results:
            self.assertIsInstance(r, TaskResult)

    def test_task_ids_match_plan(self):
        from solution import execute_plan
        mock_client = _make_mock_client("output")
        with patch("solution.get_anthropic_client", return_value=mock_client):
            results = execute_plan(SAMPLE_PLAN)
        result_ids = {r.task_id for r in results}
        plan_ids = {t["id"] for t in SAMPLE_PLAN}
        self.assertEqual(result_ids, plan_ids)
