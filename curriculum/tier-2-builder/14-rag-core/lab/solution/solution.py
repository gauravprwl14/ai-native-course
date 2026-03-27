"""Lab 14: Build a Document Q&A with RAG — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import math
from utils import get_anthropic_client, get_openai_client

EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "claude-3-haiku-20240307"

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided document excerpts.
Only answer based on the provided context. If the context doesn't contain the answer, say so clearly.
Always cite which document excerpt supports your answer."""

RAG_PROMPT_TEMPLATE = """Context documents:
{context}

Question: {question}

Answer based only on the context above:"""


def build_index(documents: list[dict]) -> list[dict]:
    """
    Build an in-memory vector index from documents.
    Each document: {"id": str, "text": str, "source": str}
    Returns list of {"id", "text", "source", "embedding"} dicts.
    """
    openai_client = get_openai_client()
    indexed = []
    for doc in documents:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=doc["text"]
        )
        indexed.append({
            **doc,
            "embedding": response.data[0].embedding
        })
    return indexed


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a ** 2 for a in v1))
    mag2 = math.sqrt(sum(b ** 2 for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def retrieve_chunks(query: str, index: list[dict], top_k: int = 3) -> list[dict]:
    """
    Find the top_k most similar chunks to the query.
    Returns list of top_k document dicts sorted by similarity (highest first).
    """
    openai_client = get_openai_client()
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    query_vector = response.data[0].embedding

    scored = []
    for chunk in index:
        sim = cosine_similarity(query_vector, chunk["embedding"])
        scored.append({**chunk, "similarity": sim})

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


def answer_question(question: str, index: list[dict], top_k: int = 3) -> dict:
    """
    Answer a question using RAG.
    Returns {"answer": str, "sources": list[str], "chunks_used": int}
    """
    chunks = retrieve_chunks(question, index, top_k)

    context = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )

    prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)

    client = get_anthropic_client()
    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=512,
        system=RAG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    answer_text = response.content[0].text
    unique_sources = list({c["source"] for c in chunks})

    return {
        "answer": answer_text,
        "sources": unique_sources,
        "chunks_used": top_k
    }


class RAGPipeline:
    """A clean wrapper that indexes documents on construction and answers via .ask()."""

    def __init__(self, documents: list[dict]):
        self.index = build_index(documents)

    def ask(self, question: str, top_k: int = 3) -> dict:
        return answer_question(question, self.index, top_k)


if __name__ == "__main__":
    sample_docs = [
        {"id": "1", "text": "Enterprise customers get a 60-day refund window.", "source": "refund-policy.txt"},
        {"id": "2", "text": "Standard accounts have a 30-day refund window.", "source": "refund-policy.txt"},
        {"id": "3", "text": "Refunds are processed within 5-7 business days.", "source": "refund-policy.txt"},
        {"id": "4", "text": "Python SDK v2.0 was released on March 1, 2024.", "source": "changelog.txt"},
    ]

    pipeline = RAGPipeline(sample_docs)
    result = pipeline.ask("How long do enterprise customers have to request a refund?")
    print("Answer:", result["answer"])
    print("Sources:", result["sources"])
    print("Chunks used:", result["chunks_used"])
