# Lab 17: Hybrid Search Pipeline

## Goal

Implement a hybrid search pipeline that combines BM25 keyword search with vector cosine similarity retrieval, fused using Reciprocal Rank Fusion (RRF).

## Background

Pure semantic (vector) search fails when queries contain specific technical terms, product codes, or exact strings that the embedding model wasn't trained to understand deeply. BM25 excels at these exact matches. Hybrid search combines both approaches: RRF takes the ranked output of each retriever and produces a single ranked list that benefits from both.

This lab is entirely algorithmic — no API calls needed.

## Functions to Implement

### `bm25_search(query, documents, top_k=5) -> list[tuple[int, float]]`

Perform BM25 keyword search over a list of documents.

1. Tokenize all documents: `[doc.lower().split() for doc in documents]`
2. Build a `BM25Okapi` index from the tokenized documents
3. Score all documents: `bm25.get_scores(query.lower().split())`
4. Sort (doc_index, score) pairs by score descending
5. Return the top `top_k` pairs

**Returns:** `list[tuple[int, float]]` — (document index, BM25 score), sorted highest score first.

---

### `reciprocal_rank_fusion(rankings, k=60) -> list[tuple[int, float]]`

Fuse multiple ranked lists using RRF.

- `rankings`: a list of lists, where each inner list contains document indices ordered from best to worst
- For each ranking, for each document at position `rank` (0-indexed), add `1 / (k + rank + 1)` to that document's cumulative RRF score
- Return `(doc_index, rrf_score)` pairs sorted by score descending

**Example:**
```python
rrf = reciprocal_rank_fusion([[2, 0, 1], [0, 2, 1]])
# Doc 0: rank 2 in list 0 + rank 1 in list 1 → 1/62 + 1/61 ≈ 0.0325
# Doc 2: rank 1 in list 0 + rank 2 in list 1 → 1/61 + 1/62 ≈ 0.0325
# Doc 1: rank 3 in list 0 + rank 3 in list 1 → 1/63 + 1/63 ≈ 0.0317
```

---

### `hybrid_search(query, documents, embeddings, query_embedding, top_k=5) -> list[tuple[int, float]]`

Full hybrid pipeline:

1. Call `bm25_search(query, documents, top_k=len(documents))` to get all documents ranked by keyword relevance
2. Extract the BM25 ranking as just indices: `[idx for idx, _ in bm25_results]`
3. Compute cosine similarity between `query_embedding` and every document embedding
4. Sort by similarity descending to get `vector_ranking` (just indices)
5. Call `reciprocal_rank_fusion([bm25_ranking, vector_ranking])`
6. Return the top `top_k` results

The `cosine_similarity(v1, v2)` function is already implemented — use it.

---

## Files

```
lab/
├── problem.md            ← this file
├── starter/
│   ├── __init__.py
│   └── solution.py       ← fill in the TODOs
├── solution/
│   └── solution.py       ← reference solution (don't peek!)
└── tests/
    ├── __init__.py
    └── test_solution.py  ← run these to verify your work
```

## Running Tests

```bash
cd curriculum/tier-2-builder/17-hybrid-search/lab
pytest tests/ -v
```

## Hints

- BM25Okapi takes a list of tokenized documents (list of lists of strings)
- `bm25.get_scores(query_tokens)` returns a numpy array of scores — use `enumerate` to get (index, score) pairs
- RRF: use `rank` as 0-indexed position, add `1 / (k + rank + 1)` (the +1 converts to 1-indexed)
- `cosine_similarity` is already implemented, just call it
