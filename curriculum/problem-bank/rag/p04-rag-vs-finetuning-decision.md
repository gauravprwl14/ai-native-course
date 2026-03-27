# RAG vs Fine-Tuning: The Decision Framework

**Category:** rag
**Difficulty:** Medium
**Key Concepts:** RAG vs fine-tuning trade-offs, knowledge vs behavior, dynamic vs static knowledge, model selection
**Time:** 25–35 min

---

## Problem Statement

You're building an AI assistant for a prestigious legal firm. The system needs to:

1. **Access 50,000 internal documents:** memos, case notes, legal briefs, and research spanning 10 years
2. **Write like the firm:** senior partners have a specific style — formal but precise, citation-heavy, structured arguments that follow a particular logical flow the firm calls "the Mercer method"
3. **Reason about precedents:** when a new client matter arises, the assistant should connect it to past cases and reason through applicability the way a senior partner would

The managing partner asks in a planning meeting: "Should we RAG these documents or fine-tune on them? We have budget for one, not both."

**Your answer is "both — but for different reasons, and the budget framing is wrong." Explain the decision framework.**

---

## What Makes This Hard

This problem looks like a resource allocation question ("which one should we pick?") but is actually a **conceptual architecture question** ("these tools serve fundamentally different purposes").

The trap: both RAG and fine-tuning involve training data and an LLM, so they feel like competing approaches to the same problem. They are not. They solve different classes of problems:

- **RAG solves a knowledge problem:** the model does not have this information
- **Fine-tuning solves a behavior problem:** the model does not act this way

A candidate who treats this as an either/or trade-off has not understood the distinction. The firm needs both, but fine-tuning on 50,000 documents is the wrong use of fine-tuning — and RAG cannot replicate learned reasoning style. Getting the allocation right requires understanding what each tool actually does.

---

## Naive Approach

**Option A: RAG everything**

Index all 50,000 documents, use a strong base model (GPT-4o), and include retrieved context with a system prompt saying "write like a senior partner."

**Why it fails:**
- Style and reasoning patterns cannot be reliably conveyed through a system prompt alone. "Write like a senior partner" is ambiguous. The model has no examples of what "the Mercer method" looks like.
- Retrieved context helps with facts but does not show the model how to reason through them. The style of logical progression — how arguments are sequenced, how precedents are cited, how uncertainty is qualified — is behavioral, not factual.
- Result: a technically correct answer in generic legal language, not in the firm's voice.

**Option B: Fine-tune on the 50,000 documents**

Use all 50,000 documents as fine-tuning data to teach the model about the firm's cases and style simultaneously.

**Why it fails:**
- Fine-tuning on 50,000 documents is computationally expensive (thousands of dollars) and trains the model to reproduce text patterns, not to retrieve facts accurately.
- Fine-tuned models are known to **confabulate fine-tuned facts confidently** — the model "remembers" training data imperfectly and will generate plausible-sounding but incorrect case details.
- The 10-year knowledge base will become stale. Fine-tuned facts cannot be updated without re-training. Every new case added to the knowledge base requires another fine-tuning run.
- Fine-tuning with 50,000 documents to "teach the style" buries the style signal in an enormous amount of factual noise.

---

## Expert Approach

### The Core Distinction

| Dimension | RAG | Fine-Tuning |
|---|---|---|
| What it solves | Knowledge (facts, documents, data) | Behavior (style, tone, reasoning patterns, output format) |
| Knowledge updates | Index a new document: near-instant | Re-train the model: hours + significant cost |
| Knowledge accuracy | High (cites sources, attributable) | Lower (model interpolates, may confabulate) |
| Behavior consistency | Inconsistent (depends on prompt) | High (baked into weights) |
| Data requirements | Any document corpus | 100–1,000 high-quality labeled examples |
| When to use | Facts change, volume is large, attribution matters | Behavior is consistent, style is learnable, good examples exist |

### The Right Architecture for This Firm

**Use RAG for the 50,000 documents.** This is the correct tool because:
- The knowledge base is large and will grow
- Accuracy and attribution matter (legal work requires citing sources)
- Documents will be updated as cases evolve
- You can retrieve only the 5–10 most relevant documents per query, keeping latency and cost manageable

**Use fine-tuning for the behavioral layer.** This is the correct tool because:
- "The Mercer method" is a learned behavior, not a fact — it cannot be retrieved
- You only need 100–500 high-quality examples, not 50,000
- Style is consistent across all queries, not context-dependent
- Fine-tuning bakes the behavior into the model weights so it requires no prompt engineering per query

**Combine them in production:**

```
User query: "Analyze this contract clause for arbitration risk"
         |
         v
RAG Retrieval: fetch 5 most relevant precedents from 50,000 docs
         |
         v
Fine-tuned model: synthesize analysis in the firm's voice and structure
         |
         v
Output: a memo that sounds like it was written by a senior partner,
        citing specific precedents from the firm's history
```

### What NOT to Fine-Tune

1. **Specific case facts and dates** — These are retrieval problems. A fine-tuned model will generate plausible but wrong case details ("the Smith v. Mercer ruling established..." when no such case exists).
2. **Frequently changing information** — Any legal standard, regulation, or precedent that updates cannot be corrected without re-training.
3. **Low-frequency edge cases** — Fine-tuning optimizes for patterns seen repeatedly. Rare scenarios will be handled poorly and fail silently.
4. **Anything that must be auditable** — If a client asks "why did you recommend this approach?", a RAG system can cite the retrieved document. A fine-tuned behavior cannot be explained in terms of specific training examples.

### The Budget Reframe

The managing partner's premise — "one or the other" — is based on conflating the costs:

| Task | Approach | Cost Estimate |
|---|---|---|
| Index 50,000 documents | RAG (one-time embedding) | ~$25 (at $0.0001/1K tokens, avg 500 tokens/doc) |
| Index updates (50 new docs/month) | Delta RAG | ~$0.25/month |
| Fine-tune on 200 style examples | Fine-tune GPT-3.5 or Llama 3 | $50–200 one-time |
| Inference (RAG + fine-tuned model) | Per query | ~$0.01–0.05/query |

The RAG indexing cost is trivially low. Fine-tuning on 200 examples is a one-time investment. The "either/or" framing was based on a misunderstanding of what the costs actually are.

**The real cost question** is inference cost at scale — which is a query volume problem, not an architecture choice problem.

### Decision Matrix

```
Does the system need to know specific facts that change over time?
    YES → RAG (mandatory)
    NO  → Base model knowledge may be sufficient

Does the system need to produce output in a specific style or format?
    YES → Fine-tuning (or few-shot prompting if examples are < 5)
    NO  → Prompt engineering is sufficient

Does the system need to reason through problems in a learned pattern?
    YES → Fine-tuning (if you have 100+ labeled examples of that reasoning)
    NO  → RAG + strong system prompt

Is the knowledge corpus > 100 documents?
    YES → RAG (fine-tuning cannot reliably memorize 100+ documents)
    NO  → Consider few-shot examples in context before fine-tuning
```

---

## Solution

<details>
<summary>Show Solution</summary>

### Implementation Plan

**Phase 1: RAG for the knowledge base (Week 1–2)**

```python
# Index the 50,000 documents
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter

def build_legal_rag_index(documents: list[dict]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,         # Legal text: larger chunks preserve sentence structure
        chunk_overlap=100,
        separators=["\n\n", "\n", ". "],
    )

    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    all_chunks = []
    for doc in documents:
        chunks = splitter.create_documents(
            [doc["content"]],
            metadatas=[{
                "doc_id": doc["id"],
                "doc_type": doc["type"],  # "memo" | "case_note" | "brief"
                "date": doc["date"],
                "matter_id": doc.get("matter_id"),
                "authors": doc.get("authors", []),
            }]
        )
        all_chunks.extend(chunks)

    vector_store = Pinecone.from_documents(all_chunks, embeddings, index_name="legal-kb")
    return vector_store
```

**Phase 2: Fine-tuning on style examples (Week 2–3)**

```python
# Fine-tuning dataset: 200 examples of senior partner outputs
# Format: input = matter description + retrieved context, output = partner-style analysis

fine_tuning_examples = [
    {
        "messages": [
            {"role": "system", "content": "You are a senior partner at [Firm]. Apply the Mercer method."},
            {"role": "user", "content": "Analyze the arbitration clause in the following contract: [context]"},
            {"role": "assistant", "content": "[Example of a Mercer-method analysis: structured, citation-heavy, formal]"}
        ]
    },
    # ... 199 more examples
]

# Fine-tune on GPT-3.5-turbo or an open-source model (Llama 3 8B)
# Expected cost: $50–150 for 200 examples on GPT-3.5
```

**Phase 3: Combined inference pipeline**

```python
def legal_assistant_query(user_query: str, matter_context: dict) -> str:
    # Step 1: RAG — retrieve relevant precedents and documents
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    relevant_docs = retriever.get_relevant_documents(user_query)

    # Step 2: Format context for the fine-tuned model
    context = format_legal_context(relevant_docs)

    # Step 3: Fine-tuned model produces output in firm's style
    response = fine_tuned_client.chat.completions.create(
        model="ft:gpt-3.5-turbo:firm-mercer-method",
        messages=[
            {"role": "system", "content": MERCER_METHOD_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context from firm precedents:\n{context}\n\nQuery: {user_query}"},
        ]
    )

    return response.choices[0].message.content
```

### Quick Reference: When to Use Each

**Use RAG when:**
- Knowledge base > 50 documents
- Documents change or grow over time
- Attribution/source citation is required
- Facts must be accurate (legal, medical, financial domains)

**Use fine-tuning when:**
- You have 100–1,000 high-quality labeled input/output examples
- The target behavior is consistent (not context-dependent)
- You want to reduce prompt length (bake behavior into weights)
- Latency matters and you can eliminate system prompt overhead

**Use both when (most production systems):**
- You need both factual accuracy and consistent style
- The system operates in a professional domain with a specific voice
- The knowledge base is large but the behavioral examples are few

</details>

---

## Interview Version

"A legal firm asks: should we RAG our 50,000 documents or fine-tune on them? What do you recommend?"

**Start with the clarifying reframe:**
"These tools solve different problems. The question I'd ask first is: what's failing — does the model not know something, or does it not act the right way?"

**Draw the decision framework:**
```
Problem: model doesn't know facts → RAG
Problem: model doesn't behave correctly → Fine-tuning
Problem: both → Both (usually much cheaper than expected)
```

**Then walk through this specific case:**
- 50,000 docs: RAG (too large to fine-tune reliably, needs to stay current)
- "Mercer method": fine-tuning (200 examples of the desired behavior)
- Combined: RAG retrieves precedents, fine-tuned model synthesizes in firm's voice

**Close with the budget reframe:**
"Indexing 50,000 documents costs about $25. Fine-tuning on 200 style examples costs about $100. The 'one or the other' premise was based on a misunderstanding of costs."

---

## Follow-up Questions

1. After deploying the fine-tuned model, the firm hires three new senior partners who have a different writing style. The managing partner wants the system to "learn" the new partners' style. How do you update the fine-tuned model without losing the original training, and how do you handle the style conflict between old and new partners?
2. A junior associate uses the assistant to draft a brief. The assistant cites a specific precedent from the firm's internal database that the associate cannot verify. The associate submits the brief and the precedent does not exist — the model hallucinated a case name while correctly retrieving the legal principle. How do you redesign the system to prevent hallucinated citations?
3. The firm wants to expand the assistant to a second jurisdiction (UK law) where the reasoning style and citation conventions are completely different. They have 5,000 UK documents and 50 examples of UK-style briefs. How do you architect the system to handle both jurisdictions without training separate models?
