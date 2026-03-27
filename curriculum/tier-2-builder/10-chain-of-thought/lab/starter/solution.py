"""Lab 10: Chain-of-Thought Prompting"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import re
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

COT_PROMPT = """Solve this math word problem. Think step by step, showing all your work.
End your response with "Therefore, the answer is: [number]"

Problem: {problem}"""


def solve_with_cot(problem: str) -> str:
    """
    Solve a math word problem using zero-shot chain-of-thought.
    Returns the full model response including reasoning.
    # TODO: Format COT_PROMPT with problem, call API with temperature=0, return full response text
    """
    raise NotImplementedError("Implement solve_with_cot")


def extract_answer(response: str) -> str | None:
    """
    Extract the final numerical answer from a CoT response.
    Looks for "Therefore, the answer is: X" pattern.
    Returns the number as a string, or None if not found.
    # TODO: Use re.search to find pattern r"Therefore, the answer is:\s*(\d+(?:\.\d+)?)"
    # Return match.group(1) if found, else None
    """
    raise NotImplementedError("Implement extract_answer")


def solve_with_self_consistency(problem: str, n: int = 5) -> str | None:
    """
    Solve using self-consistency: generate n responses and take majority vote.
    Returns the most common extracted answer, or None if no consensus.
    # TODO:
    # 1. Generate n responses using temperature=0.7
    # 2. Extract answer from each response
    # 3. Filter out None answers
    # 4. Return most common answer (use Counter from collections)
    """
    raise NotImplementedError("Implement solve_with_self_consistency")


def evaluate_math_accuracy(predictions: list[str | None], answers: list[str]) -> float:
    """
    Compare predicted answers to correct answers.
    None predictions count as wrong.
    Returns fraction correct (0.0–1.0).
    # TODO: count matches / len(answers)
    """
    raise NotImplementedError("Implement evaluate_math_accuracy")


if __name__ == "__main__":
    problems = [
        "A bookshelf has 5 shelves. Each shelf holds 12 books. "
        "If 18 books are removed, how many books remain?",
        "A farmer has 3 fields. Two fields have 45 apple trees each "
        "and one field has 30 apple trees. How many apple trees in total?",
    ]

    print("=" * 60)
    print("Chain-of-Thought Math Solver")
    print("=" * 60)

    for problem in problems:
        print(f"\nProblem: {problem}")
        print("-" * 40)

        # Single chain (zero-shot CoT)
        response = solve_with_cot(problem)
        answer = extract_answer(response)
        print(f"CoT Response:\n{response}")
        print(f"Extracted Answer: {answer}")
