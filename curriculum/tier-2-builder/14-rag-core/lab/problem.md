# Lab 14 — Build a Document Q&A with RAG

## Problem Statement

You will build a complete Retrieval-Augmented Generation (RAG) pipeline in `starter/solution.py`.

The pipeline has three core functions and one wrapper class. All three functions must work together: `build_index` creates the vector index, `retrieve_chunks` searches it, and `answer_question` ties everything together with Claude.

---

## Function Specifications

### `build_index(documents: list[dict]) -> list[dict]`

**Input:** A list of document dicts. Each dict has:
- `"id"`: str — unique identifier
- `"text"`: str — the document content
- `"source"`: str — the document filename or label

**What to do:**
1. For each document, call `get_openai_client().embeddings.create(model=EMBEDDING_MODEL, input=doc["text"])`
2. Extract the embedding from `response.data[0].embedding`
3. Add the `"embedding"` key to the document dict
4. Return the list of enriched document dicts

**Output:** Same list of dicts, each now containing an `"embedding"` key (list of floats).

---

### `cosine_similarity(v1: list[float], v2: list[float]) -> float`

Already implemented for you. Returns the cosine similarity between two vectors. Returns 0.0 if either vector is all zeros.

---

### `retrieve_chunks(query: str, index: list[dict], top_k: int = 3) -> list[dict]`

**Input:**
- `query`: the user's question as a string
- `index`: the list returned by `build_index`
- `top_k`: number of results to return (default 3)

**What to do:**
1. Embed the query: `get_openai_client().embeddings.create(model=EMBEDDING_MODEL, input=query)`
2. Extract the query vector from `response.data[0].embedding`
3. For each chunk in the index, compute `cosine_similarity(query_vector, chunk["embedding"])`
4. Add a `"similarity"` key to each chunk dict with its score
5. Sort the list by `"similarity"` descending (highest first)
6. Return the top `top_k` results

**Output:** List of up to `top_k` chunk dicts, each with a `"similarity"` key, sorted highest to lowest.

---

### `answer_question(question: str, index: list[dict], top_k: int = 3) -> dict`

**Input:**
- `question`: the user's question
- `index`: the list returned by `build_index`
- `top_k`: number of chunks to retrieve

**What to do:**
1. Call `retrieve_chunks(question, index, top_k)` to get the relevant chunks
2. Format the context string: for each chunk, format as `[Source: {chunk['source']}]\n{chunk['text']}`, joined by `\n\n`
3. Format `RAG_PROMPT_TEMPLATE` with `context=context` and `question=question`
4. Call Claude using `get_anthropic_client()`:
   - `model=LLM_MODEL`
   - `max_tokens=512`
   - `system=RAG_SYSTEM_PROMPT`
   - `messages=[{"role": "user", "content": formatted_prompt}]`
5. Extract the answer text from `response.content[0].text`
6. Collect unique source values from the retrieved chunks
7. Return `{"answer": answer_text, "sources": unique_sources, "chunks_used": top_k}`

**Output:** Dict with keys:
- `"answer"`: str — Claude's answer
- `"sources"`: list[str] — unique source values from retrieved chunks (deduplicated)
- `"chunks_used"`: int — the `top_k` value used

---

### `RAGPipeline` class

```python
class RAGPipeline:
    def __init__(self, documents: list[dict]):
        self.index = build_index(documents)

    def ask(self, question: str, top_k: int = 3) -> dict:
        return answer_question(question, self.index, top_k)
```

This class is already stubbed out for you. Once `build_index` and `answer_question` are implemented, `RAGPipeline` will work automatically.

---

## Example Usage

```python
documents = [
    {"id": "1", "text": "Enterprise customers get a 60-day refund window.", "source": "refund-policy.txt"},
    {"id": "2", "text": "Standard accounts have a 30-day refund window.", "source": "refund-policy.txt"},
    {"id": "3", "text": "Refunds are processed within 5–7 business days.", "source": "refund-policy.txt"},
    {"id": "4", "text": "Python SDK v2.0 was released on March 1, 2024.", "source": "changelog.txt"},
]

pipeline = RAGPipeline(documents)
result = pipeline.ask("How long do enterprise customers have to request a refund?")

print(result["answer"])
# "Based on the provided documents, enterprise customers have a 60-day window to request a refund."

print(result["sources"])
# ["refund-policy.txt"]

print(result["chunks_used"])
# 3
```

---

## Constants to Use

All constants are defined at the top of `starter/solution.py`:

```python
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "claude-3-haiku-20240307"

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided document excerpts.
Only answer based on the provided context. If the context doesn't contain the answer, say so clearly.
Always cite which document excerpt supports your answer."""

RAG_PROMPT_TEMPLATE = """Context documents:
{context}

Question: {question}

Answer based only on the context above:"""
```

---

## Acceptance Criteria

- [ ] `build_index` returns a list where each dict has an `"embedding"` key
- [ ] `build_index` calls the OpenAI embeddings API exactly once per document
- [ ] `retrieve_chunks` returns results sorted by similarity descending
- [ ] `retrieve_chunks` returns exactly `top_k` results when `top_k < len(index)`
- [ ] `cosine_similarity([1,0,0], [1,0,0])` returns `1.0`
- [ ] `cosine_similarity([1,0,0], [0,1,0])` returns approximately `0.0`
- [ ] `answer_question` returns a dict with `"answer"`, `"sources"`, and `"chunks_used"` keys
- [ ] `sources` contains only unique values (no duplicates)
- [ ] `RAGPipeline` builds the index in `__init__` and answers via `.ask()`
- [ ] All tests pass: `pytest tests/ -v`

---

## Running Tests

```bash
cd curriculum/tier-2-builder/14-rag-core/lab
pytest tests/ -v
```

To test against the reference solution:

```bash
LAB_TARGET=solution pytest tests/ -v
```
