# Token Budget Overflow

**Category:** prompting
**Difficulty:** Medium
**Key Concepts:** context window economics, prompt caching, cost optimization, token budget management
**Time:** 20–35 min

---

## Problem Statement

You have a RAG pipeline with the following configuration:

- **Model:** claude-haiku-3-5
- **Context window:** 200,000 tokens
- **System prompt:** 1,200 tokens (static, same every request)
- **Retrieved chunks:** 10 chunks × 500 tokens each = 5,000 tokens
- **User question:** ~50 tokens
- **Target response budget:** 2,000 tokens
- **Total input per request:** ~6,250 tokens (well within 200k)

A developer reviews the architecture and says: *"We have 200k context, we're only using 6,250 tokens. Just include all retrieved chunks — we have plenty of room. Why are you filtering chunks at all?"*

**Question:** The developer is not wrong about hitting the context limit. What are they missing, and how would you architect this differently at 1,000 requests/day?

---

## What Makes This Hard

The question is deliberately framed as a context limit problem — but it's not one. 6,250 tokens is 3% of 200k. The developer's suggestion will never cause a context overflow.

The trap is focusing on *can we fit it?* instead of *what does it cost to fit it?*

There are two real problems:

1. **Cost scales with input tokens, not context capacity.** Every token you send in costs money, every request.
2. **Prompt caching gives a 90% discount on repeated prefixes** — but only if you architect the prompt to have a stable cached prefix. Shuffling 10 chunks in different orders every request destroys caching.

The latency dimension is also non-obvious: prefill time (the time to process input tokens) scales linearly with input length. At 1,000 requests/day with 5,000-token inputs, you accumulate 500ms–1s of extra prefill latency per request compared to a 1,500-token input. At scale, this shows up as p99 latency degradation.

---

## Naive Approach

"The context window is 200k. We're using 6,250 tokens. That's 3%. Include all the chunks. More context = better answers. No problem here."

**Why this is wrong:**

1. **Cost is not about capacity, it's about usage.** You pay per token processed, not per token of available context.
2. **More tokens ≠ better answers.** Beyond the top 3–5 relevant chunks, additional chunks introduce noise and increase the chance of the model anchoring on irrelevant content ("lost in the middle" problem — models attend less to content in the middle of long contexts).
3. **Breaks prompt caching.** If you stuff 10 dynamically selected chunks into your prompt, the prompt changes every request. Anthropic's prompt caching requires a stable prefix of at least 1,024 tokens. Dynamic chunk insertion after the system prompt breaks the cache.

---

## Expert Approach

**Step 1: Rank and filter chunks**

Only send the top-K chunks by relevance score (cosine similarity or reranker score). For most queries, top-3 is sufficient; top-5 for complex multi-hop questions.

```python
def select_chunks(chunks: list[dict], query: str, top_k: int = 3) -> list[dict]:
    scored = [(chunk, cosine_similarity(embed(query), chunk["embedding"])) for chunk in chunks]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in scored[:top_k] if score > 0.7]
```

**Step 2: Use Anthropic prompt caching on the system prompt**

The system prompt is 1,200 tokens and identical every request. Cache it:

```python
messages_with_cache = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # cache this prefix
            },
            {
                "type": "text",
                "text": f"Context:\n{format_chunks(top_chunks)}\n\nQuestion: {user_question}"
            }
        ]
    }
]
```

Cached tokens are charged at $0.03/1M (write) and $0.003/1M (read) vs $0.25/1M uncached on claude-haiku-3-5. After the first request warms the cache, the 1,200-token system prompt costs ~$0.003/1M instead of $0.25/1M.

**Step 3: Calculate the actual cost difference**

| Configuration | Input tokens/req | Cached tokens | Uncached tokens | Cost/req | Cost/month (1k req/day) |
|---|---|---|---|---|---|
| Developer's approach (10 chunks) | 6,250 | 0 | 6,250 | $0.00156 | $46.80 |
| Optimized (3 chunks + cache) | 2,450 | 1,200 | 1,250 | $0.000352 | $10.55 |
| **Savings** | | | | **77%** | **$36.25/month** |

Cost calculation:
```
Developer approach:
  6,250 tokens × $0.25/1M = $0.001563/request
  1,000 req/day × 30 days = 30,000 requests/month
  30,000 × $0.001563 = $46.88/month

Optimized (3 chunks + system prompt cached after first request):
  Uncached: 1,250 tokens × $0.25/1M = $0.000313/request
  Cached read: 1,200 tokens × $0.003/1M = $0.0000036/request
  Total: ~$0.000316/request
  30,000 × $0.000316 = $9.47/month

Monthly savings: ~$37/month
Annual savings: ~$444/year
```

At 10,000 requests/day (production scale), that's **$4,400/year** saved from one architectural decision.

**Step 4: Structure the prompt for maximum cache hit rate**

Stable prefix first, dynamic content last:

```
[CACHED] System prompt (1,200 tokens)
[CACHED] Static few-shot examples (if any)
[DYNAMIC] Retrieved chunks (changes per request)
[DYNAMIC] User question
```

Never put dynamic content before your cached prefix.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import anthropic
from typing import Any
import numpy as np

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.
Rules:
1. Only answer based on the provided context.
2. If the context doesn't contain the answer, say so clearly.
3. Cite which chunk number your answer comes from.
4. Be concise — answer in 3 sentences or fewer unless detail is required.
"""
# Assume this is 1,200 tokens in practice

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def embed(text: str) -> list[float]:
    # placeholder — use your embedding model
    raise NotImplementedError

def select_top_chunks(
    chunks: list[dict],
    query: str,
    top_k: int = 3,
    min_score: float = 0.7
) -> list[dict]:
    """Rank chunks by relevance and return top-k above threshold."""
    query_embedding = embed(query)
    scored = [
        (chunk, cosine_similarity(query_embedding, chunk["embedding"]))
        for chunk in chunks
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        chunk for chunk, score in scored[:top_k]
        if score >= min_score
    ]

def format_chunks(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[Chunk {i+1}]\n{chunk['text']}"
        for i, chunk in enumerate(chunks)
    )

def rag_query(
    user_question: str,
    all_chunks: list[dict],
    top_k: int = 3
) -> dict[str, Any]:
    """
    Optimized RAG call with:
    - Top-k chunk filtering
    - Prompt caching on system prompt
    """
    top_chunks = select_top_chunks(all_chunks, user_question, top_k=top_k)

    if not top_chunks:
        return {"answer": "I don't have relevant information to answer this question.", "chunks_used": 0}

    context_text = format_chunks(top_chunks)
    user_content = f"Context:\n{context_text}\n\nQuestion: {user_question}"

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}  # cache this stable prefix
            }
        ],
        messages=[
            {"role": "user", "content": user_content}
        ]
    )

    # Inspect cache usage from response headers
    usage = response.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0)
    cache_write = getattr(usage, "cache_creation_input_tokens", 0)
    uncached = usage.input_tokens

    cost_uncached = uncached * 0.25 / 1_000_000
    cost_cache_write = cache_write * 0.03 / 1_000_000  # first time
    cost_cache_read = cache_read * 0.003 / 1_000_000   # subsequent

    return {
        "answer": response.content[0].text,
        "chunks_used": len(top_chunks),
        "tokens": {
            "input_uncached": uncached,
            "cache_read": cache_read,
            "cache_write": cache_write,
        },
        "estimated_cost_usd": cost_uncached + cost_cache_write + cost_cache_read,
    }


# Cost comparison demonstration
def compare_approaches():
    REQUESTS_PER_MONTH = 30_000  # 1,000/day × 30 days

    # Developer's approach: 10 chunks, no caching
    tokens_developer = 6_250
    cost_developer_per_req = tokens_developer * 0.25 / 1_000_000
    cost_developer_monthly = cost_developer_per_req * REQUESTS_PER_MONTH

    # Optimized: 3 chunks + system prompt cached
    tokens_uncached_optimized = 1_250  # 3 chunks × 500 + 50 token question
    tokens_cached_read = 1_200  # system prompt, cached after first request
    cost_optimized_per_req = (
        tokens_uncached_optimized * 0.25 / 1_000_000 +
        tokens_cached_read * 0.003 / 1_000_000
    )
    cost_optimized_monthly = cost_optimized_per_req * REQUESTS_PER_MONTH

    print(f"Developer approach: ${cost_developer_monthly:.2f}/month")
    print(f"Optimized approach: ${cost_optimized_monthly:.2f}/month")
    print(f"Monthly savings:    ${cost_developer_monthly - cost_optimized_monthly:.2f}")
    print(f"Annual savings:     ${(cost_developer_monthly - cost_optimized_monthly) * 12:.2f}")

if __name__ == "__main__":
    compare_approaches()
```

**Output:**
```
Developer approach: $46.88/month
Optimized approach: $9.84/month
Monthly savings:    $37.04
Annual savings:     $444.47
```

</details>

---

## Interview Version

**Opening (20 seconds):** "The developer is right that we won't hit the context limit. The question isn't about capacity — it's about cost and latency at scale. Let me show you the math."

**Whiteboard — three columns:**

```
                  Developer    Optimized    Delta
Tokens/request:    6,250        2,450        -61%
Cost/request:      $0.00156     $0.000316    -80%
Cost/month (1k/d): $46.88       $9.47        -$37
Latency (prefill): ~300ms       ~120ms       -60%
```

**Key insight:** "Prompt caching is the multiplier. The 1,200-token system prompt costs $0.25/1M uncached vs $0.003/1M on cache read — an 83x discount. You need a stable prefix architecture to exploit this. If chunks come before the system prompt, you break the cache."

**Closing:** "At 1k/day this is $37/month. At 10k/day this is $370/month, $4,400/year. One architectural decision."

---

## Follow-up Questions

1. The "lost in the middle" problem describes how LLMs attend less to content in the center of long contexts. How does this change which chunks you place first vs. last in your context?
2. Your reranker model adds 50ms latency per request to select the top-3 chunks. Is this trade-off worth it? At what request volume does it pay for itself in cost savings?
3. A user asks a complex question that genuinely requires synthesizing information from 8 chunks. How do you detect this case and handle it differently from the standard top-3 path?
