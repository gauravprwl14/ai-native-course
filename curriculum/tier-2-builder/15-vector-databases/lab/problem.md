# Lab 15: Vector Databases with Chroma

## Overview

You will build a persistent document store backed by ChromaDB. The store uses OpenAI embeddings to index documents and supports similarity search with optional metadata filtering.

---

## Functions to Implement

### 1. `create_collection(name, persist_dir=None) -> chromadb.Collection`

Create or retrieve a Chroma collection.

**Requirements:**
- If `persist_dir` is provided, use `chromadb.PersistentClient(path=persist_dir)`
- If `persist_dir` is `None`, use `chromadb.EphemeralClient()`
- Always configure the collection with `metadata={"hnsw:space": "cosine"}`
- Return `client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})`

**Signature:**
```python
def create_collection(name: str, persist_dir: str = None) -> chromadb.Collection:
```

---

### 2. `add_documents(collection, documents) -> int`

Embed and upsert a list of documents into the collection.

**Requirements:**
- Accept a list of dicts, each with at least `"id"`, `"text"`, and any additional metadata fields
- Call `get_embeddings(texts)` **once** for all document texts in a single batch — not once per document
- Separate `ids`, `texts`, and `metadatas` from the document dicts
- Metadatas should contain every key in the document except `"id"` and `"text"`
- Call `collection.add(ids=..., embeddings=..., documents=..., metadatas=...)`
- Return the number of documents added (`len(documents)`)

**Document shape:**
```python
{
    "id": "doc-001",
    "text": "The vacation policy allows 20 days per year.",
    "source": "hr-policy.pdf",
    # any other metadata fields...
}
```

**Signature:**
```python
def add_documents(collection: chromadb.Collection, documents: list[dict]) -> int:
```

---

### 3. `search(collection, query, top_k=3, filter=None) -> list[dict]`

Search for the most similar documents to a query string.

**Requirements:**
- Embed the query string using `get_embeddings([query])`
- Call `collection.query(query_embeddings=..., n_results=top_k, where=filter)`
- If `filter` is `None`, omit the `where` argument (or pass `None` — Chroma accepts both)
- Parse the Chroma results into a list of dicts, one per result:
  ```python
  {"id": str, "text": str, "distance": float, "metadata": dict}
  ```
- `results["ids"][0]` — list of ids
- `results["documents"][0]` — list of document texts
- `results["distances"][0]` — list of distances (lower = more similar for cosine)
- `results["metadatas"][0]` — list of metadata dicts

**Signature:**
```python
def search(collection: chromadb.Collection, query: str, top_k: int = 3, filter: dict = None) -> list[dict]:
```

---

### 4. `delete_document(collection, doc_id) -> None`

Delete a single document from the collection by its ID.

**Requirements:**
- Call `collection.delete(ids=[doc_id])`
- Return `None`

**Signature:**
```python
def delete_document(collection: chromadb.Collection, doc_id: str) -> None:
```

---

## Example Usage

```python
from solution import create_collection, add_documents, search, delete_document

# Create a persistent collection
collection = create_collection("hr-docs", persist_dir="./chroma_db")

# Add documents
docs = [
    {"id": "doc-1", "text": "Vacation policy: 20 days per year.", "source": "hr-policy.pdf"},
    {"id": "doc-2", "text": "Remote work: up to 3 days per week.", "source": "hr-policy.pdf"},
    {"id": "doc-3", "text": "Deployment pipeline must include integration tests.", "source": "eng-handbook.pdf"},
]
count = add_documents(collection, docs)
print(f"Added {count} documents")

# Search without filter
results = search(collection, "how many vacation days do I get?", top_k=2)
for r in results:
    print(f"[{r['distance']:.4f}] {r['text']}")

# Search with metadata filter
hr_results = search(
    collection,
    "remote work",
    top_k=2,
    filter={"source": {"$eq": "hr-policy.pdf"}}
)

# Delete a document
delete_document(collection, "doc-1")
```

---

## Running Your Solution

```bash
cd curriculum/tier-2-builder/15-vector-databases/lab/starter
python solution.py
```

## Running Tests

```bash
cd curriculum/tier-2-builder/15-vector-databases/lab
pytest tests/ -v
```
