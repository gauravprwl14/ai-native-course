# Lab 48 — Durable Workflow Engine

## Goal

Build a minimal durable workflow engine that checkpoints state to disk as JSON after every step and can resume from the last completed step after a crash.

## Background

Long-running AI workflows (research pipelines, multi-step document processing) can take minutes or hours. Without durability, a crash forces a full restart — wasting time and API credits. A durable workflow engine solves this by:

1. Saving workflow state (completed steps + outputs) to disk after every step
2. On restart, loading the checkpoint and skipping already-completed steps
3. Continuing from the first incomplete step

## What to Implement

### `StepResult` (dataclass)

Fields: `step_name: str`, `status: str`, `output: Any = None`, `error: Optional[str] = None`

Status values: `"completed"`, `"failed"`, `"skipped"`

### `WorkflowCheckpoint` (dataclass)

Fields:
- `workflow_id: str`
- `completed_steps: list[str]` (default: empty list)
- `step_outputs: dict[str, Any]` (default: empty dict)
- `status: str` (default: `"running"`)

### `DurableWorkflow` class

```
__init__(workflow_id, checkpoint_dir="/tmp/workflows")
    Sets self.workflow_id, self.checkpoint_path, and initialises self.checkpoint

load_checkpoint() -> bool
    Load checkpoint from disk. Return True if found, False if not.

save_checkpoint() -> None
    Serialize self.checkpoint as JSON and write to self.checkpoint_path

is_step_completed(step_name) -> bool
    Return True if step_name is in self.checkpoint.completed_steps

mark_step_completed(step_name, output=None) -> None
    Add step_name to completed_steps, store output, save checkpoint

run_step(step_name, func, *args, **kwargs) -> StepResult
    If already completed: return StepResult with status="skipped"
    Try func(*args, **kwargs):
        success: mark_step_completed, return StepResult(status="completed")
        failure: return StepResult(status="failed", error=str(e))

run(steps) -> list[StepResult]
    steps: list of (name, func, args, kwargs)
    Load checkpoint, run each step, stop on first failure
    On all steps complete, set checkpoint.status="completed" and save
```

## Test

```bash
cd curriculum/tier-4-architect/48-durable-workflows/lab
pytest tests/ -v
```

## Expected behaviour

```
=== First run ===
[RUN]  fetch_data         # executes
[RUN]  process_data       # executes
[RUN]  generate_report    # fails (simulated)

=== Resume ===
[SKIP] fetch_data         # checkpoint loaded, step already done
[SKIP] process_data       # checkpoint loaded, step already done
[RUN]  generate_report    # re-executes from here
[RUN]  publish_report     # executes
Completed!
```
