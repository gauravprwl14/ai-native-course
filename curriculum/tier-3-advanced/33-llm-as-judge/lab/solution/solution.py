"""Lab 33: LLM-as-Judge — Reference Solution"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

DEFAULT_RUBRIC = {
    "helpfulness": "How helpful is the response? (1=not helpful, 5=extremely helpful)",
    "accuracy": "How factually accurate? (1=many errors, 5=fully accurate)",
    "clarity": "How clear and well-organized? (1=confusing, 5=very clear)",
}

SCORE_PROMPT = """You are an expert evaluator. Score the following response on each rubric dimension.
Return ONLY a JSON object with integer scores 1-5. No explanation, no markdown.

Rubric:
{rubric}

Prompt: {prompt}
Response: {response}

JSON scores:"""

PAIRWISE_PROMPT = """You are an expert evaluator comparing two responses to the same prompt.
Decide which response is better overall.
Return ONLY one of: "A", "B", or "tie". No explanation.

Prompt: {prompt}

Response A:
{response_a}

Response B:
{response_b}

Your verdict (A / B / tie):"""


def score_response(prompt: str, response: str, rubric: dict = None) -> dict:
    """Score response on each rubric dimension. Returns {dimension: int}."""
    if rubric is None:
        rubric = DEFAULT_RUBRIC

    rubric_text = "\n".join(f"- {k}: {v}" for k, v in rubric.items())
    formatted = SCORE_PROMPT.format(
        rubric=rubric_text,
        prompt=prompt,
        response=response,
    )

    client = get_anthropic_client()
    api_response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        temperature=0,
        messages=[{"role": "user", "content": formatted}]
    )
    raw = api_response.content[0].text.strip()
    return json.loads(raw)


def pairwise_judge(prompt: str, response_a: str, response_b: str) -> str:
    """Compare two responses. Returns "A", "B", or "tie".
    Runs the judge twice (swapping order) to mitigate position bias.
    """
    client = get_anthropic_client()

    def _judge(ra: str, rb: str) -> str:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": PAIRWISE_PROMPT.format(
                prompt=prompt, response_a=ra, response_b=rb
            )}]
        )
        verdict = resp.content[0].text.strip().upper()
        if verdict not in ("A", "B", "TIE"):
            return "TIE"
        return verdict

    # Run 1: A first
    verdict_1 = _judge(response_a, response_b)

    # Run 2: B first — invert labels after
    verdict_2_raw = _judge(response_b, response_a)
    if verdict_2_raw == "A":
        verdict_2 = "B"
    elif verdict_2_raw == "B":
        verdict_2 = "A"
    else:
        verdict_2 = "TIE"

    # Agree → return winner; disagree → tie
    if verdict_1 == verdict_2:
        return verdict_1.lower() if verdict_1 == "TIE" else verdict_1
    return "tie"


def run_judge_eval(dataset: list[dict]) -> dict:
    """Run judge on dataset. Each item: {"prompt": str, "response": str}.
    Returns {"avg_scores": dict, "results": list}
    """
    results = []
    for item in dataset:
        scores = score_response(item["prompt"], item["response"])
        results.append({
            "prompt": item["prompt"],
            "response": item["response"],
            "scores": scores,
        })

    # Compute average per dimension
    dimensions = list(DEFAULT_RUBRIC.keys())
    avg_scores = {}
    for dim in dimensions:
        dim_scores = [r["scores"].get(dim, 0) for r in results if dim in r["scores"]]
        avg_scores[dim] = sum(dim_scores) / len(dim_scores) if dim_scores else 0.0

    return {
        "avg_scores": avg_scores,
        "results": results,
    }


if __name__ == "__main__":
    print("=== Rubric Score ===")
    scores = score_response(
        prompt="Explain what gradient descent is.",
        response="Gradient descent minimizes a loss function by iteratively moving in the direction of steepest descent as defined by the negative gradient.",
    )
    print(scores)

    print("\n=== Pairwise Judge ===")
    winner = pairwise_judge(
        prompt="What is the capital of France?",
        response_a="Paris is the capital of France.",
        response_b="France is a country in Europe with a capital city.",
    )
    print(f"Winner: {winner}")

    print("\n=== Run Judge Eval ===")
    dataset = [
        {"prompt": "What is ML?", "response": "Machine learning is a subset of AI that learns from data."},
        {"prompt": "What is Python?", "response": "Python is a high-level programming language."},
    ]
    report = run_judge_eval(dataset)
    print(f"Avg scores: {report['avg_scores']}")
