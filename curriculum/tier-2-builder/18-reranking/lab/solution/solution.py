"""Lab 18: Re-ranking — Reference Solution"""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

RELEVANCE_PROMPT = """Rate the relevance of this document to the query on a scale of 1-10.
Respond with ONLY a single integer between 1 and 10.

Query: {query}
Document: {document}

Relevance score (1-10):"""


def score_chunk_relevance(query: str, chunk: str) -> int:
    """
    Use LLM to score how relevant a chunk is to the query (1-10).
    Returns an integer in the range [1, 10].
    """
    client = get_anthropic_client()
    prompt = RELEVANCE_PROMPT.format(query=query, document=chunk)

    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    try:
        score = int(text)
    except ValueError:
        score = 1

    return max(1, min(10, score))


def llm_rerank(query: str, chunks: list[str], top_k: int = 5) -> list[tuple[str, int]]:
    """
    Re-rank chunks by relevance using LLM scoring.
    Returns top_k (chunk_text, score) tuples sorted by score descending.
    """
    scored = [(chunk, score_chunk_relevance(query, chunk)) for chunk in chunks]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(x ** 2 for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def two_stage_retrieve(
    query: str,
    chunks: list[str],
    chunk_embeddings: list[list[float]],
    query_embedding: list[float],
    initial_k: int = 20,
    final_k: int = 5,
) -> list[str]:
    """
    Two-stage pipeline: vector retrieve top initial_k, then re-rank to final_k.
    Returns list of final_k chunk strings.
    """
    # Stage 1: cosine similarity retrieval
    similarities = [
        (chunk, _cosine_similarity(query_embedding, emb))
        for chunk, emb in zip(chunks, chunk_embeddings)
    ]
    similarities.sort(key=lambda x: x[1], reverse=True)
    candidates = [chunk for chunk, _ in similarities[:initial_k]]

    # Stage 2: LLM re-ranking
    reranked = llm_rerank(query, candidates, top_k=final_k)
    return [chunk for chunk, _ in reranked]
