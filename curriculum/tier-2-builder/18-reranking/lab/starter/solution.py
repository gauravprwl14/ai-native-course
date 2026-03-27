"""Lab 18: Re-ranking"""
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
    # TODO:
    # Format RELEVANCE_PROMPT, call API with temperature=0
    # Parse response as int, clamp to 1-10 range
    # Return the score
    """
    raise NotImplementedError("Implement score_chunk_relevance")


def llm_rerank(query: str, chunks: list[str], top_k: int = 5) -> list[tuple[str, int]]:
    """
    Re-rank chunks by relevance using LLM scoring.
    Returns top_k (chunk_text, score) tuples sorted by score descending.
    # TODO:
    # Score each chunk using score_chunk_relevance
    # Sort by score descending
    # Return top_k results as (chunk, score) tuples
    """
    raise NotImplementedError("Implement llm_rerank")


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
    # TODO:
    # 1. Compute cosine similarity for all chunks
    # 2. Take top initial_k by similarity
    # 3. Re-rank with llm_rerank, take top final_k
    # 4. Return just the chunk strings
    """
    raise NotImplementedError("Implement two_stage_retrieve")
