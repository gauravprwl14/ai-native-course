"""Lab 10: Chain-of-Thought Prompting — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import re
from collections import Counter
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

COT_PROMPT = """Solve this math word problem. Think step by step, showing all your work.
End your response with "Therefore, the answer is: [number]"

Problem: {problem}"""


def solve_with_cot(problem: str) -> str:
    """
    Solve a math word problem using zero-shot chain-of-thought.
    Returns the full model response including reasoning.
    """
    client = get_anthropic_client()
    prompt = COT_PROMPT.format(problem=problem)

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def extract_answer(response: str) -> str | None:
    """
    Extract the final numerical answer from a CoT response.
    Looks for "Therefore, the answer is: X" pattern.
    Returns the number as a string, or None if not found.
    """
    match = re.search(
        r"Therefore, the answer is:\s*(\d+(?:\.\d+)?)",
        response,
        re.IGNORECASE
    )
    if match:
        return match.group(1)
    return None


def solve_with_self_consistency(problem: str, n: int = 5) -> str | None:
    """
    Solve using self-consistency: generate n responses and take majority vote.
    Returns the most common extracted answer, or None if no answers found.
    """
    client = get_anthropic_client()
    prompt = COT_PROMPT.format(problem=problem)
    answers = []

    for _ in range(n):
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = extract_answer(response.content[0].text)
        if answer is not None:
            answers.append(answer)

    if not answers:
        return None

    counter = Counter(answers)
    most_common_answer, _ = counter.most_common(1)[0]
    return most_common_answer


def evaluate_math_accuracy(predictions: list[str | None], answers: list[str]) -> float:
    """
    Compare predicted answers to correct answers.
    None predictions count as wrong.
    Returns fraction correct (0.0–1.0).
    """
    if not answers:
        return 0.0

    correct = sum(
        1 for pred, ans in zip(predictions, answers)
        if pred is not None and pred == ans
    )
    return correct / len(answers)


if __name__ == "__main__":
    problems = [
        "A bookshelf has 5 shelves. Each shelf holds 12 books. "
        "If 18 books are removed, how many books remain?",
        "A farmer has 3 fields. Two fields have 45 apple trees each "
        "and one field has 30 apple trees. How many apple trees in total?",
    ]

    print("=" * 60)
    print("Chain-of-Thought Math Solver — Reference Solution")
    print("=" * 60)

    for problem in problems:
        print(f"\nProblem: {problem}")
        print("-" * 40)

        response = solve_with_cot(problem)
        answer = extract_answer(response)
        print(f"CoT Response:\n{response}")
        print(f"Extracted Answer: {answer}")
