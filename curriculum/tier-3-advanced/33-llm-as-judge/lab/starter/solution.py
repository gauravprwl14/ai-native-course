"""Lab 33: LLM-as-Judge"""
import sys
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
    """Score response on each rubric dimension. Returns {dimension: int}
    # TODO:
    # 1. Use DEFAULT_RUBRIC if rubric is None
    # 2. Format rubric as "- key: description" lines
    # 3. Format SCORE_PROMPT with rubric, prompt, response
    # 4. Call get_anthropic_client().messages.create with:
    #    - model=MODEL, max_tokens=256, temperature=0
    #    - messages=[{"role": "user", "content": formatted_prompt}]
    # 5. Parse response.content[0].text.strip() as JSON and return the dict
    """
    raise NotImplementedError("Implement score_response")


def pairwise_judge(prompt: str, response_a: str, response_b: str) -> str:
    """Compare two responses. Returns "A", "B", or "tie".
    # TODO:
    # 1. Write a helper _judge(ra, rb) -> str that calls the API once with
    #    PAIRWISE_PROMPT and returns "A", "B", or "tie" (uppercase, stripped)
    # 2. verdict_1 = _judge(response_a, response_b)  [A first]
    # 3. verdict_2_raw = _judge(response_b, response_a)  [B first — labels swapped]
    # 4. Invert verdict_2_raw labels:
    #    "A" -> "B", "B" -> "A", "TIE" -> "tie"
    # 5. If verdict_1 == verdict_2 (after inversion): return that value
    #    Else: return "tie"
    """
    raise NotImplementedError("Implement pairwise_judge")


def run_judge_eval(dataset: list[dict]) -> dict:
    """Run judge on dataset. Each item: {"prompt": str, "response": str}.
    Returns {"avg_scores": dict, "results": list}
    # TODO:
    # 1. For each item in dataset:
    #    a. Call score_response(item["prompt"], item["response"]) — use default rubric
    #    b. Append {"prompt": ..., "response": ..., "scores": ...} to results
    # 2. Compute avg_scores: for each dimension in DEFAULT_RUBRIC,
    #    avg = mean of that dimension across all results
    # 3. Return {"avg_scores": avg_scores, "results": results}
    """
    raise NotImplementedError("Implement run_judge_eval")
