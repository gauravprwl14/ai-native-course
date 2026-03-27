# Production RAG at Scale

**Category:** system-design
**Difficulty:** Expert
**Key Concepts:** vector DB at scale, caching layers, horizontal scaling, latency optimization, cost management
**Time:** 40–45 min

---

## Problem Statement

Design a RAG system for a customer support platform with the following requirements:

- **Corpus:** 50 million documents (product manuals, support tickets, FAQs)
- **Traffic:** 10,000 queries per minute at peak
- **Latency:** p95 < 500ms end-to-end (embed query → retrieve → generate)
- **Availability:** 99.9% uptime (< 8.7 hours downtime per year)
- **Budget:** $50,000/month infrastructure
- **Team:** 8 engineers, including 2 ML engineers

Constraints:
- The support team adds ~5,000 new documents per day
- Queries repeat: a significant percentage of support queries are the same question rephrased
- The system must operate globally (NA, EU, APAC)

**Design the full architecture. Include component choices with justification, cost breakdown, and the trade-offs you're making.**

---

## What Makes This Hard

This is not a "which vector DB should I use" question. The hard problems are:

1. **Embedding cost at scale:** At 10,000 queries/minute, embedding every query costs $0.0001/1K tokens × ~50 tokens/query = $0.000005/query × 600,000 queries/hour = $3/hour = $2,160/month in embeddings alone. That's before you factor in LLM generation costs.

2. **Latency budget decomposition:** 500ms total means roughly: 50ms (embed) + 100ms (vector search) + 300ms (LLM generation) + 50ms (network/overhead). Any component over-budget kills p95. Most engineers don't decompose the budget before designing.

3. **50M vectors is a different regime than 500K.** Chroma and FAISS running locally are dev tools. At 50M vectors with 10K QPS, you need distributed vector search with sharding. This is a different operational tier.

4. **5,000 new docs/day means 35,000 new docs/week.** The index is not static — freshness matters for support documents. Ingestion must be continuous, not batch.

5. **Global operation with < 500ms p95** means you cannot have one region do all the work. Network latency alone from APAC to US is 150–200ms.

---

## Naive Approach

**Scale up Chroma with more compute, add a load balancer in front.**

```python
# Chroma with persistent storage, "production" deployment
chroma_client = chromadb.HttpClient(host="chroma-server", port=8000)
collection = chroma_client.get_collection("support_docs")

def query(question: str):
    embedding = openai.embeddings.create(input=question, model="text-embedding-3-small")
    results = collection.query(query_embeddings=[embedding.data[0].embedding], n_results=5)
    return results
```

**Why it fails:**

1. **Chroma is not designed for 50M vectors or 10K QPS.** Chroma uses a flat index (HNSW) in a single-process Python server. At 50M vectors, HNSW search is slow and memory-intensive (~200GB RAM for float32 embeddings at 1536 dimensions). There is no horizontal sharding.
2. **No caching layer.** Every query goes to the embedding API and vector DB, even if the same question was asked 30 seconds ago.
3. **Single region.** APAC users get 200ms+ network overhead before the 500ms budget starts.
4. **No cost management.** At 10K QPS with no caching, embedding costs alone are $2,160/month and growing.

---

## Expert Approach

### Latency Budget Decomposition (Design Constraint)

Before choosing any component, decompose the 500ms p95 budget:

```
Total budget: 500ms p95
  ├── Network (client to nearest region): 20ms
  ├── Query embedding: 30ms      (use small/fast model, cache aggressively)
  ├── Vector search: 80ms        (distributed index, ANN not exact search)
  ├── LLM generation: 320ms      (streaming, so user sees output sooner)
  └── Overhead (serialization, load balancing): 50ms
```

Any design decision that blows one of these budgets (e.g., exact nearest neighbor search instead of ANN) must be justified by trade-offs elsewhere.

### Architecture

```
User Request (global)
       |
       v
[CDN + Edge Cache]  ← static FAQ answers cached at edge (< 5ms)
       |
       v
[Regional API Gateway]  ← NA / EU / APAC (3 deployments)
       |
       v
[Query Embedding Service]  ← horizontally scaled, stateless
       |      |
       |      v
       |   [Redis Embedding Cache]  ← TTL: 24h
       |      (cache hit → skip embedding API call)
       |
       v
[Semantic Cache]  ← Redis: store (query_embedding, answer) pairs
       |            Cache hit if cosine similarity > 0.95 with a prior query
       |            (30% hit rate target → skip vector search + LLM entirely)
       |
       v
[Vector Search Service]  ← Pinecone or Weaviate (distributed, sharded)
       |                    50M vectors, ANN search, metadata filtering
       |
       v
[Reranker]  ← Cross-encoder reranking of top-20 → top-5
       |       (runs locally, not an API call — Colbert or BGE-reranker)
       |
       v
[LLM Generation]  ← Streaming response via SSE
       |            Route by query complexity: Haiku for simple, Sonnet for complex
       |
       v
[Response + Source Citations]
```

### Component Choices with Justification

**Vector DB: Pinecone (managed) or Weaviate (self-hosted)**

Pinecone:
- Managed service, no operational overhead
- 50M vectors at 1536 dimensions: ~$700/month (p2 pod type)
- Built-in horizontal scaling, ANN search via HNSW
- p95 query latency: ~50ms at this scale

Weaviate self-hosted:
- ~$300/month in EC2 compute (3 × r6g.2xlarge)
- Requires 2 engineers to operate reliably
- Better for compliance requirements (data stays in your VPC)

**Decision:** Pinecone if the team is < 10 engineers. Weaviate if data sovereignty is required.

**Embedding Cache: Redis with 24-hour TTL**

```python
import hashlib
import json
import redis

redis_client = redis.Redis(host="elasticache-endpoint", port=6379)

def get_embedding_cached(text: str, model: str = "text-embedding-3-small") -> list[float]:
    cache_key = f"emb:{model}:{hashlib.sha256(text.encode()).hexdigest()}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    embedding = openai.embeddings.create(input=text, model=model).data[0].embedding
    redis_client.setex(cache_key, 86400, json.dumps(embedding))  # 24h TTL
    return embedding
```

Cache hit rate for support queries (high repetition): ~40%. This directly reduces embedding API costs by 40%.

**Semantic Cache: Redis with Vector Similarity Check**

```python
def semantic_cache_lookup(query_embedding: list[float]) -> str | None:
    """Return cached answer if a semantically similar query was answered recently."""
    # Store recent (embedding, answer) pairs in Redis
    # Use approximate nearest neighbor search on the cached embeddings
    # Return cached answer if cosine similarity > 0.95

    recent_queries = redis_client.lrange("recent_query_embeddings", 0, 999)  # last 1000 queries

    for cached_entry in recent_queries:
        entry = json.loads(cached_entry)
        similarity = cosine_similarity(query_embedding, entry["embedding"])
        if similarity > 0.95:
            return entry["answer"]

    return None  # cache miss
```

**Target:** 30% semantic cache hit rate → 30% of queries skip vector search and LLM entirely. At 10K QPS, this saves ~3,000 LLM calls/minute.

**Model Routing: Haiku for Simple, Sonnet for Complex**

```python
def classify_query_complexity(query: str) -> str:
    """Route to cheaper model for simple queries."""
    simple_patterns = [
        r"what is your (phone|email|address|hours)",
        r"how do I (reset|change|update) my password",
        r"where is my order",
    ]
    for pattern in simple_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return "haiku"
    return "sonnet"  # default to capable model for complex queries
```

At 10K QPS: if 40% of queries are simple FAQ-type → 4,000 QPS on Haiku (10x cheaper) → significant cost reduction.

### Cost Breakdown

| Component | Monthly Cost |
|---|---|
| Vector DB (Pinecone p2, 50M vectors) | $700 |
| Redis (ElastiCache r6g.large × 3 regions) | $450 |
| Embedding API (60% of 10K QPS × 720 min/month, cache hit 40%) | $1,296 |
| LLM — Sonnet (60% of non-cached queries) | $8,640 |
| LLM — Haiku (40% of non-cached queries) | $576 |
| Compute (embedding service, API gateway, 3 regions) | $2,400 |
| Ingestion pipeline (5K docs/day embedding) | $216 |
| Monitoring, storage, data transfer | $500 |
| **Total** | **~$14,778/month** |

Well within the $50K budget. The remaining $35K/month headroom can absorb 3× traffic growth before requiring architectural changes.

*Calculation basis: Sonnet at $3/M input + $15/M output tokens, Haiku at $0.25/M input + $1.25/M output, text-embedding-3-small at $0.02/1M tokens*

### Ingestion Pipeline (5,000 docs/day)

```python
from celery import Celery
from datetime import datetime

app = Celery("ingestion", broker="redis://redis:6379/0")

@app.task(rate_limit="100/m")  # Respect embedding API rate limits
def ingest_document(doc_id: str, content: str, metadata: dict):
    chunks = chunk_document(content)
    embeddings = embed_batch(chunks)  # Batch embedding for cost efficiency

    pinecone_index.upsert(
        vectors=[(f"{doc_id}_{i}", emb, {**metadata, "chunk_index": i})
                 for i, emb in enumerate(embeddings)],
        namespace="support_docs",
    )

    # Invalidate semantic cache for related topics (optional, topic-based)
    invalidate_cache_for_topic(metadata.get("topic"))

# 5,000 docs/day = ~3.5 docs/minute → well within API rate limits
# Batch size 100 chunks/call → efficient API usage
```

### Availability Design (99.9%)

- **Active-active multi-region** (NA, EU, APAC): each region serves local traffic and can absorb another region's load if one goes down
- **Vector DB replication:** Pinecone replicates across availability zones automatically
- **Circuit breaker on LLM calls:** if LLM API returns errors, fall back to retrieval-only response with disclaimer
- **Health checks every 10 seconds** with automated failover
- **Incident budget:** 99.9% = 8.7 hours/year → SLO allows < 2 seconds of downtime per day before burning error budget

---

## Solution

<details>
<summary>Show Solution</summary>

### Architecture Decision Record (ADR)

**ADR-001: Pinecone over Weaviate**
- Chosen because: team is 8 engineers, 2 ML focused — operational overhead of self-hosting distributed vector DB exceeds team capacity
- Trade-off: higher cost ($700 vs $300/month), but saves 0.5 FTE of ops work
- Review trigger: if data sovereignty requirements emerge or team grows to 15+ engineers

**ADR-002: Semantic cache at 0.95 cosine threshold**
- Chosen because: support queries have high repetition ("where is my order" in 20 different phrasings)
- Trade-off: 0.95 is conservative — may miss some valid cache hits. 0.90 would increase cache hit rate but risk returning slightly wrong answers
- Monitoring: track cache hit rate, user satisfaction on cached vs. non-cached responses

**ADR-003: Haiku/Sonnet routing over single model**
- Chosen because: 40% cost reduction on simple queries with minimal quality loss
- Trade-off: routing logic adds ~5ms latency and can mis-classify edge cases
- Monitoring: track user ratings on Haiku vs. Sonnet responses; adjust routing rules monthly

### Load Testing Targets (Pre-Launch)

```python
# k6 load test
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '5m', target: 100 },    // ramp up
    { duration: '10m', target: 10000 }, // target load
    { duration: '5m', target: 0 },      // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],    // p95 < 500ms
    http_req_failed: ['rate<0.001'],     // < 0.1% error rate
  },
};
```

</details>

---

## Interview Version

"Design a RAG system for 50M documents, 10K queries/minute, 500ms p95 latency, $50K/month budget."

**Open with constraint decomposition (2 minutes):**
"Before choosing components, I want to decompose the latency budget: 30ms embed, 80ms vector search, 320ms LLM, 50ms overhead. Each component has to stay in its lane."

**Draw three layers:**
```
Cache Layer:   [Edge Cache] → [Embedding Cache] → [Semantic Cache]
Retrieval:     [Distributed Vector DB] → [Reranker]
Generation:    [Model Router] → [Haiku | Sonnet] → [Streaming Response]
```

**Drive the cost discussion:**
"10K QPS with no caching is $2,160/month in embeddings alone. A 40% embedding cache hit rate cuts that to $1,296. A 30% semantic cache hit rate eliminates 3,000 LLM calls/minute — that's the biggest cost lever."

**Close with a number:**
"Total estimated cost: ~$15K/month, well within the $50K budget. The headroom absorbs 3× traffic growth before we need to revisit architecture."

---

## Follow-up Questions

1. Your semantic cache has a 0.95 cosine similarity threshold. A new product is launched and dozens of users ask slightly different questions about it — none of them hit the cache because the questions are new. Cache hit rate drops to 5% for 48 hours. How do you handle the cost spike, and how do you warm the cache proactively for anticipated high-traffic topics?
2. EU GDPR requires that EU customer data never leaves the EU region. Your current semantic cache stores query content (even hashed). How do you redesign the caching layer to be compliant while preserving the latency benefit?
3. The LLM provider you depend on (your primary) has a 3-hour outage. Your circuit breaker kicks in. Design the fallback behavior: what does the system return during outage, how do you recover gracefully, and what SLO commitments can you honestly make to customers when the primary LLM is unavailable?
