"""Lab 17: Hybrid Search"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from rank_bm25 import BM25Okapi


def bm25_search(query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
    """
    BM25 keyword search.
    Returns list of (doc_index, score) tuples, sorted by score descending.

    # TODO:
    # tokenize: tokenized_docs = [doc.lower().split() for doc in documents]
    # bm25 = BM25Okapi(tokenized_docs)
    # scores = bm25.get_scores(query.lower().split())
    # Sort by score descending, return top_k (index, score) pairs
    """
    raise NotImplementedError("Implement bm25_search")


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a**2 for a in v1))
    m2 = math.sqrt(sum(b**2 for b in v2))
    return dot / (m1 * m2) if m1 and m2 else 0.0


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """
    Fuse multiple ranked lists using RRF.
    rankings: list of lists, each inner list is doc_indices ranked best-to-worst
    Returns: sorted list of (doc_index, rrf_score) tuples, highest score first

    # TODO:
    # scores = {}
    # for ranking in rankings:
    #   for rank, doc_idx in enumerate(ranking):
    #     scores[doc_idx] = scores.get(doc_idx, 0) + 1 / (k + rank + 1)
    # return sorted(scores.items(), key=lambda x: x[1], reverse=True)
    """
    raise NotImplementedError("Implement reciprocal_rank_fusion")


def hybrid_search(
    query: str,
    documents: list[str],
    embeddings: list[list[float]],
    query_embedding: list[float],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """
    Combine BM25 and vector search with RRF fusion.
    Returns sorted list of (doc_index, rrf_score), highest score first.

    # TODO:
    # 1. bm25_results = bm25_search(query, documents, top_k=len(documents))
    # 2. Extract just the indices: bm25_ranking = [idx for idx, _ in bm25_results]
    # 3. Compute cosine similarity for all embeddings, sort descending
    # 4. Get vector_ranking (just indices)
    # 5. Call reciprocal_rank_fusion([bm25_ranking, vector_ranking])
    # 6. Return top_k results
    """
    raise NotImplementedError("Implement hybrid_search")
