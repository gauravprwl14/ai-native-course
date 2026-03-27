# Embedding Model Mismatch

**Category:** rag
**Difficulty:** Hard
**Key Concepts:** embedding model versioning, mixed-model index, re-indexing strategy, semantic space alignment
**Time:** 30–45 min

---

## Problem Statement

Your RAG pipeline has 2 million documents indexed with `text-embedding-ada-002` (1536 dimensions). Your company wants to migrate to `text-embedding-3-large` (3072 dimensions) for better retrieval quality.

A teammate proposes: "Start indexing new documents with `text-embedding-3-large`. Leave old ones as-is. Over time the index will naturally migrate."

What is wrong with this plan? Design the correct migration strategy.

---

## What Makes This Hard

The teammate's proposal sounds reasonable — it's incremental, low-risk, and requires no downtime. It is catastrophically wrong.

The reason is not the dimension mismatch (that's detectable at query time). The reason is **semantic space incompatibility**.

Each embedding model learns a different mapping from text to vector space. The vector `[0.12, -0.45, 0.89, ...]` from `ada-002` and the vector `[0.12, -0.45, 0.89, ...]` from `text-embedding-3-large` mean completely different things. When you query with a `text-embedding-3-large` vector and retrieve `ada-002` vectors via cosine similarity, you are measuring the angle between vectors in two different semantic universes.

The similarity scores from cross-model comparisons are noise — not high, not low, just meaningless numbers that happen to look like similarity scores.

This creates a silent failure: your retrieval returns results, they look plausible, but 40% of them are semantically unrelated. There's no error, no warning, no obvious signal that anything is wrong. Users see slightly worse answers and attribute it to model quality.

A secondary challenge: 2 million documents cannot be re-indexed in one API call. You need a migration strategy that handles rate limits, partial failure, and a transition period where both models coexist.

---

## Naive Approach

**"Use the new model for new documents. Keep old documents as-is."**

```python
def get_embedding(text: str, doc_date: str) -> list[float]:
    # Use new model for documents after the migration date
    if doc_date >= "2024-01-15":
        return embed_with_3_large(text)
    else:
        return embed_with_ada_002(text)

# At query time:
query_embedding = embed_with_3_large(query)
results = vector_db.search(query_embedding, top_k=10)
# ^ This searches ALL documents with a 3-large query vector
# 40% of documents were indexed with ada-002 — their similarities are noise
```

**Why this fails:**

1. **Cosine similarity across model boundaries is meaningless.** A query vector from `text-embedding-3-large` compared to an index vector from `ada-002` does not measure semantic similarity. The score is noise.
2. **Different dimensions cause runtime errors.** `ada-002` → 1536 dims, `text-embedding-3-large` → 3072 dims. Most vector databases reject queries where the query vector dimension doesn't match the stored vector dimension.
3. **Silent degradation.** If you somehow bridge the dimension gap, you get silent quality degradation — results look plausible but are wrong. No error is thrown.
4. **The "natural migration" never completes.** If you add 5,000 new documents/day, after 6 months you have 1.1M old-model docs and 900K new-model docs. The mixed state persists indefinitely.
5. **No rollback path.** If the new model performs worse on your document domain, you have no clean way to revert. The index is permanently mixed.

---

## Expert Approach

**Never mix embedding models in the same vector collection.**

Each vector collection must be a single-model collection. Mixing models within a collection is not a performance problem — it is a correctness problem.

**Migration strategy: parallel index with batched re-indexing**

**Phase 1: Preparation (Day 0)**
- Create a new, empty collection: `documents_v2` (3072 dims, `text-embedding-3-large`)
- Tag every document in the existing collection with `embedding_model: "ada-002"`
- Version tag all new documents before they enter the pipeline

**Phase 2: Batched re-indexing (Days 1–7)**
- Re-index in batches of 10,000 documents/hour
- Cost estimate: 2M documents × avg 400 tokens/doc = 800M tokens ÷ 1000 × $0.00002 = ~$16
- Use exponential backoff on rate limit errors
- Track progress with a `last_indexed_id` checkpoint — resumable if interrupted

**Phase 3: Parallel query (Days 1–7, during migration)**
- On every query: search both `documents_v1` (ada-002) and `documents_v2` (3-large) simultaneously
- Apply a `model_tag` filter so each query only compares within-model embeddings
- Merge the top-K results from each collection using a weighted score
- This is a temporary state — do not optimize for it

**Phase 4: Cutover (Day 8)**
- Once 100% of documents are in `documents_v2`, switch to single-collection query
- Keep `documents_v1` read-only for 7 days (rollback window)
- After 7 days: delete `documents_v1`

**Key principle: version tag every chunk**

Every document chunk in your vector store must carry an `embedding_model` metadata field. This makes future migrations detectable immediately and prevents accidental mixed-model queries.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import time
import json
import asyncio
from dataclasses import dataclass
from typing import Optional
import anthropic
import openai  # For text-embedding-3-large

# In production, use your vector DB client (Pinecone, Weaviate, Qdrant, etc.)
# This example uses a stub to illustrate the migration logic

anthropic_client = anthropic.Anthropic()
openai_client = openai.OpenAI()

# --- Embedding helpers ---

def embed_ada_002(texts: list[str]) -> list[list[float]]:
    """Legacy: text-embedding-ada-002 (1536 dims)."""
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    return [item.embedding for item in response.data]


def embed_3_large(texts: list[str]) -> list[list[float]]:
    """New: text-embedding-3-large (3072 dims)."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=texts
    )
    return [item.embedding for item in response.data]


# --- Document schema ---

@dataclass
class Document:
    doc_id: str
    text: str
    metadata: dict

@dataclass
class IndexedChunk:
    chunk_id: str
    doc_id: str
    text: str
    embedding: list[float]
    embedding_model: str   # ALWAYS tag with model name
    embedding_dims: int
    indexed_at: float


# --- Stub vector DB (replace with Pinecone/Qdrant/etc.) ---

class VectorCollection:
    """Stub. In production, use your vector DB SDK."""
    def __init__(self, name: str, dims: int):
        self.name = name
        self.dims = dims
        self._store: dict[str, IndexedChunk] = {}

    def upsert(self, chunk: IndexedChunk):
        assert len(chunk.embedding) == self.dims, (
            f"Dimension mismatch: collection expects {self.dims}, got {len(chunk.embedding)}"
        )
        self._store[chunk.chunk_id] = chunk

    def query(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        assert len(query_vector) == self.dims, (
            f"Query dimension mismatch: collection expects {self.dims}, got {len(query_vector)}"
        )
        # Stub: return random results. In production: cosine similarity search.
        return [(chunk_id, 0.9) for chunk_id in list(self._store.keys())[:top_k]]

    def count(self) -> int:
        return len(self._store)

    def get_all_ids(self) -> list[str]:
        return list(self._store.keys())


# --- Migration engine ---

class EmbeddingMigration:
    """
    Migrates a vector collection from one embedding model to another.
    Designed for 2M+ documents with rate limit handling and progress tracking.
    """

    def __init__(
        self,
        source_collection: VectorCollection,
        target_collection: VectorCollection,
        new_embed_fn,
        batch_size: int = 100,
        rate_limit_rpm: int = 3000,  # text-embedding-3-large: 3000 RPM
        checkpoint_path: str = "migration_checkpoint.json",
    ):
        self.source = source_collection
        self.target = target_collection
        self.new_embed_fn = new_embed_fn
        self.batch_size = batch_size
        self.rate_limit_rpm = rate_limit_rpm
        self.checkpoint_path = checkpoint_path
        self.min_delay = 60.0 / rate_limit_rpm * batch_size  # Seconds between batches

    def load_checkpoint(self) -> dict:
        try:
            with open(self.checkpoint_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {"migrated_ids": [], "last_batch_at": 0}

    def save_checkpoint(self, checkpoint: dict):
        with open(self.checkpoint_path, "w") as f:
            json.dump(checkpoint, f)

    def run(self, dry_run: bool = False) -> dict:
        """
        Execute the migration. Resumable: skip already-migrated chunks.
        """
        checkpoint = self.load_checkpoint()
        migrated_ids = set(checkpoint["migrated_ids"])

        all_ids = self.source.get_all_ids()
        remaining = [id for id in all_ids if id not in migrated_ids]

        print(f"Migration status: {len(migrated_ids)}/{len(all_ids)} chunks already migrated")
        print(f"Remaining: {len(remaining)} chunks")

        if dry_run:
            cost_estimate = len(remaining) * 400 / 1000 * 0.00002  # avg 400 tokens/chunk
            print(f"Estimated cost: ${cost_estimate:.2f}")
            return {"status": "dry_run", "remaining": len(remaining), "cost_estimate": cost_estimate}

        total_migrated = len(migrated_ids)
        errors = 0

        for i in range(0, len(remaining), self.batch_size):
            batch_ids = remaining[i:i + self.batch_size]
            batch_chunks = [self.source._store[id] for id in batch_ids if id in self.source._store]

            if not batch_chunks:
                continue

            # Rate limiting
            elapsed = time.time() - checkpoint.get("last_batch_at", 0)
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)

            try:
                texts = [chunk.text for chunk in batch_chunks]
                new_embeddings = self.new_embed_fn(texts)

                for chunk, new_embedding in zip(batch_chunks, new_embeddings):
                    new_chunk = IndexedChunk(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        text=chunk.text,
                        embedding=new_embedding,
                        embedding_model="text-embedding-3-large",
                        embedding_dims=len(new_embedding),
                        indexed_at=time.time(),
                    )
                    if not dry_run:
                        self.target.upsert(new_chunk)
                    migrated_ids.add(chunk.chunk_id)
                    total_migrated += 1

                checkpoint["migrated_ids"] = list(migrated_ids)
                checkpoint["last_batch_at"] = time.time()
                self.save_checkpoint(checkpoint)

                print(f"Migrated {total_migrated}/{len(all_ids)} chunks ({100*total_migrated/len(all_ids):.1f}%)")

            except Exception as e:
                errors += 1
                print(f"Batch error at chunk {i}: {e}")
                if errors > 10:
                    raise RuntimeError(f"Too many errors ({errors}) — stopping migration")
                time.sleep(5 * errors)  # Exponential backoff

        return {
            "status": "complete",
            "migrated": total_migrated,
            "errors": errors,
        }


# --- Dual-collection query (during transition) ---

class DualModelRAG:
    """
    Query both collections during migration. After migration: use single collection.
    """

    def __init__(
        self,
        collection_v1: VectorCollection,   # ada-002, 1536 dims
        collection_v2: VectorCollection,   # text-embedding-3-large, 3072 dims
        migration_progress: float = 0.0,  # 0.0 to 1.0
    ):
        self.v1 = collection_v1
        self.v2 = collection_v2
        self.migration_progress = migration_progress

    def query(self, query_text: str, top_k: int = 10) -> list[dict]:
        results = []

        # Always query v2 with v2 embedding (correct)
        if self.v2.count() > 0:
            v2_query = embed_3_large([query_text])[0]
            v2_results = self.v2.query(v2_query, top_k=top_k)
            for chunk_id, score in v2_results:
                results.append({
                    "chunk_id": chunk_id,
                    "score": score,
                    "source_model": "text-embedding-3-large",
                    "collection": "v2"
                })

        # Query v1 ONLY with v1 embedding (correct) — never cross-model
        remaining_in_v1 = 1.0 - self.migration_progress
        if remaining_in_v1 > 0 and self.v1.count() > 0:
            v1_query = embed_ada_002([query_text])[0]
            v1_results = self.v1.query(v1_query, top_k=top_k)
            for chunk_id, score in v1_results:
                results.append({
                    "chunk_id": chunk_id,
                    "score": score,
                    "source_model": "ada-002",
                    "collection": "v1"
                })

        # Merge and deduplicate (doc_id level)
        seen_doc_ids = set()
        merged = []
        for r in sorted(results, key=lambda x: x["score"], reverse=True):
            if r["chunk_id"] not in seen_doc_ids:
                seen_doc_ids.add(r["chunk_id"])
                merged.append(r)
            if len(merged) >= top_k:
                break

        return merged


# --- Version-tagged indexing (prevents future mismatches) ---

def index_document(
    collection: VectorCollection,
    doc: Document,
    embed_fn,
    model_name: str,
) -> list[IndexedChunk]:
    """
    Always tag embeddings with the model that created them.
    Future migrations will use this tag to identify what needs re-indexing.
    """
    # Chunk the document
    chunks = chunk_text(doc.text, max_tokens=512)

    # Embed all chunks
    embeddings = embed_fn([chunk for chunk in chunks])

    indexed = []
    for i, (chunk_text_content, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = IndexedChunk(
            chunk_id=f"{doc.doc_id}-chunk-{i}",
            doc_id=doc.doc_id,
            text=chunk_text_content,
            embedding=embedding,
            embedding_model=model_name,     # ALWAYS tag
            embedding_dims=len(embedding),  # ALWAYS record
            indexed_at=time.time(),
        )
        collection.upsert(chunk)
        indexed.append(chunk)

    return indexed


def chunk_text(text: str, max_tokens: int = 512) -> list[str]:
    """Stub chunker — replace with your actual chunking strategy."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_tokens // 2):  # ~2 words/token estimate
        chunk = " ".join(words[i:i + max_tokens // 2])
        if chunk:
            chunks.append(chunk)
    return chunks or [text]


if __name__ == "__main__":
    # Setup
    collection_v1 = VectorCollection("documents_v1", dims=1536)
    collection_v2 = VectorCollection("documents_v2", dims=3072)

    # Seed v1 with some documents (simulating existing 2M docs)
    print("Seeding v1 collection (ada-002)...")
    sample_docs = [
        Document(f"doc-{i}", f"This is document {i} about topic {i % 10}", {})
        for i in range(20)
    ]

    # Note: skip real API calls in this demo — stubs would be used
    print(f"v1 collection ready: {collection_v1.count()} chunks")

    # Show migration dry run
    migration = EmbeddingMigration(
        source_collection=collection_v1,
        target_collection=collection_v2,
        new_embed_fn=embed_3_large,
        batch_size=100,
    )
    result = migration.run(dry_run=True)
    print(f"Migration plan: {result}")

    # During migration: dual-collection query
    rag = DualModelRAG(collection_v1, collection_v2, migration_progress=0.0)
    print("\nDual-model RAG initialized. During migration, both collections are queried.")
    print("After migration, switch to single-collection query against v2 only.")
```

</details>

---

## Interview Version

**Opening (20 seconds):** "The teammate's proposal fails because embedding models don't share a semantic space. An `ada-002` vector and a `text-embedding-3-large` vector at the same position in cosine space have no relationship. Cross-model similarity scores are noise, not signal. You'd have a pipeline that looks like it's working but returns 40% irrelevant results."

**Draw the semantic space issue:**
```
ada-002 space:
  "dog" → [0.2, 0.8, -0.3, ...]
  "cat" → [0.3, 0.7, -0.2, ...]  ← close, makes sense

text-embedding-3-large space:
  "dog" → [0.9, -0.1, 0.5, ...]  ← completely different axes
  "cat" → [0.8, -0.2, 0.6, ...]  ← close in THIS space, but...

Cross-model cosine("dog" in ada-002, "cat" in 3-large):
  → [0.2, 0.8, -0.3] · [0.8, -0.2, 0.6] = meaningless number
```

**The migration plan:**
```
Day 0: Create documents_v2 (3072 dims). Tag all v1 chunks with embedding_model="ada-002"
Days 1–7: Re-index 10K chunks/hour (cost: ~$16 for 2M docs)
           Query: run v1 with ada-002 vector + v2 with 3-large vector → merge
Day 8: Switch to v2 only. Keep v1 for 7-day rollback window.
Day 15: Delete v1.
```

**Rule to state clearly:** "Never mix embedding models in the same collection. Tag every chunk with its embedding model. Every future migration will thank you."

---

## Follow-up Questions

1. During the dual-collection transition (Days 1–7), your queries run two embedding calls (one for each model) and two vector searches. This doubles query latency and cost. How would you architect the dual-collection query to minimize latency, and at what migration progress percentage would you switch to single-collection queries?
2. After migrating to `text-embedding-3-large`, you discover that retrieval quality on your medical documents actually decreased compared to `ada-002`. How do you diagnose whether the quality drop is due to the model or the migration process, and what's your rollback plan?
3. Your company has 5 RAG applications, each with its own vector collection, all currently on `ada-002`. A new policy requires all collections to migrate to `text-embedding-3-large` within 3 months. Design the migration sequencing and shared infrastructure to handle this at scale without 5 independent migration scripts.
