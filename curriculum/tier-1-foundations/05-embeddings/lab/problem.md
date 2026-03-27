# Lab 05 — Semantic Search with Embeddings

## Problem Statement

You will implement three functions that together form the core of a semantic search pipeline.

---

### Function 1: `embed_text(text: str) -> list[float]`

Call the OpenAI embeddings API to convert a string into a vector of floats.

**Requirements:**
- Use `get_openai_client()` from shared utils to get the client
- Call `client.embeddings.create(model=EMBEDDING_MODEL, input=text)`
- Return `response.data[0].embedding` — a list of 1536 floats

**Example:**
```python
vec = embed_text("Hello, world!")
print(len(vec))   # 1536
print(type(vec[0]))  # <class 'float'>
```

---

### Function 2: `cosine_similarity(v1: list[float], v2: list[float]) -> float`

Compute cosine similarity between two vectors **without using any external libraries** — implement it with pure Python math.

**Formula:**
```
cos(θ) = (v1 · v2) / (|v1| × |v2|)
```

Where:
- `v1 · v2` = dot product = `sum(a*b for a, b in zip(v1, v2))`
- `|v1|` = magnitude = `math.sqrt(sum(a**2 for a in v1))`

**Expected behaviour:**
| Input | Output |
|-------|--------|
| `[1, 0]`, `[1, 0]` | `1.0` (identical direction) |
| `[1, 0]`, `[0, 1]` | `0.0` (orthogonal) |
| `[1, 0]`, `[-1, 0]` | `-1.0` (opposite direction) |

---

### Function 3: `find_most_similar(query: str, candidates: list[str]) -> tuple[str, float]`

Given a query string and a list of candidate strings, return the candidate that is most semantically similar to the query, along with its similarity score.

**Steps:**
1. Embed the query with `embed_text`
2. Embed each candidate with `embed_text`
3. Compute `cosine_similarity` between the query vector and each candidate vector
4. Return a tuple of `(most_similar_string, highest_score)`

**Example:**
```python
query = "I love dogs"
candidates = [
    "cats are wonderful pets",
    "I enjoy spending time with my dog",
    "pizza is my favourite food",
]
result, score = find_most_similar(query, candidates)
print(result)  # "I enjoy spending time with my dog"
print(score)   # ~0.85 (varies slightly by model version)
```

---

## Files

| File | Description |
|------|-------------|
| `starter/solution.py` | Fill in the TODOs here |
| `solution/solution.py` | Reference implementation |
| `tests/test_solution.py` | Automated tests (uses mocks — no real API calls) |

## How to Run

```bash
# Install dependency
pip install openai

# Set your API key
# Edit curriculum/shared/.env and add: OPENAI_API_KEY=sk-...

# Run your implementation
cd curriculum/tier-1-foundations/05-embeddings/lab/starter
python solution.py

# Run tests
cd curriculum/tier-1-foundations/05-embeddings/lab
pytest tests/ -v
```
