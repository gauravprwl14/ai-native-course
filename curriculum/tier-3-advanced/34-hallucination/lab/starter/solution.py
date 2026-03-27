"""Lab 34: Hallucination Detection"""
import sys
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


def check_faithfulness(answer: str, context: str) -> float:
    """Returns faithfulness score 0-1.
    # TODO: call API with FAITHFULNESS_PROMPT, parse JSON response, return score as float.
    # Fallback to 0.5 if JSON parsing fails.
    """
    raise NotImplementedError()


def detect_contradictions(answer: str, context: str) -> list[str]:
    """Returns list of sentences in answer that may contradict context.
    # TODO: build a prompt asking LLM to identify contradicting/unsupported sentences.
    # Parse the JSON list from the response. Return [] if no contradictions.
    """
    raise NotImplementedError()


def verify_rag_answer(question: str, answer: str, retrieved_chunks: list[str]) -> dict:
    """Verify full RAG answer against retrieved chunks.
    Returns {"faithful": bool, "score": float, "issues": list[str]}.
    # TODO: join retrieved_chunks with '\n\n' as context.
    # Call check_faithfulness and detect_contradictions.
    # Set faithful = True if score >= 0.8.
    """
    raise NotImplementedError()
