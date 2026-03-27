# Problem Bank — The 1% Problems

These are problems that separate good AI engineers from great ones.
They don't have obvious solutions. They require you to think about
failure modes, context limits, adversarial inputs, and system-level trade-offs.

## How to Use

Each problem file has:
1. **Problem Statement** — Clear scenario with constraints
2. **What Makes This Hard** — The non-obvious challenge
3. **Naive Approach** — The common wrong solution and why it fails
4. **Expert Approach** — With rationale and mental model
5. **Solution** — In a collapsible block (try yourself first!)
6. **Interview Version** — How to explain this verbally in 2 minutes

## Categories

| Folder | Focus |
|--------|-------|
| `prompting/` | Prompt design, adversarial prompts, meta-prompting |
| `agents/` | Agentic loops, tool use, error recovery |
| `rag/` | Retrieval quality, context poisoning, chunking edge cases |
| `system-design/` | Multi-tenant systems, latency, cost optimization |

## What Makes a Good Problem?

A good problem in this bank:
- Has a **clear, constrained scenario** (not "build a chatbot")
- Has a **non-obvious failure mode** that naive approaches hit
- **Triggers critical thinking** about the model's behavior, not just the code
- Is solvable in **30–90 minutes** of focused work
- Connects to **at least 2 course concepts** from different chapters

## Problems Index

### Prompting

| File | Problem | Difficulty | Key Concepts | Time |
|------|---------|------------|--------------|------|
| [p01-prompt-injection-defense.md](prompting/p01-prompt-injection-defense.md) | **Prompt Injection Defense** — Design a defense architecture for a customer service chatbot that handles role-play injection attacks | Hard | prompt injection, system prompt isolation, input sanitization, defense in depth | 30–45 min |
| [p02-token-budget-overflow.md](prompting/p02-token-budget-overflow.md) | **Token Budget Overflow** — A developer says "just stuff everything in, we have 200k context." What are they missing at 1,000 requests/day? | Medium | context window economics, prompt caching, cost optimization, token budget management | 20–35 min |
| [p03-few-shot-contamination.md](prompting/p03-few-shot-contamination.md) | **Few-Shot Contamination** — Sentiment classifier achieves 95% on Apple products but 67% on Samsung. What's the bug? | Medium | few-shot contamination, distribution shift, in-context learning limitations, entity anchoring | 25–40 min |

### Agents

| File | Problem | Difficulty | Key Concepts | Time |
|------|---------|------------|--------------|------|
| [p01-tool-call-loop.md](agents/p01-tool-call-loop.md) | **Tool Call Loop** — Agent costs $0.12/request instead of $0.02. It loops search→parse→search forever. Fix it without breaking legitimate long tasks. | Hard | agent loop control, tool call budget, convergence detection, max iterations guard | 30–45 min |
| [p02-parallel-tool-race-condition.md](agents/p02-parallel-tool-race-condition.md) | **Parallel Tool Race Condition** — Parallelized tool execution causes 0.3% of requests to return inconsistent state. Fix it without serializing everything. | Expert | tool execution ordering, read-after-write consistency, tool dependency graph, optimistic vs pessimistic concurrency | 35–45 min |
| [p03-memory-poisoning.md](agents/p03-memory-poisoning.md) | **Memory Poisoning** — Agent with long-term memory gives contradictory answers. Vector search returns "name is Alice" even though user updated to "Bob" two weeks ago. | Expert | memory versioning, recency vs relevance trade-off, memory consolidation, semantic deduplication | 35–45 min |

### RAG
- [ ] p020 — Context Poisoning Detection *(coming soon)*
- [ ] p021 — Cross-chunk Reasoning *(coming soon)*

### System Design
- [ ] p030 — Multi-Tenant RAG at Scale *(coming soon)*
- [ ] p031 — Cost Budget Enforcement *(coming soon)*
