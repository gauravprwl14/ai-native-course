"""Lab 05: Semantic Search with Embeddings"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from utils import get_openai_client

EMBEDDING_MODEL = "text-embedding-3-small"


def embed_text(text: str) -> list[float]:
    """
    Get the embedding vector for a piece of text.

    # TODO: Use get_openai_client() to call client.embeddings.create()
    # with model=EMBEDDING_MODEL and input=text
    # Return the embedding as a list of floats: response.data[0].embedding
    """
    raise NotImplementedError("Implement embed_text")


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    # TODO:
    # dot_product = sum(a*b for a, b in zip(v1, v2))
    # magnitude1 = math.sqrt(sum(a**2 for a in v1))
    # magnitude2 = math.sqrt(sum(b**2 for b in v2))
    # return dot_product / (magnitude1 * magnitude2)
    """
    raise NotImplementedError("Implement cosine_similarity")


def find_most_similar(query: str, candidates: list[str]) -> tuple[str, float]:
    """
    Find the most semantically similar string from candidates to the query.

    # TODO:
    # 1. Embed the query
    # 2. Embed each candidate
    # 3. Compute cosine similarity between query and each candidate
    # 4. Return (most_similar_text, highest_similarity_score)
    """
    raise NotImplementedError("Implement find_most_similar")


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
