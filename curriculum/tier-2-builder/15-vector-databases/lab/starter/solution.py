"""Lab 15: Vector Databases with Chroma"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import chromadb
from utils import get_openai_client

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a list of texts using OpenAI."""
    client = get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def create_collection(name: str, persist_dir: str = None) -> chromadb.Collection:
    """
    Create or get a Chroma collection.
    If persist_dir is provided, use PersistentClient. Otherwise, use EphemeralClient.
    Returns the collection object.

    # TODO:
    # If persist_dir: client = chromadb.PersistentClient(path=persist_dir)
    # Else: client = chromadb.EphemeralClient()
    # Return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    """
    raise NotImplementedError("Implement create_collection")


def add_documents(collection: chromadb.Collection, documents: list[dict]) -> int:
    """
    Add documents to the collection.
    Each document: {"id": str, "text": str, "source": str, ...metadata}
    Returns number of documents added.

    # TODO:
    # 1. Get embeddings for all document texts in batch
    #      texts = [doc["text"] for doc in documents]
    #      embeddings = get_embeddings(texts)
    # 2. Separate ids, texts, metadatas from the document dicts
    #      ids = [doc["id"] for doc in documents]
    #      metadatas = [{k: v for k, v in doc.items() if k not in ("id", "text")} for doc in documents]
    # 3. Call collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    # 4. Return len(documents)
    """
    raise NotImplementedError("Implement add_documents")


def search(collection: chromadb.Collection, query: str, top_k: int = 3, filter: dict = None) -> list[dict]:
    """
    Search for similar documents.
    Returns list of {"id", "text", "distance", "metadata"} dicts.

    # TODO:
    # 1. Get query embedding
    #      query_embedding = get_embeddings([query])[0]
    # 2. Call collection.query(query_embeddings=[query_embedding], n_results=top_k, where=filter)
    # 3. Parse results into list of dicts:
    #      results["ids"][0], results["documents"][0],
    #      results["distances"][0], results["metadatas"][0]
    #      Return [{"id": id, "text": text, "distance": dist, "metadata": meta} ...]
    """
    raise NotImplementedError("Implement search")


def delete_document(collection: chromadb.Collection, doc_id: str) -> None:
    """
    Delete a document from the collection by ID.
    # TODO: collection.delete(ids=[doc_id])
    """
    raise NotImplementedError("Implement delete_document")


if __name__ == "__main__":
    print("Creating collection...")
    collection = create_collection("demo")

    docs = [
        {"id": "doc-1", "text": "Vacation policy: 20 days per year.", "source": "hr-policy.pdf"},
        {"id": "doc-2", "text": "Remote work: up to 3 days per week from home.", "source": "hr-policy.pdf"},
        {"id": "doc-3", "text": "Deployment pipeline must include integration tests.", "source": "eng-handbook.pdf"},
    ]

    count = add_documents(collection, docs)
    print(f"Added {count} documents.")

    results = search(collection, "how many vacation days do employees get?", top_k=2)
    print("\nSearch results:")
    for r in results:
        print(f"  [{r['distance']:.4f}] {r['text']}")

    print("\nDeleting doc-1...")
    delete_document(collection, "doc-1")
    print(f"Collection size after delete: {collection.count()}")
