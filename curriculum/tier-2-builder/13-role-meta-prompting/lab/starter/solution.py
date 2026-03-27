"""Lab 13: Role + Meta Prompting"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

META_PROMPT_TEMPLATE = """You are a prompt engineering expert. Generate {n} diverse, high-quality prompt variants for the following task.

Task description: {task_description}

Requirements for each variant:
- Each prompt should approach the task differently (different role, framing, or structure)
- Each should be specific and actionable
- Number them 1 through {n}
- Separate each prompt with "---"

Generate {n} prompt variants now:"""


def apply_role_prompt(task: str, role_description: str) -> str:
    """
    Apply a role to a task and get the response.
    Returns the model's response.

    # TODO:
    # Build system prompt: "You are {role_description}."
    # Call API with temperature=0.3, system=role_description_prompt, user message=task
    # Return response text
    """
    raise NotImplementedError("Implement apply_role_prompt")


def generate_prompt_variants(task_description: str, n: int = 5) -> list[str]:
    """
    Use meta-prompting to generate n prompt variants for a task.
    Returns list of n prompt strings.

    # TODO:
    # Format META_PROMPT_TEMPLATE with n and task_description
    # Call API with temperature=0.8 (want diversity)
    # Split response by "---" to get individual variants
    # Clean up each variant (strip whitespace, remove numbering)
    # Return list of n prompts (truncate or pad if needed)
    """
    raise NotImplementedError("Implement generate_prompt_variants")


def evaluate_prompt(prompt: str, test_cases: list[dict]) -> float:
    """
    Evaluate a prompt on test cases using LLM-as-judge.
    Each test case: {"input": str, "expected_keywords": list[str]}
    Returns fraction of test cases where all expected_keywords appear in response.

    # TODO:
    # For each test case:
    #   Format: full_prompt = prompt + "\n\n" + test_case["input"]
    #   Call API, get response
    #   Check if ALL expected_keywords appear in response (case-insensitive)
    # Return count_passed / len(test_cases)
    """
    raise NotImplementedError("Implement evaluate_prompt")


if __name__ == "__main__":
    print("=== Testing apply_role_prompt ===")
    response = apply_role_prompt(
        task="What are the top 3 things to check when reviewing Python code?",
        role_description="a senior Python engineer with 10 years of experience reviewing production code"
    )
    print(response)

    print("\n=== Testing generate_prompt_variants ===")
    variants = generate_prompt_variants("Explain list comprehensions in Python", n=3)
    for i, v in enumerate(variants, 1):
        print(f"\nVariant {i}:")
        print(v[:200] + "..." if len(v) > 200 else v)

    print("\n=== Testing evaluate_prompt ===")
    test_cases = [
        {"input": "What is a for loop?", "expected_keywords": ["iteration", "repeat"]},
        {"input": "What is a variable?", "expected_keywords": ["store", "value"]},
    ]
    score = evaluate_prompt(
        prompt="You are a Python tutor explaining concepts to beginners.",
        test_cases=test_cases
    )
    print(f"Evaluation score: {score:.2f}")
