# Lab 18: Re-ranking

## Problem Statement

You are improving the retrieval stage of a RAG pipeline. Raw vector search returns too many noisy candidates. Your job is to implement a two-stage pipeline:

1. **Stage 1 — Vector retrieval:** compute cosine similarity between a query embedding and all chunk embeddings, take the top `initial_k` candidates.
2. **Stage 2 — Re-rank:** use an LLM to score each candidate for relevance to the query, sort by score, and return the top `final_k` chunks.

## Functions to Implement

### `score_chunk_relevance(query: str, chunk: str) -> int`

Use the Anthropic API to ask an LLM how relevant `chunk` is to `query`. The LLM should respond with a single integer from 1 to 10.

- Use `RELEVANCE_PROMPT` (provided in the starter).
- Call the API with `temperature=0` for deterministic scoring.
- Parse the response as an integer.
- Clamp the result to the range [1, 10] in case the LLM returns an out-of-range value.

### `llm_rerank(query: str, chunks: list[str], top_k: int = 5) -> list[tuple[str, int]]`

Score every chunk using `score_chunk_relevance`, sort by score descending, and return the top `top_k` results as a list of `(chunk_text, score)` tuples.

### `two_stage_retrieve(query, chunks, chunk_embeddings, query_embedding, initial_k=20, final_k=5) -> list[str]`

1. Compute cosine similarity between `query_embedding` and every vector in `chunk_embeddings`.
2. Select the top `initial_k` chunks by similarity.
3. Pass those candidates to `llm_rerank` to get `final_k` results.
4. Return just the chunk strings (not the scores).

## Cosine Similarity Formula

```
cosine_similarity(a, b) = dot(a, b) / (|a| * |b|)
```

## Acceptance Criteria

- `score_chunk_relevance` returns an `int` in [1, 10]
- `score_chunk_relevance` calls the API with `temperature=0`
- `llm_rerank` returns a list of `(str, int)` tuples, sorted by score descending
- `llm_rerank` returns at most `top_k` items
- `two_stage_retrieve` returns a list of strings
- `two_stage_retrieve` returns at most `final_k` items

## Running Tests

```bash
cd curriculum/tier-2-builder/18-reranking/lab
pytest tests/ -v
```
