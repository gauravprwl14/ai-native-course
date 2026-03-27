# Retrieval Freshness: Stale Data in Production RAG

**Category:** rag
**Difficulty:** Hard
**Key Concepts:** incremental indexing, document versioning, cache invalidation, real-time vs batch ingestion
**Time:** 30–40 min

---

## Problem Statement

You built a RAG system over a company knowledge base of 10,000 documents — pricing sheets, product specs, internal policies. Your ingestion pipeline runs once per week on Sunday night (full re-index).

By Thursday, the business has updated 200 documents: pricing changed on 40 SKUs, a return policy was revised, and three product specs were corrected.

On Monday morning after Sunday's re-index, sales reps start asking the bot about last week's pricing. It answers correctly. But by the following Thursday — four days before the next index run — three sales reps submitted incorrect quotes based on outdated pricing returned by the bot.

**The damage is real: one wrong quote resulted in a $12,000 revenue loss.**

Your task: redesign the ingestion and retrieval architecture to prevent stale data from reaching users. Constraints:

- Full re-indexing 10,000 documents costs ~$5/run at $0.0001 per 1K tokens (average 500 tokens/doc)
- Real-time streaming indexing adds operational complexity your team wants to minimize
- You need a solution that scales to 10,000 documents and is operable by a 3-person team

---

## What Makes This Hard

The naive response — "index more often" — trades cost for freshness but does not actually solve the problem. Even nightly full re-indexing:

- Costs $5/night × 365 = $1,825/year in embedding costs alone
- Still leaves a 24-hour staleness window
- A pricing change at 2pm is stale until 3am the next day

The real challenge is that **freshness is not uniform across documents**. A 5-year-old HR policy memo almost never changes. A daily pricing sheet changes every business day. Treating all 10,000 documents identically is the core architectural mistake.

The second non-obvious problem: even after fixing ingestion, the **retrieval layer must communicate uncertainty to the LLM**. A freshly ingested document has no way of signaling "this was updated 10 minutes ago — be cautious" unless you design for it.

---

## Naive Approach

**Re-index all 10,000 documents every night.**

```python
# Runs nightly at 2am
def nightly_reindex():
    documents = fetch_all_documents()  # 10,000 docs
    embeddings = embed_all(documents)  # $5 per run
    vector_db.upsert_all(embeddings)
```

**Why it fails:**

1. **Cost:** $5/night × 365 = $1,825/year, just in embedding costs. At scale (100K docs), this becomes $18,250/year.
2. **Still stale:** A 24-hour window is unacceptable for pricing data. The problem was a 4-day window; you've reduced it to 24 hours, but a pricing change at 9am is still stale until 2am.
3. **No priority:** A legal brief from 2019 and today's pricing sheet get re-indexed on the same schedule. This is wasteful.
4. **No signal to LLM:** Even a freshly indexed document has no mechanism to tell the LLM "this was recently changed — flag it."
5. **Operational fragility:** A failed nightly run means 48 hours of staleness with no alerting.

---

## Expert Approach

### Architecture: Three-Tier Freshness System

Segment documents by change frequency, apply different ingestion strategies to each tier, and add retrieval-layer staleness signals.

**Tier 1 — High-velocity documents (pricing, policy, product specs):**
- Trigger immediate re-indexing on any change (webhook or file watcher)
- Target freshness: < 5 minutes after document save
- Estimated volume: ~500 documents

**Tier 2 — Medium-velocity documents (internal guides, team processes):**
- Delta indexing: check `last_modified` timestamp, re-embed only changed docs
- Run every 6 hours
- Estimated volume: ~3,000 documents

**Tier 3 — Low-velocity documents (archived memos, historical contracts):**
- Weekly batch re-index (current approach is fine for these)
- Estimated volume: ~6,500 documents

### Implementation

#### Step 1: Track Document Modification Timestamps

```python
import hashlib
from datetime import datetime
from typing import Optional

class DocumentRegistry:
    """Track which documents have changed since last index."""

    def __init__(self, db_connection):
        self.db = db_connection

    def get_changed_documents(self, since: datetime) -> list[str]:
        """Return doc IDs where last_modified > since."""
        return self.db.query(
            "SELECT doc_id FROM documents WHERE last_modified > ? AND indexed_at < last_modified",
            (since,)
        )

    def mark_indexed(self, doc_id: str, indexed_at: datetime):
        self.db.execute(
            "UPDATE documents SET indexed_at = ? WHERE doc_id = ?",
            (indexed_at, doc_id)
        )

    def get_content_hash(self, doc_id: str) -> Optional[str]:
        """Use content hash to detect changes even when timestamps are unreliable."""
        row = self.db.query("SELECT content_hash FROM documents WHERE doc_id = ?", (doc_id,))
        return row[0]["content_hash"] if row else None
```

#### Step 2: Delta Indexing — Only Re-Embed Changed Documents

```python
from datetime import datetime, timedelta

def delta_index(registry: DocumentRegistry, vector_db, embedder, since_hours: int = 6):
    """Re-index only documents changed in the last N hours."""
    since = datetime.utcnow() - timedelta(hours=since_hours)
    changed_doc_ids = registry.get_changed_documents(since)

    if not changed_doc_ids:
        print("No changes detected. Skipping index run.")
        return

    print(f"Delta index: {len(changed_doc_ids)} documents changed since {since}")

    for doc_id in changed_doc_ids:
        doc = fetch_document(doc_id)
        new_hash = hashlib.md5(doc.content.encode()).hexdigest()

        # Skip if content hasn't actually changed (timestamp bump but no edit)
        if registry.get_content_hash(doc_id) == new_hash:
            continue

        chunks = chunk_document(doc)
        embeddings = embedder.embed(chunks)

        # Delete old chunks for this doc, insert new ones
        vector_db.delete(filter={"doc_id": doc_id})
        vector_db.upsert(embeddings, metadata=[{
            "doc_id": doc_id,
            "last_updated": doc.last_modified.isoformat(),
            "doc_tier": doc.tier,
            "content_hash": new_hash,
        } for _ in chunks])

        registry.mark_indexed(doc_id, datetime.utcnow())
```

#### Step 3: Real-Time Indexing for Tier 1 Documents (Webhook)

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

@app.post("/webhook/document-updated")
async def handle_document_update(payload: dict, background_tasks: BackgroundTasks):
    doc_id = payload["doc_id"]
    doc_tier = get_document_tier(doc_id)

    if doc_tier == "tier1":
        # Immediate re-index — do not wait for scheduled run
        background_tasks.add_task(reindex_single_document, doc_id)
        return {"status": "queued_immediate"}

    # Tier 2 and 3 are handled by scheduled delta indexing
    return {"status": "will_be_indexed_in_next_run"}

async def reindex_single_document(doc_id: str):
    doc = fetch_document(doc_id)
    chunks = chunk_document(doc)
    embeddings = embedder.embed(chunks)
    vector_db.delete(filter={"doc_id": doc_id})
    vector_db.upsert(embeddings, metadata=[{"doc_id": doc_id, "last_updated": doc.last_modified.isoformat()}])
```

#### Step 4: Staleness Warning in Retrieval

```python
from datetime import datetime, timedelta

STALENESS_THRESHOLD_DAYS = {
    "tier1": 1,   # Pricing: warn if older than 1 day
    "tier2": 7,   # Guides: warn if older than 7 days
    "tier3": 90,  # Archives: warn if older than 90 days
}

def retrieve_with_freshness(query: str, tenant_id: str, vector_db) -> dict:
    results = vector_db.similarity_search(
        query,
        filter={"tenant_id": tenant_id},
        k=5,
        include_metadata=True,
    )

    now = datetime.utcnow()
    context_chunks = []
    staleness_warnings = []

    for chunk in results:
        last_updated = datetime.fromisoformat(chunk.metadata["last_updated"])
        doc_tier = chunk.metadata.get("doc_tier", "tier3")
        age_days = (now - last_updated).days

        threshold = STALENESS_THRESHOLD_DAYS[doc_tier]
        if age_days > threshold:
            staleness_warnings.append(
                f"Note: The following content was last verified {age_days} days ago "
                f"and may be outdated: '{chunk.content[:80]}...'"
            )

        context_chunks.append(chunk.content)

    return {
        "context": "\n\n".join(context_chunks),
        "staleness_warnings": staleness_warnings,
    }

def build_prompt_with_freshness(query: str, retrieval_result: dict) -> str:
    warnings = retrieval_result["staleness_warnings"]
    warning_block = ""
    if warnings:
        warning_block = "\n\nDATA FRESHNESS WARNINGS:\n" + "\n".join(warnings) + "\n\nFlag these uncertainties in your answer.\n"

    return f"""Answer the following question using the provided context.{warning_block}

Context:
{retrieval_result['context']}

Question: {query}
Answer:"""
```

#### Step 5: Prefer Fresher Chunks When Similarity Scores Are Close

```python
def rerank_by_freshness(results: list, similarity_threshold: float = 0.05) -> list:
    """
    If two chunks have similarity scores within 0.05 of each other,
    prefer the more recently updated chunk.
    """
    if not results:
        return results

    max_score = results[0].score  # Assume sorted by score descending

    def sort_key(chunk):
        score_gap = max_score - chunk.score
        last_updated = datetime.fromisoformat(chunk.metadata["last_updated"])
        freshness_bonus = 1 / (1 + (datetime.utcnow() - last_updated).days)

        # Only apply freshness tiebreaker within the similarity threshold
        if score_gap <= similarity_threshold:
            return (-chunk.score - freshness_bonus * 0.01)
        return -chunk.score

    return sorted(results, key=sort_key)
```

### Cost Analysis

| Strategy | Docs Re-Embedded/Week | Cost/Week | Cost/Year |
|---|---|---|---|
| Full re-index nightly | 70,000 (10K × 7) | $3.50 | $182 |
| Full re-index weekly | 10,000 | $0.50 | $26 |
| Delta indexing (200 changed/week) | 200 | $0.01 | $0.52 |
| Tier 1 real-time (500 tier-1 docs, 1 change/week avg) | 500 | $0.025 | $1.30 |

Delta indexing reduces embedding cost by **98%** compared to nightly full re-indexing while delivering meaningfully better freshness guarantees.

*Calculation basis: 500 tokens/doc average, $0.0001/1K tokens (OpenAI text-embedding-3-small)*

---

## Solution

<details>
<summary>Show Solution</summary>

### Complete Architecture Diagram

```
Document Store (S3 / SharePoint / Confluence)
        |
        |  file watcher / webhook
        v
   Change Detector
        |
        +---> Tier 1 (pricing, policy) ---> Immediate reindex queue
        |
        +---> Tier 2 (guides, specs)   ---> 6-hour delta index job
        |
        +---> Tier 3 (archives)        ---> Weekly batch index job
        |
        v
   Embedding Service (OpenAI / Cohere)
        |
        v
   Vector DB (Pinecone / Weaviate)
   [chunk, doc_id, last_updated, doc_tier, tenant_id]
        |
   Query Time
        |
        v
   Retrieval + Freshness Reranker
        |
        v
   Staleness Warning Injector
        |
        v
   LLM (with freshness context in prompt)
```

### Deployment Checklist

- [ ] Tag every chunk with `last_updated`, `doc_tier`, `doc_id`
- [ ] Implement file watcher or webhook for Tier 1 documents
- [ ] Set up delta index job running every 6 hours for Tier 2
- [ ] Keep weekly batch job for Tier 3 (no change needed)
- [ ] Add staleness warning logic to retrieval layer
- [ ] Add freshness reranker for close similarity scores
- [ ] Alert on failed index runs (staleness detector)
- [ ] Measure: track percentage of retrieved chunks that are "stale" over time

### Alerting for Ingestion Failures

```python
def check_index_health(vector_db, registry) -> dict:
    """Run every hour. Alert if critical docs are stale."""
    tier1_docs = registry.get_tier1_documents()
    stale_tier1 = []

    for doc in tier1_docs:
        last_indexed = registry.get_last_indexed(doc.doc_id)
        if (datetime.utcnow() - last_indexed).hours > 2:
            stale_tier1.append(doc.doc_id)

    if stale_tier1:
        send_alert(f"CRITICAL: {len(stale_tier1)} Tier 1 documents have not been re-indexed in > 2 hours")

    return {"stale_tier1_count": len(stale_tier1)}
```

</details>

---

## Interview Version

"Your RAG system returns stale pricing data. Sales reps are submitting wrong quotes. The full re-index costs $5 and runs weekly. How do you fix this?"

**Draw on whiteboard:**
```
10,000 docs
    |
    +-- 500 docs: Tier 1 (pricing, policy) -- change in < 5 min
    +-- 3,000 docs: Tier 2 (specs, guides) -- change in < 6 hrs
    +-- 6,500 docs: Tier 3 (archives)      -- weekly is fine
```

**Structure your answer:**
1. Diagnose: the real problem is that all documents are treated with equal urgency
2. Segment by volatility: not all documents need the same freshness guarantee
3. Fix the pipeline: webhook for Tier 1, delta indexing for Tier 2, batch for Tier 3
4. Fix the retrieval: metadata timestamps + staleness warnings in the LLM prompt
5. Quantify: delta indexing 200 changed docs = $0.01/week vs $3.50 for nightly full re-index

**Key phrase to use:** "Freshness is not uniform across a document corpus. The architecture should reflect that."

---

## Follow-up Questions

1. Your document store is SharePoint, which does not support webhooks. How do you implement near-real-time change detection without a push mechanism? What are the trade-offs of polling vs. hash-based change detection?
2. A user asks a question, the bot returns an answer with a staleness warning, and the user ignores the warning. Three months later, the wrong answer causes a problem. What product and technical safeguards would you add to reduce this class of failure?
3. Your delta indexing job detects 200 changed documents but fails halfway through (network error at document 100). How do you make the ingestion pipeline idempotent so a retry does not produce duplicate chunks or miss updates?
