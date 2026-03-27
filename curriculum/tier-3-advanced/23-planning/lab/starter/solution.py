"""Lab 23: Planning & Task Decomposition"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import json
from dataclasses import dataclass, field
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

PLANNING_PROMPT = """Break down the following goal into 3-7 concrete, executable sub-tasks.
Return ONLY a JSON array of objects with this schema:
[{{"id": "task-1", "description": "...", "depends_on": []}}]

Rules:
- Each "id" must be unique (task-1, task-2, ...)
- "depends_on" lists IDs of tasks that must complete before this one
- Tasks with empty depends_on can run first
- Return raw JSON only — no markdown, no explanation

Goal: {goal}
Context: {context}"""


@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: str
    error: str = None


def generate_plan(goal: str, context: str = "") -> list[dict]:
    """
    Use LLM to generate a plan (list of task dicts) for a goal.
    Returns list of {"id": str, "description": str, "depends_on": list} dicts.

    # TODO:
    # 1. Format PLANNING_PROMPT with goal and context
    # 2. Call the Anthropic API with temperature=0 and max_tokens=1024
    # 3. Parse the JSON response text and return the list
    """
    raise NotImplementedError("Implement generate_plan")


def execute_task(task: dict, available_results: dict[str, TaskResult]) -> TaskResult:
    """
    Execute a single task (stub implementation for lab).
    Returns TaskResult.

    # TODO:
    # 1. Check that all task["depends_on"] IDs are in available_results and succeeded.
    #    If not, return TaskResult(task_id=task["id"], success=False, output="",
    #                              error="Dependency {dep_id} not satisfied")
    # 2. Build a context string from the outputs of successful dependencies:
    #    context = "\n".join(f"{dep_id}: {available_results[dep_id].output[:300]}"
    #                        for dep_id in task["depends_on"])
    # 3. Call the LLM:
    #    prompt = f"Execute this task: {task['description']}\nContext from prior tasks:\n{context}"
    #    Use the Anthropic client with MODEL, max_tokens=512
    # 4. Return TaskResult(task_id=task["id"], success=True, output=response_text)
    """
    raise NotImplementedError("Implement execute_task")


def execute_plan(plan: list[dict]) -> list[TaskResult]:
    """
    Execute all tasks in dependency order (sequential for this lab).
    Returns list of TaskResult for all tasks.

    # TODO:
    # 1. results = {}  (dict mapping task_id -> TaskResult)
    # 2. For each task in plan (in order):
    #    a. Call execute_task(task, results)
    #    b. Store result in results[task["id"]]
    # 3. Return list(results.values())
    """
    raise NotImplementedError("Implement execute_plan")
