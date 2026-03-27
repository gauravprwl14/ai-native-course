"""
Capstone Lab: Research Assistant Agent

A complete AI system that demonstrates all major concepts from the course:
- RAG pipeline (Tier 2)
- Tool use / function calling (Tier 2)
- Agentic loop with planning (Tier 2-3)
- Streaming responses (Tier 2)
- Guardrails (Tier 3)
- Observability / tracing (Tier 3)
- Caching (Tier 4)
- Graceful degradation (Tier 4)

Usage:
    python solution.py "What is retrieval augmented generation?"
"""
import sys
import time
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Iterator, Callable, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

# ============================================================
# MILESTONE 1: Core LLM Client
# ============================================================

@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str

@dataclass
class StreamChunk:
    text: str
    done: bool

class LLMClient:
    """Thin wrapper around Anthropic API with retry logic."""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", max_retries: int = 3):
        self.model = model
        self.max_retries = max_retries

    def complete(self, messages: list[Message], system: str = "", max_tokens: int = 1024) -> str:
        """Single-shot completion. Returns full response text."""
        # TODO: Import anthropic
        # TODO: Create client: anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        # TODO: Convert messages to anthropic format:
        #       [{"role": m.role, "content": m.content} for m in messages]
        # TODO: Wrap in a for loop: for attempt in range(self.max_retries):
        # TODO:   Call client.messages.create(model=self.model, max_tokens=max_tokens,
        #                                     system=system, messages=fmt_messages)
        # TODO:   Return response.content[0].text on success
        # TODO:   On anthropic.RateLimitError: time.sleep(2 ** attempt), then continue
        # TODO: After all retries exhausted, raise the last exception
        pass

    def stream(self, messages: list[Message], system: str = "", max_tokens: int = 1024) -> Iterator[StreamChunk]:
        """Streaming completion. Yields StreamChunk objects."""
        # TODO: Import anthropic (same import as above)
        # TODO: Create client the same way as in complete()
        # TODO: Convert messages to anthropic format
        # TODO: Use: with client.messages.stream(...) as stream:
        # TODO:   for text in stream.text_stream:
        # TODO:       yield StreamChunk(text=text, done=False)
        # TODO: After the with block: yield StreamChunk(text="", done=True)
        pass


# ============================================================
# MILESTONE 2: RAG Pipeline
# ============================================================

@dataclass
class Document:
    id: str
    content: str
    metadata: dict = field(default_factory=dict)

@dataclass
class RetrievedChunk:
    document: Document
    score: float

class SimpleVectorStore:
    """In-memory vector store using cosine similarity on TF-IDF vectors."""

    def __init__(self):
        self._documents: list[Document] = []
        self._vectors: list[dict[str, float]] = []  # TF-IDF dicts

    def _tfidf_vector(self, text: str) -> dict[str, float]:
        """Compute simple TF-IDF-like vector (term frequency only, for simplicity)."""
        # TODO: Define stopwords set: {"a", "the", "is", "are", "of", "in", "to", "and", "it", "for"}
        # TODO: Lowercase text and split on whitespace: words = text.lower().split()
        # TODO: Filter out stopwords: words = [w for w in words if w not in stopwords]
        # TODO: Count term frequencies using a dict
        # TODO: Normalize: divide each count by len(words) (guard against zero division)
        # TODO: Return the normalized dict
        pass

    def _cosine_similarity(self, a: dict[str, float], b: dict[str, float]) -> float:
        """Cosine similarity between two TF-IDF vectors."""
        # TODO: Compute dot product: sum a[term] * b[term] for terms in both a and b
        # TODO: Compute magnitude of a: sqrt(sum of squared values in a)
        # TODO: Compute magnitude of b: sqrt(sum of squared values in b)
        # TODO: If either magnitude is 0, return 0.0 (avoid division by zero)
        # TODO: Return dot_product / (mag_a * mag_b)
        pass

    def add(self, doc: Document) -> None:
        """Add a document to the store."""
        # TODO: Compute TF-IDF vector for doc.content using _tfidf_vector()
        # TODO: Append doc to self._documents
        # TODO: Append vector to self._vectors
        pass

    def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        """Return top_k most similar documents."""
        # TODO: If store is empty, return []
        # TODO: Compute query vector using _tfidf_vector(query)
        # TODO: For each stored doc/vector, compute _cosine_similarity(query_vec, doc_vec)
        # TODO: Create list of RetrievedChunk(document=doc, score=score)
        # TODO: Sort by score descending
        # TODO: Return first top_k results
        pass


class RAGPipeline:
    def __init__(self, store: SimpleVectorStore, llm: LLMClient):
        self.store = store
        self.llm = llm

    def ingest(self, documents: list[Document]) -> None:
        """Add all documents to the vector store."""
        # TODO: Call self.store.add(doc) for each document in documents
        pass

    def retrieve_and_answer(self, question: str, history: list[Message] = None) -> str:
        """Retrieve relevant docs and answer the question."""
        # TODO: Search store for top 3 relevant docs: chunks = self.store.search(question, top_k=3)
        # TODO: Check if all scores are below threshold (0.05) or no chunks found
        #       If so: call self.llm.complete([Message("user", question)],
        #                                     system="Answer from your knowledge. Note if uncertain.")
        #       and return the result (graceful degradation)
        # TODO: Build context string: join doc contents with "\n\n"
        # TODO: Build messages list: (history or []) + [Message("user", question)]
        # TODO: Build system prompt: "Answer the question based on the context below.
        #       If the answer is not in the context, say so.\n\nContext:\n{context}"
        # TODO: Call self.llm.complete(messages, system=system_prompt) and return result
        pass


# ============================================================
# MILESTONE 3: Tool System
# ============================================================

@dataclass
class ToolCall:
    name: str
    arguments: dict

@dataclass
class ToolResult:
    name: str
    output: str
    success: bool

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._descriptions: dict[str, str] = {}

    def register(self, name: str, description: str, func: Callable) -> None:
        """Register a tool by name."""
        # TODO: Store func in self._tools[name]
        # TODO: Store description in self._descriptions[name]
        pass

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute a tool call. Never raises — returns ToolResult(success=False) on error."""
        # TODO: If call.name not in self._tools:
        #       return ToolResult(call.name, f"Unknown tool: {call.name}", False)
        # TODO: Try: result = self._tools[call.name](**call.arguments)
        #            return ToolResult(call.name, str(result), True)
        # TODO: Except Exception as e:
        #            return ToolResult(call.name, str(e), False)
        pass

    def get_tool_descriptions(self) -> str:
        """Return formatted string of tool names and descriptions."""
        # TODO: If no tools registered, return "No tools available"
        # TODO: Build list of "{name}: {description}" strings
        # TODO: Join with newline and return
        pass

    def list_names(self) -> list[str]:
        """Return list of registered tool names."""
        # TODO: Return list(self._tools.keys())
        pass


def create_default_tools() -> ToolRegistry:
    """Create registry with default tools."""
    registry = ToolRegistry()

    # TODO: Define web_search function: takes query: str, returns mock result string
    # Mock return: f"[Mock web results for: {query}] Relevant information found in search results."

    # TODO: Register "web_search" with description:
    # "Search the web for current information. Args: query (str)"

    # TODO: Define calculator function: takes expression: str, evaluates safely, returns str(result)
    # Use safe eval: safe_builtins = {"__builtins__": {}, "abs": abs, "round": round, "max": max, "min": min}
    # result = eval(expression, safe_builtins)

    # TODO: Register "calculator" with description:
    # "Evaluate a mathematical expression. Args: expression (str)"

    # TODO: Return registry
    pass


# ============================================================
# MILESTONE 4: Planner
# ============================================================

@dataclass
class Plan:
    needs_rag: bool
    needs_tools: list[str]  # tool names to call
    reasoning: str

def parse_plan(llm_response: str) -> Plan:
    """Parse planner LLM response into a Plan."""
    # TODO: Search for "NEEDS_RAG:" line in response (case-insensitive)
    #       If found and value contains "yes": needs_rag = True, else False
    #       Default: needs_rag = False
    # TODO: Search for "TOOLS:" line in response (case-insensitive)
    #       Split the value by comma, strip each, filter empty strings
    #       Default: needs_tools = []
    # TODO: Search for "REASONING:" line, capture everything after it
    #       Default reasoning: use the full response
    # TODO: Return Plan(needs_rag=needs_rag, needs_tools=needs_tools, reasoning=reasoning)
    pass

def plan_query(query: str, llm: LLMClient, available_tools: list[str]) -> Plan:
    """Ask LLM to plan how to answer the query."""
    # TODO: Build tool_list string from available_tools (comma-separated or "none")
    # TODO: Build system prompt:
    #   "You are a planning agent. Decide the best strategy to answer the user query.
    #    Available tools: {tool_list}
    #    Respond in EXACTLY this format:
    #    NEEDS_RAG: yes/no
    #    TOOLS: comma-separated tool names (or empty if none needed)
    #    REASONING: brief explanation"
    # TODO: Call llm.complete([Message("user", query)], system=system_prompt, max_tokens=200)
    # TODO: Return parse_plan(response)
    pass


# ============================================================
# MILESTONE 5: Agent Loop
# ============================================================

@dataclass
class AgentTrace:
    step: str
    input: str
    output: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)

class ResearchAssistant:
    def __init__(self, llm: LLMClient, rag: RAGPipeline, tools: ToolRegistry):
        self.llm = llm
        self.rag = rag
        self.tools = tools
        self.history: list[Message] = []
        self.traces: list[AgentTrace] = []
        self._cache: dict[str, str] = {}

    def _trace(self, step: str, input_: str, output: str, start_time: float) -> None:
        """Record a trace entry."""
        # TODO: Calculate duration_ms = (time.time() - start_time) * 1000
        # TODO: Create AgentTrace(step=step, input=input_[:200], output=output[:200],
        #                         duration_ms=duration_ms)
        # TODO: Append to self.traces
        pass

    def _check_guardrails(self, query: str) -> Optional[str]:
        """Check for prompt injection. Returns error message string, or None if safe."""
        # TODO: Define injection_patterns list:
        #   ["ignore previous instructions", "system:", "jailbreak",
        #    "forget your instructions", "act as if", "disregard"]
        # TODO: Check if any pattern appears in query.lower()
        # TODO: If found: return "Query rejected: potential prompt injection detected"
        # TODO: Return None if all checks pass
        pass

    def _cache_key(self, query: str) -> str:
        """Return SHA-256 hash of the normalized query."""
        # TODO: Normalize: query.lower().strip()
        # TODO: Return hashlib.sha256(normalized.encode()).hexdigest()
        pass

    def answer(self, query: str, stream: bool = False) -> str:
        """Main entry point. Run full agent loop and return answer."""

        # Step 1: Guardrail check
        # TODO: error = self._check_guardrails(query)
        # TODO: if error: return error

        # Step 2: Cache check
        # TODO: key = self._cache_key(query)
        # TODO: if key in self._cache: print("[Cache hit]"); return self._cache[key]

        # Step 3: Plan
        # TODO: t0 = time.time()
        # TODO: plan = plan_query(query, self.llm, self.tools.list_names())
        # TODO: self._trace("plan", query, str(plan), t0)

        # Step 4: Execute tools if needed
        # TODO: tool_context_parts = []
        # TODO: for tool_name in plan.needs_tools:
        # TODO:     t1 = time.time()
        # TODO:     result = self.tools.execute(ToolCall(tool_name, {"query": query}))
        # TODO:     self._trace(f"tool:{tool_name}", query, result.output, t1)
        # TODO:     if result.success:
        # TODO:         tool_context_parts.append(f"[{tool_name} result]: {result.output}")

        # Step 5: RAG or direct LLM
        # TODO: t2 = time.time()
        # TODO: if plan.needs_rag:
        # TODO:     answer = self.rag.retrieve_and_answer(query, self.history)
        # TODO: else:
        # TODO:     context_prefix = "\n".join(tool_context_parts)
        # TODO:     user_content = f"{context_prefix}\n\n{query}".strip() if context_prefix else query
        # TODO:     messages = self.history + [Message("user", user_content)]
        # TODO:     answer = self.llm.complete(messages, system="You are a helpful research assistant.")
        # TODO: self._trace("generate", query, answer, t2)

        # Step 6: Update history and cache
        # TODO: self.history.append(Message("user", query))
        # TODO: self.history.append(Message("assistant", answer))
        # TODO: self._cache[key] = answer

        # Step 7: Return answer
        # TODO: return answer
        pass


# ============================================================
# MILESTONE 6: Observability
# ============================================================

def format_trace_report(traces: list[AgentTrace]) -> str:
    """Format traces as a readable report."""
    # TODO: Build header: "=== Trace Report ==="
    # TODO: If no traces, append "(no steps recorded)" and return
    # TODO: For each trace (enumerate from 1):
    #       line = f"[{i}] {trace.step:<12} | {trace.duration_ms:>6.0f}ms | "
    #              f"input: \"{trace.input[:60]}...\" → output: \"{trace.output[:60]}...\""
    #       append to lines
    # TODO: Compute total_ms = sum(t.duration_ms for t in traces)
    # TODO: Append "---" separator
    # TODO: Append f"Total: {total_ms:.0f}ms across {len(traces)} steps"
    # TODO: Return "\n".join(lines)
    pass


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    import os

    if len(sys.argv) < 2:
        print("Usage: python solution.py <question>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    # Sample knowledge base
    KNOWLEDGE_BASE = [
        Document("1", "Retrieval Augmented Generation (RAG) combines vector search with LLMs to answer questions from a knowledge base."),
        Document("2", "Embeddings are numerical vector representations of text that capture semantic meaning."),
        Document("3", "An agentic loop is the observe-think-act cycle where an AI agent iteratively solves a task."),
        Document("4", "Fine-tuning adjusts a pre-trained model's weights on a specific dataset to improve task performance."),
        Document("5", "Prompt injection is a security attack where malicious content in prompts overrides system instructions."),
    ]

    # TODO: Initialize LLMClient()
    # TODO: Initialize SimpleVectorStore()
    # TODO: Initialize RAGPipeline(store=store, llm=llm)
    # TODO: Call rag.ingest(KNOWLEDGE_BASE)
    # TODO: Initialize tools = create_default_tools()
    # TODO: Initialize assistant = ResearchAssistant(llm=llm, rag=rag, tools=tools)
    # TODO: Print "Research Assistant ready. Processing query..."
    # TODO: answer = assistant.answer(query)
    # TODO: Print a blank line
    # TODO: Print answer
    # TODO: Print a blank line
    # TODO: Print format_trace_report(assistant.traces)


if __name__ == "__main__":
    main()
