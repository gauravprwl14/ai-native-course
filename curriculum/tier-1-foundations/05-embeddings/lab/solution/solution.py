"""Lab 05: Semantic Search with Embeddings (SOLUTION)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from utils import get_openai_client

EMBEDDING_MODEL = "text-embedding-3-small"


def embed_text(text: str) -> list[float]:
    """Get the embedding vector for a piece of text."""
    client = get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a ** 2 for a in v1))
    magnitude2 = math.sqrt(sum(b ** 2 for b in v2))
    return dot_product / (magnitude1 * magnitude2)


def find_most_similar(query: str, candidates: list[str]) -> tuple[str, float]:
    """Find the most semantically similar string from candidates to the query."""
    query_vec = embed_text(query)
    best_text = None
    best_score = float("-inf")
    for candidate in candidates:
        candidate_vec = embed_text(candidate)
        score = cosine_similarity(query_vec, candidate_vec)
        if score > best_score:
            best_score = score
            best_text = candidate
    return (best_text, best_score)


if __name__ == "__main__":
    query = "I love dogs"
    candidates = [
        "cats are wonderful pets",
        "I enjoy spending time with my dog",
        "pizza is my favourite food",
        "machine learning is fascinating",
    ]

    print(f"Query: '{query}'")
    print(f"Candidates: {candidates}")
    print()

    result, score = find_most_similar(query, candidates)
    print(f"Most similar: '{result}'")
    print(f"Similarity score: {score:.4f}")
