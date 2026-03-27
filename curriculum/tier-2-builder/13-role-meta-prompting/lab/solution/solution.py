"""Lab 13: Role + Meta Prompting (SOLUTION)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import re
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
    """Apply a role to a task and get the response."""
    client = get_anthropic_client()
    system_prompt = f"You are {role_description}."

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": task}],
    )
    return response.content[0].text


def generate_prompt_variants(task_description: str, n: int = 5) -> list[str]:
    """Use meta-prompting to generate n diverse prompt variants for a task."""
    client = get_anthropic_client()
    meta_prompt = META_PROMPT_TEMPLATE.format(n=n, task_description=task_description)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        temperature=0.8,
        messages=[{"role": "user", "content": meta_prompt}],
    )
    raw = response.content[0].text

    # Split on separator and clean up
    raw_variants = [v.strip() for v in raw.split("---") if v.strip()]

    # Remove leading numbering like "1." or "1)" from the start of each variant
    cleaned = []
    for variant in raw_variants:
        # Strip leading "1." / "1)" / "1 -" style numbering
        cleaned_variant = re.sub(r"^\d+[\.\)]\s*", "", variant).strip()
        cleaned.append(cleaned_variant)

    # Truncate to n if the model produced more; pad with empty string if fewer
    result = cleaned[:n]
    while len(result) < n:
        result.append("")

    return result


def evaluate_prompt(prompt: str, test_cases: list[dict]) -> float:
    """
    Evaluate a prompt on test cases using keyword matching.
    Returns fraction of test cases where all expected_keywords appear in response.
    """
    client = get_anthropic_client()
    count_passed = 0

    for test_case in test_cases:
        full_prompt = prompt + "\n\n" + test_case["input"]
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            temperature=0,
            messages=[{"role": "user", "content": full_prompt}],
        )
        response_text = response.content[0].text.lower()

        all_present = all(
            keyword.lower() in response_text
            for keyword in test_case["expected_keywords"]
        )
        if all_present:
            count_passed += 1

    return count_passed / len(test_cases)


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
