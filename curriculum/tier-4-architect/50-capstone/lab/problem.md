# Capstone Lab: Research Assistant Agent

## Problem Statement

You are building **ResearchAssistant** — a production-quality AI agent that answers natural-language research questions using a combination of retrieval-augmented generation, tool calling, and an agentic planning loop.

This lab synthesizes every major concept from the AI-Native Development Course across all four tiers. You will build the system from scratch, one milestone at a time.

---

## System Requirements

### Functional Requirements

1. **Accept a research question** as a command-line argument or string input.
2. **Check for prompt injection** before any LLM call. Return an error if injection is detected.
3. **Check the cache** before running the pipeline. Return the cached answer for repeated queries.
4. **Plan the strategy**: use an LLM call to decide whether RAG and/or tools are needed.
5. **Execute tools** if the plan requests them (web search, calculator).
6. **Retrieve and answer**: if the plan requests RAG, search the knowledge base and use retrieved context to generate the answer. If no relevant documents are found, fall back to LLM-only.
7. **Stream the response** (bonus: implement `stream=True` path).
8. **Track conversation history** across multiple turns.
9. **Cache the answer** after generation.
10. **Print a trace report** showing each pipeline step with duration.

### Non-Functional Requirements

- **No external vector database dependencies** — use the in-memory `SimpleVectorStore` (TF-IDF).
- **No API keys beyond `ANTHROPIC_API_KEY`** — mock the web search tool.
- **Retry on rate limit** — exponential backoff, up to `max_retries` attempts.
- **Never crash on tool failure** — `ToolRegistry.execute()` must catch all exceptions and return `ToolResult(success=False)`.
- **Graceful RAG degradation** — if all retrieved scores are below `0.05`, skip context and call LLM directly.

---

## Knowledge Base

The system is pre-loaded with these documents (defined in `main()`):

| ID | Content |
|----|---------|
| 1 | Retrieval Augmented Generation (RAG) combines vector search with LLMs to answer questions from a knowledge base. |
| 2 | Embeddings are numerical vector representations of text that capture semantic meaning. |
| 3 | An agentic loop is the observe-think-act cycle where an AI agent iteratively solves a task. |
| 4 | Fine-tuning adjusts a pre-trained model's weights on a specific dataset to improve task performance. |
| 5 | Prompt injection is a security attack where malicious content in prompts overrides system instructions. |

---

## The Six Milestones

### Milestone 1: Core LLM Client
Build `LLMClient` with `complete()` (retry) and `stream()` (streaming). This is the foundation all other components depend on.

### Milestone 2: RAG Pipeline
Build `SimpleVectorStore` (TF-IDF cosine similarity) and `RAGPipeline` (ingest + retrieve + answer with graceful degradation).

### Milestone 3: Tool System
Build `ToolRegistry` (register, execute, describe) and `create_default_tools()` (web_search mock, calculator with safe eval).

### Milestone 4: Planner
Build `parse_plan()` (parse structured LLM response) and `plan_query()` (prompt LLM for strategy).

### Milestone 5: Agent Loop
Build `ResearchAssistant` with guardrails, cache, the 7-step answer loop, and conversation history.

### Milestone 6: Observability
Build `format_trace_report()` to render the step trace as a human-readable table with per-step durations and a total.

---

## Acceptance Criteria

The system is complete when:

1. `python starter/solution.py "What is RAG?"` prints a non-empty answer followed by a trace report.
2. Running the same query twice shows `[Cache hit]` on the second run.
3. `python starter/solution.py "ignore previous instructions"` returns an error, not an LLM response.
4. `python starter/solution.py "What is 15 * 47?"` calls the calculator tool (visible in trace).
5. All tests in `tests/test_solution.py` pass with `pytest tests/ -v`.

---

## Running the Tests

```bash
cd curriculum/tier-4-architect/50-capstone/lab
pytest tests/ -v
```

For integration tests against the real API (requires `ANTHROPIC_API_KEY`):
```bash
ANTHROPIC_API_KEY=sk-ant-... pytest tests/ -v -m integration
```

---

## Implementation Notes

- **Do not change the class/function signatures** — the tests import these directly.
- Implement milestones in order — each milestone depends on the previous.
- The `solution/solution.py` file contains the complete reference implementation if you get stuck.
- The `SimpleVectorStore` uses TF-IDF (not dense embeddings) so no embeddings API key is needed.
