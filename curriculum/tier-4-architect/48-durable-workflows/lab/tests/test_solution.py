"""Tests for Lab 48 — Durable Workflow Engine"""

import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Run tests against the starter by default; LAB_TARGET=solution for reference
import os
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


def _make_workflow(suffix="test"):
    """Create a DurableWorkflow with a temporary checkpoint directory."""
    from solution import DurableWorkflow
    tmpdir = tempfile.mkdtemp()
    return DurableWorkflow(workflow_id=f"wf-{suffix}", checkpoint_dir=tmpdir), tmpdir


class TestWorkflowCheckpoint(unittest.TestCase):
    def test_checkpoint_dataclass_exists(self):
        from solution import WorkflowCheckpoint
        cp = WorkflowCheckpoint(workflow_id="test")
        self.assertEqual(cp.workflow_id, "test")

    def test_checkpoint_defaults(self):
        from solution import WorkflowCheckpoint
        cp = WorkflowCheckpoint(workflow_id="test")
        self.assertEqual(cp.completed_steps, [])
        self.assertEqual(cp.step_outputs, {})
        self.assertEqual(cp.status, "running")

    def test_step_result_dataclass_exists(self):
        from solution import StepResult
        r = StepResult(step_name="s1", status="completed", output=42)
        self.assertEqual(r.step_name, "s1")
        self.assertEqual(r.status, "completed")
        self.assertEqual(r.output, 42)

    def test_step_result_default_output_none(self):
        from solution import StepResult
        r = StepResult(step_name="s1", status="failed", error="oops")
        self.assertIsNone(r.output)
        self.assertEqual(r.error, "oops")


class TestSaveAndLoadCheckpoint(unittest.TestCase):
    def test_load_returns_false_when_no_file(self):
        wf, _ = _make_workflow("no-file")
        result = wf.load_checkpoint()
        self.assertFalse(result)

    def test_save_creates_file(self):
        wf, tmpdir = _make_workflow("save-creates")
        wf.save_checkpoint()
        self.assertTrue(wf.checkpoint_path.exists())

    def test_save_writes_valid_json(self):
        wf, _ = _make_workflow("valid-json")
        wf.save_checkpoint()
        data = json.loads(wf.checkpoint_path.read_text())
        self.assertIn("workflow_id", data)
        self.assertIn("completed_steps", data)

    def test_load_returns_true_after_save(self):
        wf, _ = _make_workflow("round-trip")
        wf.save_checkpoint()
        wf2_cls = type(wf)
        wf2 = wf2_cls.__new__(wf2_cls)
        wf2.workflow_id = wf.workflow_id
        wf2.checkpoint_path = wf.checkpoint_path
        from solution import WorkflowCheckpoint
        wf2.checkpoint = WorkflowCheckpoint(workflow_id=wf.workflow_id)
        result = wf2.load_checkpoint()
        self.assertTrue(result)

    def test_load_restores_completed_steps(self):
        wf, _ = _make_workflow("restore-steps")
        wf.checkpoint.completed_steps = ["step_a", "step_b"]
        wf.checkpoint.step_outputs = {"step_a": "out_a", "step_b": "out_b"}
        wf.save_checkpoint()

        from solution import DurableWorkflow
        wf2 = DurableWorkflow(wf.workflow_id, str(wf.checkpoint_path.parent))
        wf2.load_checkpoint()
        self.assertIn("step_a", wf2.checkpoint.completed_steps)
        self.assertIn("step_b", wf2.checkpoint.completed_steps)

    def test_load_restores_step_outputs(self):
        wf, _ = _make_workflow("restore-outputs")
        wf.checkpoint.step_outputs = {"step_x": {"key": "value"}}
        wf.checkpoint.completed_steps = ["step_x"]
        wf.save_checkpoint()

        from solution import DurableWorkflow
        wf2 = DurableWorkflow(wf.workflow_id, str(wf.checkpoint_path.parent))
        wf2.load_checkpoint()
        self.assertEqual(wf2.checkpoint.step_outputs.get("step_x"), {"key": "value"})


class TestIsStepCompleted(unittest.TestCase):
    def test_returns_false_for_unknown_step(self):
        wf, _ = _make_workflow("is-completed-false")
        self.assertFalse(wf.is_step_completed("step_a"))

    def test_returns_true_after_mark_completed(self):
        wf, _ = _make_workflow("is-completed-true")
        wf.checkpoint.completed_steps.append("step_a")
        self.assertTrue(wf.is_step_completed("step_a"))


class TestMarkStepCompleted(unittest.TestCase):
    def test_adds_step_to_completed_steps(self):
        wf, _ = _make_workflow("mark-adds")
        wf.mark_step_completed("step_a", output="result_a")
        self.assertIn("step_a", wf.checkpoint.completed_steps)

    def test_stores_output_in_step_outputs(self):
        wf, _ = _make_workflow("mark-output")
        wf.mark_step_completed("step_b", output={"data": 42})
        self.assertEqual(wf.checkpoint.step_outputs.get("step_b"), {"data": 42})

    def test_saves_checkpoint_after_mark(self):
        wf, _ = _make_workflow("mark-saves")
        wf.mark_step_completed("step_c", output="c_result")
        self.assertTrue(wf.checkpoint_path.exists())


class TestRunStep(unittest.TestCase):
    def test_run_step_executes_function(self):
        wf, _ = _make_workflow("run-executes")
        mock_fn = MagicMock(return_value="output_value")
        result = wf.run_step("step_a", mock_fn)
        mock_fn.assert_called_once()
        self.assertEqual(result.status, "completed")

    def test_run_step_returns_output(self):
        wf, _ = _make_workflow("run-output")
        result = wf.run_step("step_a", lambda: "hello")
        self.assertEqual(result.output, "hello")

    def test_run_step_marks_completed(self):
        wf, _ = _make_workflow("run-marks")
        wf.run_step("step_a", lambda: "done")
        self.assertIn("step_a", wf.checkpoint.completed_steps)

    def test_run_step_skips_completed_step(self):
        wf, _ = _make_workflow("run-skips")
        wf.checkpoint.completed_steps.append("step_a")
        wf.checkpoint.step_outputs["step_a"] = "cached_output"
        mock_fn = MagicMock(return_value="new_output")
        result = wf.run_step("step_a", mock_fn)
        mock_fn.assert_not_called()
        self.assertEqual(result.status, "skipped")

    def test_run_step_skipped_returns_stored_output(self):
        wf, _ = _make_workflow("run-skip-output")
        wf.checkpoint.completed_steps.append("step_b")
        wf.checkpoint.step_outputs["step_b"] = "stored_value"
        result = wf.run_step("step_b", lambda: "new")
        self.assertEqual(result.output, "stored_value")

    def test_run_step_returns_failed_on_exception(self):
        wf, _ = _make_workflow("run-fail")
        def bad_func():
            raise ValueError("something broke")
        result = wf.run_step("step_fail", bad_func)
        self.assertEqual(result.status, "failed")
        self.assertIn("something broke", result.error)

    def test_run_step_failed_does_not_mark_completed(self):
        wf, _ = _make_workflow("run-fail-no-mark")
        def bad_func():
            raise RuntimeError("crash")
        wf.run_step("step_bad", bad_func)
        self.assertNotIn("step_bad", wf.checkpoint.completed_steps)

    def test_run_step_passes_args_to_function(self):
        wf, _ = _make_workflow("run-args")
        received = {}
        def capture_fn(a, b, key="default"):
            received.update({"a": a, "b": b, "key": key})
            return "ok"
        wf.run_step("step_args", capture_fn, 10, 20, key="custom")
        self.assertEqual(received, {"a": 10, "b": 20, "key": "custom"})


class TestRunWorkflow(unittest.TestCase):
    def _build_steps(self):
        def s1(): return "result_1"
        def s2(): return "result_2"
        def s3(): return "result_3"
        return [
            ("step_1", s1, [], {}),
            ("step_2", s2, [], {}),
            ("step_3", s3, [], {}),
        ]

    def test_run_returns_list(self):
        wf, _ = _make_workflow("run-list")
        results = wf.run(self._build_steps())
        self.assertIsInstance(results, list)

    def test_run_returns_result_per_step(self):
        wf, _ = _make_workflow("run-count")
        results = wf.run(self._build_steps())
        self.assertEqual(len(results), 3)

    def test_run_all_completed(self):
        wf, _ = _make_workflow("run-all-completed")
        results = wf.run(self._build_steps())
        for r in results:
            self.assertEqual(r.status, "completed")

    def test_run_sets_checkpoint_completed(self):
        wf, _ = _make_workflow("run-status-completed")
        wf.run(self._build_steps())
        self.assertEqual(wf.checkpoint.status, "completed")

    def test_run_stops_at_failed_step(self):
        wf, _ = _make_workflow("run-stops-fail")
        call_log = []
        def s1(): call_log.append("s1"); return "r1"
        def s2(): call_log.append("s2"); raise RuntimeError("fail")
        def s3(): call_log.append("s3"); return "r3"
        steps = [
            ("s1", s1, [], {}),
            ("s2", s2, [], {}),
            ("s3", s3, [], {}),
        ]
        results = wf.run(steps)
        self.assertNotIn("s3", call_log)
        self.assertEqual(len(results), 2)

    def test_run_skips_completed_steps_on_resume(self):
        wf, tmpdir = _make_workflow("run-resume")

        call_log = []
        def s1(): call_log.append("s1"); return "r1"
        def s2(): call_log.append("s2"); return "r2"

        steps = [("s1", s1, [], {}), ("s2", s2, [], {})]

        # First run completes everything
        wf.run(steps)
        call_log.clear()

        # Second run on new workflow instance with same checkpoint dir
        from solution import DurableWorkflow
        wf2 = DurableWorkflow("wf-run-resume", tmpdir)
        wf2.run(steps)

        # Neither step should have been called again
        self.assertEqual(call_log, [])

    def test_run_resumes_from_failed_step(self):
        wf, tmpdir = _make_workflow("run-resume-fail")

        attempt = {"n": 0}
        def s1(): return "r1"
        def s2():
            attempt["n"] += 1
            if attempt["n"] == 1:
                raise RuntimeError("first attempt fails")
            return "r2"

        steps = [("s1", s1, [], {}), ("s2", s2, [], {})]

        # First run: s1 completes, s2 fails
        wf.run(steps)
        self.assertIn("s1", wf.checkpoint.completed_steps)

        # Second run: s1 skipped, s2 retried
        from solution import DurableWorkflow
        wf2 = DurableWorkflow("wf-run-resume-fail", tmpdir)
        results = wf2.run(steps)
        statuses = {r.step_name: r.status for r in results}
        self.assertEqual(statuses["s1"], "skipped")
        self.assertEqual(statuses["s2"], "completed")


if __name__ == "__main__":
    unittest.main()
