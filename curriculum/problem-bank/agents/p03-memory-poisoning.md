# Memory Poisoning

**Category:** agents
**Difficulty:** Expert
**Key Concepts:** memory versioning, recency vs relevance trade-off, memory consolidation, semantic deduplication
**Time:** 35–45 min

---

## Problem Statement

You built an agent with long-term memory. When a user shares a fact, your agent stores it in a vector database (Pinecone/Weaviate/pgvector). When the user asks a question, the agent retrieves the most semantically similar memories.

Memory storage:
```python
def store_memory(user_id: str, fact: str):
    embedding = embed(fact)
    db.insert({
        "user_id": user_id,
        "fact": fact,
        "embedding": embedding,
        "timestamp": datetime.now().isoformat()
    })
```

Memory retrieval:
```python
def retrieve_memories(user_id: str, query: str, top_k: int = 5) -> list[str]:
    query_embedding = embed(query)
    return db.query(
        filter={"user_id": user_id},
        vector=query_embedding,
        top_k=top_k
    )
```

After 2 weeks in production, users report contradictory answers. You investigate user `u_4892`:

```json
Memory entries for u_4892:
[
  {"fact": "User's name is Alice", "timestamp": "2024-01-01T10:00:00"},
  {"fact": "User prefers dark mode", "timestamp": "2024-01-03T14:00:00"},
  {"fact": "User's name is Bob", "timestamp": "2024-01-15T09:00:00"},
  {"fact": "User works at Acme Corp", "timestamp": "2024-01-15T09:01:00"}
]
```

When the user asks "What's my name?", the vector search returns `"User's name is Alice"` because its embedding is more similar to "What's my name?" than the newer `"User's name is Bob"` entry.

The agent says "Your name is Alice" — which was correct 2 weeks ago, but the user updated it.

**How do you redesign the memory architecture to prevent this?**

---

## What Makes This Hard

The instinct is to sort by recency: "just use the most recent memory, not the most similar." But this over-corrects. A user who mentioned their city once three months ago shouldn't have that fact overridden by a more recent unrelated fact just because it's newer.

The real problem is that pure vector similarity is a retrieval mechanism designed for documents, not for mutable facts about a person. Documents don't get superseded. Facts do.

There are three distinct failure modes:

1. **Contradictory facts:** "Name is Alice" vs "Name is Bob" — only one can be true, the newer one wins.
2. **Outdated facts:** "Works at Acme Corp" (2024-01-01) vs "Works at Beta Inc" (2024-03-15) — an update, not a contradiction.
3. **Additive facts:** "Likes coffee" (2024-01-01) + "Prefers oat milk in coffee" (2024-02-01) — both valid, the newer one adds detail.

A system that blindly deduplicates loses additive facts. A system that keeps everything accumulates contradictions. You need semantic deduplication at write time plus recency weighting at read time.

---

## Naive Approach

```python
# Approach A: Sort by recency
def retrieve_memories_by_recency(user_id: str, query: str, top_k: int = 5) -> list[str]:
    memories = db.query(filter={"user_id": user_id})
    sorted_memories = sorted(memories, key=lambda m: m["timestamp"], reverse=True)
    return [m["fact"] for m in sorted_memories[:top_k]]
```

**Why this fails:**

- Returns the 5 most recently stored facts, regardless of relevance.
- User asks "what's my coffee preference?" and gets 5 recent facts about their work schedule, name update, and address.
- The coffee preference fact (stored 3 months ago) is never retrieved.

```python
# Approach B: Just append new facts
def store_memory_v2(user_id: str, fact: str):
    # Just insert the new fact, let retrieval sort it out
    db.insert({"user_id": user_id, "fact": fact, "timestamp": datetime.now()})
```

**Why this fails:** Described in the problem statement — the root cause.

---

## Expert Approach

**Step 1: Semantic deduplication at write time**

Before storing a new fact, search for existing facts that are semantically similar (cosine > 0.9). If found, mark the old fact as superseded and store the new one.

```python
SUPERSEDE_THRESHOLD = 0.90

def store_memory_with_dedup(user_id: str, new_fact: str):
    new_embedding = embed(new_fact)

    # Search for semantically similar existing memories
    similar = db.query(
        filter={"user_id": user_id, "status": "active"},
        vector=new_embedding,
        top_k=3,
        include_similarity=True
    )

    # Supersede memories that are semantically close
    superseded_ids = []
    for memory, similarity in similar:
        if similarity >= SUPERSEDE_THRESHOLD:
            superseded_ids.append(memory["id"])

    # Mark old memories as superseded
    if superseded_ids:
        db.update(
            ids=superseded_ids,
            fields={"status": "superseded", "superseded_by_timestamp": datetime.now().isoformat()}
        )

    # Store new memory
    db.insert({
        "user_id": user_id,
        "fact": new_fact,
        "embedding": new_embedding,
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "supersedes": superseded_ids,
    })
```

**Step 2: Recency-weighted retrieval**

At read time, combine semantic similarity with recency in a single score:

```python
import math
from datetime import datetime, timezone

def recency_score(timestamp_str: str, decay_days: float = 30.0) -> float:
    """
    Exponential decay: recent memories score near 1.0, older ones decay toward 0.
    Half-life = decay_days.
    """
    ts = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - ts).days
    return math.exp(-age_days * math.log(2) / decay_days)

def retrieve_memories_weighted(
    user_id: str,
    query: str,
    top_k: int = 5,
    similarity_weight: float = 0.7,
    recency_weight: float = 0.3,
) -> list[dict]:
    query_embedding = embed(query)

    # Only retrieve active memories
    candidates = db.query(
        filter={"user_id": user_id, "status": "active"},
        vector=query_embedding,
        top_k=top_k * 3,  # retrieve 3x, then rerank
        include_similarity=True,
        include_fields=["fact", "timestamp"]
    )

    # Rerank with combined score
    scored = []
    for memory, similarity in candidates:
        recency = recency_score(memory["timestamp"])
        combined = similarity_weight * similarity + recency_weight * recency
        scored.append((memory, combined))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [{"fact": m["fact"], "score": s} for m, s in scored[:top_k]]
```

**Step 3: Structured memory for known entity types**

For facts that follow predictable patterns (name, email, location, employer), use a structured store with explicit upsert semantics instead of the vector store:

```python
# Structured memory for entities that are definitely singular
STRUCTURED_ENTITY_TYPES = {
    "name": r"(?:my name is|I'm called|call me)\s+(\w+)",
    "email": r"my email is\s+([\w.]+@[\w.]+)",
    "employer": r"I work at\s+(.+?)(?:\.|$)",
    "city": r"I live in\s+(.+?)(?:\.|$)",
}

def extract_structured_fact(text: str) -> tuple[str, str] | None:
    for entity_type, pattern in STRUCTURED_ENTITY_TYPES.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return entity_type, match.group(1).strip()
    return None

def store_fact_smart(user_id: str, fact: str):
    structured = extract_structured_fact(fact)
    if structured:
        entity_type, value = structured
        # Hard upsert: no ambiguity, always latest wins
        structured_db.upsert(
            key=f"{user_id}:{entity_type}",
            value=value,
            updated_at=datetime.now().isoformat()
        )
        # Also store in vector DB for retrieval consistency
    # Always store in vector DB with deduplication
    store_memory_with_dedup(user_id, fact)
```

**Step 4: Periodic consolidation job**

Run a background job weekly to:
1. Find active memories with cosine similarity > 0.85 (near-duplicates that slipped through)
2. Ask the LLM to merge them: "Given these two facts, what is the single most accurate, up-to-date statement?"

```python
async def consolidate_user_memories(user_id: str):
    active_memories = db.get_all(filter={"user_id": user_id, "status": "active"})
    embeddings = [(m, embed(m["fact"])) for m in active_memories]

    # Find near-duplicate pairs
    pairs_to_merge = []
    for i, (mem_a, emb_a) in enumerate(embeddings):
        for j, (mem_b, emb_b) in enumerate(embeddings):
            if i >= j:
                continue
            sim = cosine_similarity(emb_a, emb_b)
            if sim > 0.85:
                pairs_to_merge.append((mem_a, mem_b, sim))

    for mem_a, mem_b, sim in pairs_to_merge:
        merged = await merge_facts_with_llm(mem_a["fact"], mem_b["fact"])
        # Supersede both, store merged
        db.update(ids=[mem_a["id"], mem_b["id"]], fields={"status": "consolidated"})
        store_memory_with_dedup(user_id, merged)
```

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import re
import math
import json
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any
import anthropic
import numpy as np

client = anthropic.Anthropic()

# --- Embedding stub (replace with real embedding model) ---

def embed(text: str) -> list[float]:
    """Stub — use text-embedding-3-small or similar in production."""
    raise NotImplementedError("Replace with real embedding call")

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


# --- In-memory store (replace with vector DB in production) ---

@dataclass
class MemoryEntry:
    id: str
    user_id: str
    fact: str
    embedding: list[float]
    timestamp: str
    status: str = "active"  # active | superseded | consolidated
    supersedes: list[str] = field(default_factory=list)


class InMemoryVectorStore:
    def __init__(self):
        self._store: dict[str, MemoryEntry] = {}
        self._counter = 0

    def insert(self, entry_data: dict) -> str:
        self._counter += 1
        entry_id = f"mem_{self._counter}"
        self._store[entry_id] = MemoryEntry(id=entry_id, **entry_data)
        return entry_id

    def update(self, ids: list[str], fields: dict):
        for entry_id in ids:
            if entry_id in self._store:
                for k, v in fields.items():
                    setattr(self._store[entry_id], k, v)

    def query_active(self, user_id: str, query_embedding: list[float], top_k: int) -> list[tuple[MemoryEntry, float]]:
        active = [e for e in self._store.values()
                  if e.user_id == user_id and e.status == "active"]
        scored = [(e, cosine_similarity(query_embedding, e.embedding)) for e in active]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_all_active(self, user_id: str) -> list[MemoryEntry]:
        return [e for e in self._store.values()
                if e.user_id == user_id and e.status == "active"]


db = InMemoryVectorStore()

SUPERSEDE_THRESHOLD = 0.90
STRUCTURED_PATTERNS = {
    "name": r"(?:my name is|i(?:'m| am) called|call me)\s+(\w+)",
    "email": r"my email (?:is|address is)\s+([\w.]+@[\w.]+)",
    "employer": r"i work (?:at|for)\s+(.+?)(?:\.|,|$)",
    "city": r"i (?:live|am based) in\s+(.+?)(?:\.|,|$)",
}


def extract_structured_fact(text: str) -> tuple[str, str] | None:
    for entity_type, pattern in STRUCTURED_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return entity_type, match.group(1).strip()
    return None


def recency_score(timestamp_str: str, half_life_days: float = 30.0) -> float:
    ts = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
    age_days = max((datetime.now(timezone.utc) - ts).total_seconds() / 86400, 0)
    return math.exp(-age_days * math.log(2) / half_life_days)


def store_memory(user_id: str, fact: str, embedding: list[float]):
    # Semantic deduplication: find similar active memories
    similar = db.query_active(user_id, embedding, top_k=5)
    superseded_ids = [
        m.id for m, sim in similar
        if sim >= SUPERSEDE_THRESHOLD
    ]

    if superseded_ids:
        db.update(superseded_ids, {"status": "superseded"})

    db.insert({
        "user_id": user_id,
        "fact": fact,
        "embedding": embedding,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "supersedes": superseded_ids,
    })


def retrieve_memories(
    user_id: str,
    query_embedding: list[float],
    top_k: int = 5,
    similarity_weight: float = 0.7,
    recency_weight: float = 0.3,
) -> list[dict]:
    # Fetch more candidates, then rerank
    candidates = db.query_active(user_id, query_embedding, top_k=top_k * 3)

    scored = []
    for memory, similarity in candidates:
        recency = recency_score(memory.timestamp)
        combined = similarity_weight * similarity + recency_weight * recency
        scored.append({"fact": memory.fact, "score": combined, "timestamp": memory.timestamp})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


async def merge_facts_with_llm(fact_a: str, fact_b: str) -> str:
    """Ask the LLM to merge two near-duplicate facts into one."""
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"""Two memory entries about the same user are near-duplicates.
Merge them into a single, accurate, up-to-date statement.
If they contradict each other, prefer the information that seems more specific or more recently likely to be true.
Output only the merged fact, nothing else.

Fact A: {fact_a}
Fact B: {fact_b}"""
        }]
    )
    return response.content[0].text.strip()


async def consolidate_memories(user_id: str):
    """Periodic job: find and merge near-duplicate active memories."""
    active = db.get_all_active(user_id)
    if len(active) < 2:
        return

    pairs_to_merge: list[tuple[MemoryEntry, MemoryEntry]] = []
    for i, mem_a in enumerate(active):
        for j, mem_b in enumerate(active):
            if i >= j:
                continue
            sim = cosine_similarity(mem_a.embedding, mem_b.embedding)
            if 0.85 <= sim < SUPERSEDE_THRESHOLD:  # near-duplicate but not caught at write time
                pairs_to_merge.append((mem_a, mem_b))

    for mem_a, mem_b in pairs_to_merge:
        merged_fact = await merge_facts_with_llm(mem_a.fact, mem_b.fact)
        merged_embedding = embed(merged_fact)
        db.update([mem_a.id, mem_b.id], {"status": "consolidated"})
        store_memory(user_id, merged_fact, merged_embedding)
        print(f"Consolidated:\n  '{mem_a.fact}'\n  '{mem_b.fact}'\n  → '{merged_fact}'")


# Demonstration of the fix
def demonstrate_fix():
    user_id = "u_4892"

    # Simulate conversation over time
    facts_over_time = [
        ("2024-01-01", "User's name is Alice"),
        ("2024-01-03", "User prefers dark mode"),
        ("2024-01-15", "User's name is Bob"),  # update — should supersede Alice
        ("2024-01-15", "User works at Acme Corp"),
    ]

    print("=== Storing memories with deduplication ===")
    for timestamp, fact in facts_over_time:
        # In real code, embed() would call an API
        # Here we simulate: name facts get similar embeddings to each other
        print(f"Storing: '{fact}'")
        # store_memory(user_id, fact, embed(fact))  # would call real embed

    print()
    print("=== Expected retrieval behavior ===")
    print("Query: 'What is my name?'")
    print("Expected: 'User's name is Bob' (newest, supersedes Alice)")
    print("With naive approach: 'User's name is Alice' (higher cosine similarity to query)")
    print("With recency weighting: Bob's entry gets combined_score = 0.7*sim + 0.3*1.0")
    print("                        Alice's entry gets combined_score = 0.7*high_sim + 0.3*low_recency")


if __name__ == "__main__":
    demonstrate_fix()
```

**Summary of the four-layer fix:**

| Layer | When | What it does |
|---|---|---|
| Semantic dedup | On write | Supersedes similar existing memories (cosine > 0.9) |
| Structured upsert | On write | Hard override for known entity types (name, email) |
| Recency weighting | On read | Blends similarity (70%) + recency (30%) |
| Consolidation job | Weekly | Merges near-duplicates that slipped through |

</details>

---

## Interview Version

**Opening (20 seconds):** "Pure vector similarity retrieves the most *similar* memory, not the most *current* one. For documents that's fine. For mutable facts about a person, it's a bug. We need semantic deduplication at write time and recency weighting at read time."

**Draw the two failure modes:**

```
Write time (no dedup):
  Jan 1:  store("name is Alice")  → memory #1
  Jan 15: store("name is Bob")   → memory #2  ← both exist, #1 has higher sim to "what's my name?"

Read time (pure similarity):
  query("what is my name?")
  → retrieves "name is Alice" (higher cosine similarity due to exact phrasing overlap)
  → correct answer (Bob) is buried
```

**Draw the fix:**

```
Write time with dedup:
  Jan 1:  store("name is Alice") → memory #1, active
  Jan 15: check similar → memory #1 has cosine 0.95 > threshold
         → mark #1 as superseded
         → store("name is Bob") → memory #2, active

Read time with recency weight:
  combined_score = 0.7 * cosine_sim + 0.3 * recency_score
  → recent Bob entry wins even if Alice's raw similarity is slightly higher
```

**Key insight:** "The structured memory store is the most robust layer for known entity types. If you know 'name' is always singular, model it as a key-value with upsert semantics, not a vector DB entry. Use vector DB for unstructured facts where you don't know the schema."

---

## Follow-up Questions

1. A user says "My name was Alice before I got married, now it's Bob." Your deduplication would supersede the Alice memory. But what if the user later asks "What was my name before?" — how would you preserve both memories while still returning Bob as the current name?
2. Your recency decay function has a half-life of 30 days. A user's email address was stored 90 days ago and hasn't been mentioned since. Your system's recency score for that memory is 0.125. Is this the right behavior? What's the risk of too-aggressive decay for stable facts?
3. The consolidation job uses an LLM to merge near-duplicate memories. Give two examples of near-duplicate memory pairs where LLM merging could go wrong (produce a worse result than keeping both), and describe a safer alternative for those cases.
