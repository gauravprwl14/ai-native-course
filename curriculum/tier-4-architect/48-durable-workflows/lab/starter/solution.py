"""Lab 48: Durable Workflow Engine — Starter File

Implement a workflow engine that:
1. Checkpoints state to disk as JSON after every step
2. Resumes from the last checkpoint on restart
3. Skips already-completed steps
"""

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
        """Load checkpoint from disk. Returns True if checkpoint exists.

        Steps:
        1. Check if self.checkpoint_path exists
        2. If it exists, read the file and parse JSON
        3. Reconstruct a WorkflowCheckpoint from the parsed dict
        4. Return True if loaded, False if no checkpoint found
        """
        # TODO: Check if self.checkpoint_path exists
        # TODO: If exists, read JSON and reconstruct WorkflowCheckpoint
        #       Hint: WorkflowCheckpoint(**data) where data is the parsed dict
        # TODO: Return True if loaded, False if no checkpoint
        pass

    def save_checkpoint(self) -> None:
        """Save current checkpoint to disk as JSON.

        Steps:
        1. Create parent directory if it does not exist (parents=True, exist_ok=True)
        2. Convert self.checkpoint to a dict using dataclasses.asdict
        3. Write the JSON string to self.checkpoint_path
        """
        # TODO: Create parent directory if needed
        # TODO: Write self.checkpoint as JSON to self.checkpoint_path
        pass

    def is_step_completed(self, step_name: str) -> bool:
        """Return True if step_name is in completed_steps.

        Steps:
        1. Return True if step_name in self.checkpoint.completed_steps
        """
        # TODO: Return True if step_name in self.checkpoint.completed_steps
        pass

    def mark_step_completed(self, step_name: str, output: Any = None) -> None:
        """Mark a step as completed and save checkpoint.

        Steps:
        1. Append step_name to self.checkpoint.completed_steps
        2. Store output in self.checkpoint.step_outputs[step_name]
        3. Call self.save_checkpoint()
        """
        # TODO: Append step_name to completed_steps
        # TODO: Store output in step_outputs[step_name]
        # TODO: Call save_checkpoint()
        pass

    def run_step(
        self, step_name: str, func: Callable, *args, **kwargs
    ) -> StepResult:
        """Run a single step, skipping it if already completed.

        Steps:
        1. If is_step_completed(step_name):
               return StepResult(step_name, "skipped",
                                 output=self.checkpoint.step_outputs[step_name])
        2. Try calling func(*args, **kwargs)
        3. On success: call mark_step_completed(step_name, output)
                       return StepResult(step_name, "completed", output=output)
        4. On exception: return StepResult(step_name, "failed", error=str(e))
           Do NOT raise the exception — let the caller decide what to do
        """
        # TODO: Check if already completed and return skipped result
        # TODO: Try executing func(*args, **kwargs)
        # TODO: On success: mark as completed and return completed result
        # TODO: On exception: return failed result with error message
        pass

    def run(
        self, steps: list[tuple[str, Callable, list, dict]]
    ) -> list[StepResult]:
        """Run all steps in order, resuming from checkpoint.

        Args:
            steps: list of (step_name, func, args, kwargs)

        Returns:
            list of StepResult for all steps attempted

        Steps:
        1. Call load_checkpoint() to pick up any existing state
        2. For each (name, func, args, kwargs) in steps:
               result = run_step(name, func, *args, **kwargs)
               append result to results
               if result.status == "failed": stop and return results so far
        3. When all steps complete:
               set self.checkpoint.status = "completed"
               call save_checkpoint()
        4. Return all results
        """
        # TODO: Load checkpoint
        # TODO: Run each step; stop on first failure
        # TODO: Set status to "completed" and save when all steps done
        # TODO: Return results
        pass
