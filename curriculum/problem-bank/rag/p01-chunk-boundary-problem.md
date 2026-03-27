# The Chunk Boundary Problem

**Category:** rag
**Difficulty:** Medium
**Key Concepts:** chunk overlap, semantic chunking, recursive text splitter, parent-child retrieval
**Time:** 20–30 min

---

## Problem Statement

Your RAG pipeline answers "What are the payment terms?" correctly in testing but fails in production.

Investigation reveals the following text in the source contract PDF:

> "Payment Terms: Net 30. For international orders, see Appendix C. International clients are invoiced in USD with Net 60 terms and a 2% processing fee."

Your chunker split this as:

- **Chunk A** (page 4): `"...Payment Terms: Net 30."`
- **Chunk B** (page 7): `"For international orders, see Appendix C. International clients are invoiced in USD with Net 60 terms..."`

When a user asks "What are payment terms for international orders?", retrieval returns Chunk A (highest cosine similarity to "payment terms") — which says Net 30. The bot confidently gives the wrong answer. A sales rep sends an incorrect quote.

**How do you fix this — without bloating your index or retrieval cost?**

---

## What Makes This Hard

Chunk overlap is the obvious fix — and it is partially correct — but it does not solve the root problem. The issue is not that chunks are too small. The issue is that the document's logical structure (a policy that references another section) was destroyed by character-count-based splitting.

Adding overlap to every chunk:
- Increases total tokens in the index (cost and latency go up)
- Still fails when references span many pages ("see Appendix C" is 3 words pointing to content 3 pages away)
- Does not help retrieval ranking — Chunk A still scores higher for "payment terms" even with overlap

The real challenge is recognizing this as a **document structure problem**, not a chunk size problem.

---

## Naive Approach

**Add 20% chunk overlap to the RecursiveCharacterTextSplitter.**

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100  # 20% overlap
)
```

**Why it fails:**

1. Overlap only helps for adjacent chunks. When the cross-reference spans pages (Chunk A on page 4, Appendix C on page 7), the overlap window never bridges the gap.
2. Even when overlap does catch the split, it duplicates content across many chunks. A 10,000-document corpus with 20% overlap means ~12,000 effective chunks — 20% more embedding cost forever.
3. Retrieval ranking is unchanged. Chunk A still wins for "payment terms" queries because it contains the exact phrase. Overlap does not fix the ranking problem.
4. Long sentences that happen to straddle a boundary still get cut mid-sentence if the sentence is longer than the overlap window.

**The failure mode:** You think you fixed it (overlap looks reasonable), you ship it, and the same class of cross-reference bugs keeps appearing in different documents.

---

## Expert Approach

Three complementary fixes, applied in order of impact:

### 1. Structure-Aware Chunking (Fix the split)

Do not split on raw character count. Split on document structure first.

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

# For PDFs: extract headers/section titles first
headers_to_split_on = [
    ("#", "section"),
    ("##", "subsection"),
]

splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
sections = splitter.split_text(document_text)

# Now apply character-level splitting WITHIN each section
from langchain.text_splitter import RecursiveCharacterTextSplitter
char_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

chunks = []
for section in sections:
    sub_chunks = char_splitter.split_documents([section])
    chunks.extend(sub_chunks)
```

Key principle: a cross-reference like "see Appendix C" means Appendix C should be indexed with metadata linking it back to the referring section. You need to detect and model these links, not hope overlap catches them.

### 2. Parent-Child Retrieval (Fix the context passed to LLM)

Use small chunks for retrieval precision, large parent chunks for LLM context.

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.vectorstores import Chroma

# Small chunks for retrieval (high precision)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)

# Large chunks passed to the LLM (full context)
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)

vectorstore = Chroma(embedding_function=embeddings)
store = InMemoryStore()

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)
```

When Chunk A (small, 200 tokens) is retrieved, the system returns its parent (2000 tokens), which likely includes both the Net 30 clause and the international order reference in the same window.

### 3. Chunk Metadata Enrichment (Fix retrieval ranking)

Tag every chunk with structural metadata so you can boost or filter at query time.

```python
def enrich_chunk_metadata(chunk, doc_structure):
    return {
        **chunk.metadata,
        "section_header": doc_structure.get_section_header(chunk),
        "page_number": doc_structure.get_page(chunk),
        "preceding_header": doc_structure.get_preceding_header(chunk),
        "cross_references": doc_structure.extract_see_also_links(chunk),
        # e.g. ["Appendix C"] — enables graph-based retrieval
    }
```

At query time, if a retrieved chunk contains a cross-reference (`"see Appendix C"`), automatically fetch the referenced section and include it in the LLM context.

---

## Solution

<details>
<summary>Show Solution</summary>

### Full Implementation

```python
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

@dataclass
class StructuredChunk:
    content: str
    section: str
    page: int
    parent_id: str
    cross_references: List[str]

def extract_sections_from_pdf(pdf_text: str) -> List[Dict]:
    """Split on section headers, not character count."""
    # Regex for common contract section patterns
    section_pattern = re.compile(
        r'^(#{1,3}\s+.+|[A-Z][A-Z\s]+:|Section \d+\.?\d*\s+[A-Z])',
        re.MULTILINE
    )

    sections = []
    matches = list(section_pattern.finditer(pdf_text))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(pdf_text)
        sections.append({
            "header": match.group().strip(),
            "content": pdf_text[start:end].strip(),
            "start_char": start,
        })

    return sections

def detect_cross_references(text: str) -> List[str]:
    """Find 'see Section X', 'see Appendix Y' patterns."""
    patterns = [
        r'see (Appendix [A-Z])',
        r'see (Section \d+\.?\d*)',
        r'refer to (Appendix [A-Z])',
        r'detailed in (Appendix [A-Z])',
    ]
    refs = []
    for pattern in patterns:
        refs.extend(re.findall(pattern, text, re.IGNORECASE))
    return refs

def build_smart_index(documents: List[str]) -> tuple:
    """Build index with structure-aware chunking and parent-child retrieval."""
    embeddings = OpenAIEmbeddings()

    all_child_chunks = []
    parent_map = {}  # parent_id -> full section text

    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30,  # minimal overlap — structural splits do the heavy lifting
        separators=["\n\n", "\n", ". ", " "],
    )

    for doc_id, doc_text in enumerate(documents):
        sections = extract_sections_from_pdf(doc_text)

        for section in sections:
            parent_id = f"doc_{doc_id}_section_{section['header'][:30]}"
            parent_map[parent_id] = section["content"]

            # Create small child chunks within each section
            child_docs = char_splitter.create_documents(
                [section["content"]],
                metadatas=[{
                    "parent_id": parent_id,
                    "section_header": section["header"],
                    "doc_id": doc_id,
                    "cross_references": detect_cross_references(section["content"]),
                }]
            )
            all_child_chunks.extend(child_docs)

    vectorstore = Chroma.from_documents(all_child_chunks, embeddings)
    return vectorstore, parent_map

def smart_retrieve(query: str, vectorstore, parent_map: Dict, k: int = 5) -> List[str]:
    """Retrieve child chunks, return parent context + resolve cross-references."""
    child_results = vectorstore.similarity_search(query, k=k)

    context_parts = []
    fetched_parents = set()

    for chunk in child_results:
        parent_id = chunk.metadata["parent_id"]

        # Return parent (large context), not child (small retrieval chunk)
        if parent_id not in fetched_parents:
            context_parts.append(parent_map[parent_id])
            fetched_parents.add(parent_id)

        # Auto-resolve cross-references
        for ref in chunk.metadata.get("cross_references", []):
            ref_parent_id = find_section_by_name(ref, parent_map)
            if ref_parent_id and ref_parent_id not in fetched_parents:
                context_parts.append(parent_map[ref_parent_id])
                fetched_parents.add(ref_parent_id)

    return context_parts

def find_section_by_name(section_name: str, parent_map: Dict) -> Optional[str]:
    """Find a parent section ID by name (e.g., 'Appendix C')."""
    for parent_id in parent_map:
        if section_name.lower() in parent_id.lower():
            return parent_id
    return None
```

### Key Decision Points

| Scenario | Fix |
|---|---|
| Cross-reference spans 1–2 sentences | Chunk overlap (50–100 tokens) is sufficient |
| Cross-reference spans sections/pages | Parent-child retrieval is required |
| Cross-reference is a "see Appendix X" pointer | Auto-resolve at retrieval time |
| Retrieval returns wrong section despite good query | Check section metadata; boost by header match |

</details>

---

## Interview Version

"Imagine a contract PDF where the answer to a user's question is split across two chunks — one chunk says 'Net 30' and a second chunk three pages later explains international payment terms. Your retrieval always returns the first chunk because it has higher similarity to 'payment terms'. How do you fix it?"

**Draw on whiteboard:**
```
[Document]
  └── Section: Payment Terms (page 4)
        └── Child chunk A: "Net 30"  ← retrieval finds this
        └── Parent chunk: "Net 30. For international, see Appendix C"

  └── Section: Appendix C (page 7)
        └── Full international terms
```

**Structure your answer:**
1. Diagnose: this is a document structure problem, not a chunk size problem
2. Fix the split: structure-aware chunking (split on sections, not characters)
3. Fix the context: parent-child retrieval (small chunks for retrieval, large parents for LLM)
4. Fix cross-references: detect "see Appendix X" patterns, auto-fetch linked sections

**Avoid saying:** "I'd just add more overlap." — That shows you understand the symptom but not the cause.

---

## Follow-up Questions

1. How would you handle a document where sections are not marked by headers — for example, a dense legal contract with no clear formatting? What signals could you use to detect logical boundaries?
2. The parent-child retrieval strategy increases the tokens sent to the LLM. At what point does the increased context cost outweigh the retrieval precision benefit, and how would you measure it?
3. A cross-reference says "see our updated pricing at pricing.example.com". The referenced content is external, not in your corpus. How do you handle dynamic external references in a RAG system?
