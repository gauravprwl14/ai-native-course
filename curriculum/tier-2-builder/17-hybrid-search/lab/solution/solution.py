"""Lab 17: Hybrid Search — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from rank_bm25 import BM25Okapi


def bm25_search(query: str, documents: list[str], top_k: int = 5) -> list[tuple[int, float]]:
    """
    BM25 keyword search over a list of documents.
    Returns a list of (doc_index, score) tuples, sorted by score descending.
    """
    tokenized_docs = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    scores = bm25.get_scores(query.lower().split())

    # Sort (index, score) pairs by score descending
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    m1 = math.sqrt(sum(a**2 for a in v1))
    m2 = math.sqrt(sum(b**2 for b in v2))
    return dot / (m1 * m2) if m1 and m2 else 0.0


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """
    Fuse multiple ranked lists using Reciprocal Rank Fusion.

    rankings: list of lists — each inner list is document indices ordered best to worst
    k: constant (default 60) — dampens the advantage of rank-1
    Returns: list of (doc_index, rrf_score) sorted by score descending
    """
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc_idx in enumerate(ranking):
            # rank is 0-indexed; +1 converts to 1-indexed for the RRF formula
            scores[doc_idx] = scores.get(doc_idx, 0.0) + 1.0 / (k + rank + 1)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(
    query: str,
    documents: list[str],
    embeddings: list[list[float]],
    query_embedding: list[float],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """
    Full hybrid search pipeline: BM25 + vector cosine similarity fused with RRF.
    Returns top_k (doc_index, rrf_score) tuples sorted by score descending.
    """
    # Step 1: BM25 — rank all documents by keyword relevance
    bm25_results = bm25_search(query, documents, top_k=len(documents))
    bm25_ranking = [idx for idx, _ in bm25_results]

    # Step 2: Vector — rank all documents by cosine similarity
    sim_scores = [
        (i, cosine_similarity(query_embedding, emb))
        for i, emb in enumerate(embeddings)
    ]
    sim_scores.sort(key=lambda x: x[1], reverse=True)
    vector_ranking = [idx for idx, _ in sim_scores]

    # Step 3: RRF fusion
    fused = reciprocal_rank_fusion([bm25_ranking, vector_ranking])
    return fused[:top_k]
