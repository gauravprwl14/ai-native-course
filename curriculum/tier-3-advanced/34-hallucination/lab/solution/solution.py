"""Lab 34: Hallucination Detection — Reference Solution"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

FAITHFULNESS_PROMPT = """Given a context and an answer, rate how faithful the answer is to the context.
Return a JSON: {{"score": float 0-1, "reason": "brief explanation"}}
A score of 1.0 means every claim in the answer is supported by the context.
A score of 0.0 means the answer directly contradicts or invents information not in the context.

Context: {context}
Answer: {answer}"""

CONTRADICTION_PROMPT = """You are a fact-checker. Given a context and an answer, identify every sentence in the answer that:
1. Directly contradicts something stated in the context, OR
2. States a fact that is not mentioned anywhere in the context

Return a JSON list of suspicious sentences. Return an empty list [] if everything is supported.

Context: {context}
Answer: {answer}"""


def check_faithfulness(answer: str, context: str) -> float:
    """Returns faithfulness score 0-1."""
    client = get_anthropic_client()
    prompt = FAITHFULNESS_PROMPT.format(context=context, answer=answer)
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    try:
        # Find and parse JSON object from response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1:
            return 0.5
        data = json.loads(text[start:end])
        return float(data["score"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return 0.5


def detect_contradictions(answer: str, context: str) -> list[str]:
    """Returns list of sentences in answer that may contradict context."""
    client = get_anthropic_client()
    prompt = CONTRADICTION_PROMPT.format(context=context, answer=answer)
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1:
            return []
        return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError):
        return []


def verify_rag_answer(question: str, answer: str, retrieved_chunks: list[str]) -> dict:
    """Verify full RAG answer. Returns {"faithful": bool, "score": float, "issues": list[str]}."""
    context = "\n\n".join(retrieved_chunks)
    score = check_faithfulness(answer, context)
    issues = detect_contradictions(answer, context)
    return {
        "faithful": score >= 0.8,
        "score": score,
        "issues": issues,
    }
