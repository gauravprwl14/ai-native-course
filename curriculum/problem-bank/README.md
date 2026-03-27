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
| [p04-structured-output-validation.md](prompting/p04-structured-output-validation.md) | **Structured Output Validation** — LLM extracts JSON from medical records. 8% of responses are invalid (markdown fences, truncation, wrong schema). Fix without switching models. | Medium | structured output, JSON mode, retry loops, output parsing, tool use | 20–35 min |
| [p05-context-window-management.md](prompting/p05-context-window-management.md) | **Context Window Management** — After 20+ turns, coding assistant "forgets" requirements from turn 1. Context is 45k tokens — well under the 200k limit. Why, and how do you fix it? | Hard | attention dilution, context compression, conversation summarization, memory management | 30–45 min |

### Agents

| File | Problem | Difficulty | Key Concepts | Time |
|------|---------|------------|--------------|------|
| [p01-tool-call-loop.md](agents/p01-tool-call-loop.md) | **Tool Call Loop** — Agent costs $0.12/request instead of $0.02. It loops search→parse→search forever. Fix it without breaking legitimate long tasks. | Hard | agent loop control, tool call budget, convergence detection, max iterations guard | 30–45 min |
| [p02-parallel-tool-race-condition.md](agents/p02-parallel-tool-race-condition.md) | **Parallel Tool Race Condition** — Parallelized tool execution causes 0.3% of requests to return inconsistent state. Fix it without serializing everything. | Expert | tool execution ordering, read-after-write consistency, tool dependency graph, optimistic vs pessimistic concurrency | 35–45 min |
| [p03-memory-poisoning.md](agents/p03-memory-poisoning.md) | **Memory Poisoning** — Agent with long-term memory gives contradictory answers. Vector search returns "name is Alice" even though user updated to "Bob" two weeks ago. | Expert | memory versioning, recency vs relevance trade-off, memory consolidation, semantic deduplication | 35–45 min |
| [p04-agent-cost-explosion.md](agents/p04-agent-cost-explosion.md) | **Agent Cost Explosion** — Monthly bill is $12k instead of $3k. 2% of requests cost $4–12 each; 98% cost $0.05. All runaway requests loop before hitting max_iterations=50. Fix without breaking legitimate long tasks. | Hard | cost attribution, per-request budget, circuit breaker, anomaly detection | 35–45 min |
| [p05-human-in-loop-at-scale.md](agents/p05-human-in-loop-at-scale.md) | **Human-in-the-Loop at Scale** — Agent handles 500 requests/day. One reviewer can't keep up. Redesign HITL with 3 reviewers, no duplicate approvals, and guaranteed 10-minute SLA. | Expert | HITL architecture, work queue, escalation, SLA, async workflows | 40–45 min |

### RAG

| File | Problem | Difficulty | Key Concepts | Time |
|------|---------|------------|--------------|------|
| [p01-chunk-boundary-problem.md](rag/p01-chunk-boundary-problem.md) | **Chunk Boundary Problem** | — | chunking, retrieval quality | — |
| [p02-retrieval-freshness.md](rag/p02-retrieval-freshness.md) | **Retrieval Freshness** | — | freshness, indexing, recency | — |
| [p03-multi-tenant-isolation.md](rag/p03-multi-tenant-isolation.md) | **Multi-Tenant Isolation** | — | multi-tenancy, access control, RAG | — |
| [p04-rag-vs-finetuning-decision.md](rag/p04-rag-vs-finetuning-decision.md) | **RAG vs Fine-tuning Decision** | — | RAG, fine-tuning, model selection | — |
| [p05-embedding-model-mismatch.md](rag/p05-embedding-model-mismatch.md) | **Embedding Model Mismatch** — 2M docs indexed with ada-002. Company wants to switch to text-embedding-3-large. What's wrong with indexing new docs in the new model while leaving old docs as-is? Design the migration. | Hard | embedding model versioning, mixed-model index, re-indexing strategy, semantic space alignment | 30–45 min |

### System Design

| File | Problem | Difficulty | Key Concepts | Time |
|------|---------|------------|--------------|------|
| [p01-production-rag-at-scale.md](system-design/p01-production-rag-at-scale.md) | **Production RAG at Scale** | — | RAG, scalability, production | — |
| [p02-multi-model-agent-system.md](system-design/p02-multi-model-agent-system.md) | **Multi-Model Agent System** | — | multi-model, orchestration | — |
| [p03-streaming-agent-ux.md](system-design/p03-streaming-agent-ux.md) | **Streaming Agent UX** | — | streaming, UX, latency | — |
| [p04-eval-driven-development.md](system-design/p04-eval-driven-development.md) | **Eval-Driven Development** — Safe system prompt deployment with regression testing, shadow deployment, and auto-rollback | Hard | LLM evals, A/B testing, regression testing, shadow deployment | 35–45 min |
| [p05-llm-gateway-fallback.md](system-design/p05-llm-gateway-fallback.md) | **LLM Gateway Fallback** — Anthropic has a 45-minute outage; 8,000 users can't use your app. Design a multi-provider fallback with <2s overhead for the 99.9% healthy case and zero-latency failover. | Expert | multi-provider gateway, circuit breaker, fallback routing, provider health checks, latency vs reliability trade-off | 40–45 min |
