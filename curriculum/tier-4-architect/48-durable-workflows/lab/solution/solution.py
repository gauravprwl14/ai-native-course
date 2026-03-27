"""Lab 48: Durable Workflow Engine — Reference Solution"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class StepResult:
    step_name: str
    status: str  # "completed", "failed", "skipped"
    output: Any = None
    error: Optional[str] = None


@dataclass
class WorkflowCheckpoint:
    workflow_id: str
    completed_steps: list = field(default_factory=list)
    step_outputs: dict = field(default_factory=dict)
    status: str = "running"  # running, completed, failed


class DurableWorkflow:
    def __init__(self, workflow_id: str, checkpoint_dir: str = "/tmp/workflows"):
        self.workflow_id = workflow_id
        self.checkpoint_path = Path(checkpoint_dir) / f"{workflow_id}.json"
        self.checkpoint: WorkflowCheckpoint = WorkflowCheckpoint(
            workflow_id=workflow_id
        )

    def load_checkpoint(self) -> bool:
        """Load checkpoint from disk. Returns True if checkpoint exists."""
        if not self.checkpoint_path.exists():
            return False
        data = json.loads(self.checkpoint_path.read_text())
        self.checkpoint = WorkflowCheckpoint(**data)
        return True

    def save_checkpoint(self) -> None:
        """Save current checkpoint to disk as JSON."""
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.write_text(json.dumps(asdict(self.checkpoint), indent=2))

    def is_step_completed(self, step_name: str) -> bool:
        """Return True if step_name is in completed_steps."""
        return step_name in self.checkpoint.completed_steps

    def mark_step_completed(self, step_name: str, output: Any = None) -> None:
        """Mark a step as completed and save checkpoint."""
        self.checkpoint.completed_steps.append(step_name)
        self.checkpoint.step_outputs[step_name] = output
        self.save_checkpoint()

    def run_step(
        self, step_name: str, func: Callable, *args, **kwargs
    ) -> StepResult:
        """Run a single step, skipping it if already completed."""
        if self.is_step_completed(step_name):
            stored_output = self.checkpoint.step_outputs.get(step_name)
            return StepResult(step_name, "skipped", output=stored_output)

        try:
            output = func(*args, **kwargs)
            self.mark_step_completed(step_name, output)
            return StepResult(step_name, "completed", output=output)
        except Exception as e:
            return StepResult(step_name, "failed", error=str(e))

    def run(
        self, steps: list[tuple[str, Callable, list, dict]]
    ) -> list[StepResult]:
        """Run all steps in order, resuming from checkpoint."""
        self.load_checkpoint()
        results: list[StepResult] = []

        for name, func, args, kwargs in steps:
            result = self.run_step(name, func, *args, **kwargs)
            results.append(result)
            if result.status == "failed":
                self.checkpoint.status = "failed"
                self.save_checkpoint()
                break

        if all(r.status in ("completed", "skipped") for r in results) and len(results) == len(steps):
            self.checkpoint.status = "completed"
            self.save_checkpoint()

        return results


# ── Demo: crash and resume ──────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    checkpoint_dir = tempfile.mkdtemp()
    workflow_id = "demo-workflow"

    # Simulate a step that fails on the first call but succeeds on the second
    call_count: dict[str, int] = {}

    def fetch_data() -> list[str]:
        return ["source_1", "source_2", "source_3"]

    def process_data() -> dict:
        return {"processed": True, "count": 3}

    def generate_report() -> str:
        call_count["generate_report"] = call_count.get("generate_report", 0) + 1
        if call_count["generate_report"] == 1:
            raise RuntimeError("Simulated crash in generate_report")
        return "Final report: 3 sources processed"

    def publish_report() -> str:
        return "Published at /reports/demo"

    steps = [
        ("fetch_data", fetch_data, [], {}),
        ("process_data", process_data, [], {}),
        ("generate_report", generate_report, [], {}),
        ("publish_report", publish_report, [], {}),
    ]

    print("=== First run (will fail at generate_report) ===")
    wf1 = DurableWorkflow(workflow_id, checkpoint_dir)
    results1 = wf1.run(steps)
    for r in results1:
        icon = {"completed": "[OK]  ", "failed": "[FAIL]", "skipped": "[SKIP]"}[r.status]
        print(f"  {icon} {r.step_name}" + (f" — {r.error}" if r.error else ""))

    print()
    print("=== Second run (resume from generate_report) ===")
    wf2 = DurableWorkflow(workflow_id, checkpoint_dir)
    results2 = wf2.run(steps)
    for r in results2:
        icon = {"completed": "[OK]  ", "failed": "[FAIL]", "skipped": "[SKIP]"}[r.status]
        print(f"  {icon} {r.step_name}")

    print()
    print(f"Final workflow status: {wf2.checkpoint.status}")
