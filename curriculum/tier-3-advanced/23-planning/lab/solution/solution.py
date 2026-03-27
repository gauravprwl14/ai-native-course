"""Lab 23: Planning & Task Decomposition — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import json
from dataclasses import dataclass
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
    """
    client = get_anthropic_client()
    prompt = PLANNING_PROMPT.format(goal=goal, context=context)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if LLM wraps response
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def execute_task(task: dict, available_results: dict[str, TaskResult]) -> TaskResult:
    """
    Execute a single task with context from its dependencies.
    Returns TaskResult.
    """
    # Check all dependencies are satisfied
    for dep_id in task.get("depends_on", []):
        if dep_id not in available_results or not available_results[dep_id].success:
            return TaskResult(
                task_id=task["id"],
                success=False,
                output="",
                error=f"Dependency {dep_id} not satisfied"
            )

    # Build context from completed dependencies
    context_parts = []
    for dep_id in task.get("depends_on", []):
        dep_result = available_results[dep_id]
        context_parts.append(f"{dep_id}: {dep_result.output[:300]}")
    context = "\n".join(context_parts)

    # Execute the task
    client = get_anthropic_client()
    prompt = f"Execute this task: {task['description']}"
    if context:
        prompt += f"\n\nContext from prior tasks:\n{context}"

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    return TaskResult(
        task_id=task["id"],
        success=True,
        output=response.content[0].text
    )


def execute_plan(plan: list[dict]) -> list[TaskResult]:
    """
    Execute all tasks in dependency order (sequential).
    Returns list of TaskResult for all tasks.
    """
    results: dict[str, TaskResult] = {}
    for task in plan:
        result = execute_task(task, results)
        results[task["id"]] = result
    return list(results.values())


if __name__ == "__main__":
    goal = "Summarise the history of Python programming language"
    print(f"Goal: {goal}\n")

    plan = generate_plan(goal)
    print("Generated plan:")
    for task in plan:
        print(f"  [{task['id']}] {task['description']} (depends: {task['depends_on']})")

    print("\nExecuting plan...")
    results = execute_plan(plan)
    for r in results:
        status = "OK" if r.success else "FAILED"
        print(f"\n[{r.task_id}] {status}")
        if r.success:
            print(r.output[:300])
        else:
            print(f"Error: {r.error}")
