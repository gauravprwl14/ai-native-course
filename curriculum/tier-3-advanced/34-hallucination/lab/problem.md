# Lab 34: Hallucination Detection

## Problem

RAG systems can generate answers that contradict the very documents they retrieved. Your task is to build a faithfulness checker that detects these hallucinations before they reach users.

## Functions to Implement

### `check_faithfulness(answer: str, context: str) -> float`

Use an LLM to score how faithful the given answer is to the given context. Returns a float between 0.0 (answer contradicts context) and 1.0 (every claim is supported by context).

### `detect_contradictions(answer: str, context: str) -> list[str]`

Return a list of sentences from the answer that either contradict something in the context or state facts not mentioned in the context. Returns `[]` if the answer is fully supported.

### `verify_rag_answer(question: str, answer: str, retrieved_chunks: list[str]) -> dict`

Combine both checks to produce a structured verification report:

```python
{
    "faithful": bool,   # True if score >= 0.8
    "score": float,     # Faithfulness score 0-1
    "issues": list[str] # List of problematic sentences
}
```

## Files

- `starter/solution.py` — implement your solution here
- `solution/solution.py` — reference solution (do not peek until done)
- `tests/test_solution.py` — run with `pytest tests/ -v`

## Running Tests

```bash
cd curriculum/tier-3-advanced/34-hallucination/lab
pytest tests/ -v
```
