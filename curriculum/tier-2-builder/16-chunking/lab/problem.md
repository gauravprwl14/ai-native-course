# Lab 16: Chunking Strategies

## Goal

Implement three chunking functions that form the document preprocessing stage of a RAG pipeline.

## Background

Before a document can be embedded and stored in a vector database, it must be split into smaller, retrievable pieces called **chunks**. The chunking strategy you choose — and the parameters you set — directly affect retrieval quality.

In this lab you will implement:

1. **Fixed-size chunking with overlap** — the simplest strategy
2. **Sentence-based chunking** — splits at sentence boundaries for better semantic coherence
3. **Chunking with metadata** — attaches source information to every chunk

## Functions to Implement

### `fixed_size_chunk(text, chunk_size=512, overlap=50) -> list[str]`

Split `text` into character chunks of at most `chunk_size` characters. Each consecutive chunk starts `chunk_size - overlap` characters after the previous chunk starts. This means the last `overlap` characters of chunk N are repeated at the start of chunk N+1.

**Example:**

```python
text = "ABCDEFGHIJ"  # 10 chars
chunks = fixed_size_chunk(text, chunk_size=6, overlap=2)
# chunk 0: "ABCDEF"  (chars 0–6)
# chunk 1: "EFGHIJ"  (chars 4–10, overlap=2 → step=4)
```

### `sentence_chunk(text, max_tokens=256) -> list[str]`

Split `text` into chunks at sentence boundaries. A sentence boundary is detected using the regex `(?<=[.!?])\s+`. Accumulate sentences into a chunk until adding the next sentence would push the chunk over `max_tokens`. When the limit is reached, save the current chunk and start a new one. Use `tiktoken` (already imported) or approximate token counting.

**Rules:**
- Never split mid-sentence
- A single sentence that exceeds `max_tokens` on its own should still be its own chunk (don't discard it)
- Return an empty list if `text` is empty or whitespace-only

### `chunk_with_metadata(text, source, chunk_size=512, overlap=50) -> list[dict]`

Call `fixed_size_chunk(text, chunk_size, overlap)` and wrap each chunk in a metadata dict:

```python
{
    "text": str,          # the chunk content
    "source": str,        # the source parameter passed in
    "chunk_index": int,   # 0-indexed position of this chunk
    "token_count": int    # approximate token count (use count_tokens from tiktoken)
}
```

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
cd curriculum/tier-2-builder/16-chunking/lab
pytest tests/ -v
```

## Hints

- For `fixed_size_chunk`: use a `while` loop with index `i`, step `i += chunk_size - overlap`
- For `sentence_chunk`: `re.split(r'(?<=[.!?])\s+', text)` splits into sentences. Accumulate into `current_sentences`, check token count before each append
- For `chunk_with_metadata`: call `fixed_size_chunk` first, then use a list comprehension or loop to build the dicts
