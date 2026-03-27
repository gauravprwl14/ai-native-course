"""
Capstone Lab: Research Assistant Agent (SOLUTION)

A complete AI system demonstrating all major concepts from the course:
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
import os
import time
import hashlib
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Iterator, Callable

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
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        fmt_messages = [{"role": m.role, "content": m.content} for m in messages]

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=fmt_messages,
                )
                return response.content[0].text
            except anthropic.RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                time.sleep(wait)
        raise last_error

    def stream(self, messages: list[Message], system: str = "", max_tokens: int = 1024) -> Iterator[StreamChunk]:
        """Streaming completion. Yields StreamChunk objects."""
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        fmt_messages = [{"role": m.role, "content": m.content} for m in messages]

        with client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=fmt_messages,
        ) as stream:
            for text in stream.text_stream:
                yield StreamChunk(text=text, done=False)
        yield StreamChunk(text="", done=True)


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

    _STOPWORDS = {"a", "the", "is", "are", "of", "in", "to", "and", "it", "for"}

    def __init__(self):
        self._documents: list[Document] = []
        self._vectors: list[dict[str, float]] = []

    def _tfidf_vector(self, text: str) -> dict[str, float]:
        """Compute simple term-frequency vector (normalized)."""
        words = [w for w in text.lower().split() if w not in self._STOPWORDS]
        if not words:
            return {}
        counts: dict[str, int] = {}
        for w in words:
            counts[w] = counts.get(w, 0) + 1
        total = len(words)
        return {term: count / total for term, count in counts.items()}

    def _cosine_similarity(self, a: dict[str, float], b: dict[str, float]) -> float:
        """Cosine similarity between two TF-IDF vectors."""
        dot = sum(a[t] * b[t] for t in a if t in b)
        mag_a = math.sqrt(sum(v * v for v in a.values()))
        mag_b = math.sqrt(sum(v * v for v in b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def add(self, doc: Document) -> None:
        """Add a document to the store."""
        self._documents.append(doc)
        self._vectors.append(self._tfidf_vector(doc.content))

    def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        """Return top_k most similar documents."""
        if not self._documents:
            return []
        query_vec = self._tfidf_vector(query)
        scored = [
            RetrievedChunk(document=doc, score=self._cosine_similarity(query_vec, vec))
            for doc, vec in zip(self._documents, self._vectors)
        ]
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]


class RAGPipeline:
    def __init__(self, store: SimpleVectorStore, llm: LLMClient):
        self.store = store
        self.llm = llm

    def ingest(self, documents: list[Document]) -> None:
        """Add all documents to the vector store."""
        for doc in documents:
            self.store.add(doc)

    def retrieve_and_answer(self, question: str, history: list[Message] = None) -> str:
        """Retrieve relevant docs and answer the question."""
        chunks = self.store.search(question, top_k=3)

        # Graceful degradation: no relevant docs found
        if not chunks or chunks[0].score < 0.05:
            return self.llm.complete(
                [Message("user", question)],
                system="Answer the question from your knowledge. Note if you are uncertain.",
            )

        context = "\n\n".join(c.document.content for c in chunks)
        system_prompt = (
            "Answer the question based on the context below. "
            "If the answer is not in the context, say so.\n\n"
            f"Context:\n{context}"
        )
        messages = (history or []) + [Message("user", question)]
        return self.llm.complete(messages, system=system_prompt)


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
        """Register a tool."""
        self._tools[name] = func
        self._descriptions[name] = description

    def execute(self, call: ToolCall) -> ToolResult:
        """Execute a tool call. Never raises."""
        if call.name not in self._tools:
            return ToolResult(call.name, f"Unknown tool: {call.name}", False)
        try:
            result = self._tools[call.name](**call.arguments)
            return ToolResult(call.name, str(result), True)
        except Exception as e:
            return ToolResult(call.name, str(e), False)

    def get_tool_descriptions(self) -> str:
        """Return formatted string of tool names and descriptions."""
        if not self._tools:
            return "No tools available"
        return "\n".join(f"{name}: {desc}" for name, desc in self._descriptions.items())

    def list_names(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())


def create_default_tools() -> ToolRegistry:
    """Create registry with default tools."""
    registry = ToolRegistry()

    def web_search(query: str) -> str:
        return f"[Mock web results for: {query}] Relevant information found in search results."

    registry.register(
        "web_search",
        "Search the web for current information. Args: query (str)",
        web_search,
    )

    def calculator(expression: str) -> str:
        safe_builtins = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "max": max,
            "min": min,
        }
        result = eval(expression, safe_builtins)  # noqa: S307
        return str(result)

    registry.register(
        "calculator",
        "Evaluate a mathematical expression. Args: expression (str)",
        calculator,
    )

    return registry


# ============================================================
# MILESTONE 4: Planner
# ============================================================

@dataclass
class Plan:
    needs_rag: bool
    needs_tools: list[str]
    reasoning: str

def parse_plan(llm_response: str) -> Plan:
    """Parse planner LLM response into a Plan."""
    needs_rag = False
    needs_tools: list[str] = []
    reasoning = llm_response.strip()

    for line in llm_response.splitlines():
        line_lower = line.lower().strip()
        if line_lower.startswith("needs_rag:"):
            value = line.split(":", 1)[1].strip().lower()
            needs_rag = "yes" in value
        elif line_lower.startswith("tools:"):
            raw = line.split(":", 1)[1].strip()
            needs_tools = [t.strip() for t in raw.split(",") if t.strip()]
        elif line_lower.startswith("reasoning:"):
            reasoning = line.split(":", 1)[1].strip()

    return Plan(needs_rag=needs_rag, needs_tools=needs_tools, reasoning=reasoning)

def plan_query(query: str, llm: LLMClient, available_tools: list[str]) -> Plan:
    """Ask LLM to plan how to answer the query."""
    tool_list = ", ".join(available_tools) if available_tools else "none"
    system_prompt = (
        "You are a planning agent. Decide the best strategy to answer the user query.\n"
        f"Available tools: {tool_list}\n"
        "Respond in EXACTLY this format:\n"
        "NEEDS_RAG: yes/no\n"
        "TOOLS: comma-separated tool names (or empty if none needed)\n"
        "REASONING: brief explanation"
    )
    response = llm.complete([Message("user", query)], system=system_prompt, max_tokens=200)
    return parse_plan(response)


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
        duration_ms = (time.time() - start_time) * 1000
        self.traces.append(AgentTrace(
            step=step,
            input=input_[:200],
            output=output[:200],
            duration_ms=duration_ms,
        ))

    def _check_guardrails(self, query: str) -> Optional[str]:
        """Check for prompt injection. Returns error message or None if safe."""
        injection_patterns = [
            "ignore previous instructions",
            "system:",
            "jailbreak",
            "forget your instructions",
            "act as if",
            "disregard",
        ]
        query_lower = query.lower()
        for pattern in injection_patterns:
            if pattern in query_lower:
                return "Query rejected: potential prompt injection detected"
        return None

    def _cache_key(self, query: str) -> str:
        """Return SHA-256 hash of the normalized query."""
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def answer(self, query: str, stream: bool = False) -> str:
        """Main entry point. Run full agent loop and return answer."""

        # Step 1: Guardrail check
        error = self._check_guardrails(query)
        if error:
            return error

        # Step 2: Cache check
        key = self._cache_key(query)
        if key in self._cache:
            print("[Cache hit]")
            return self._cache[key]

        # Step 3: Plan
        t0 = time.time()
        plan = plan_query(query, self.llm, self.tools.list_names())
        self._trace("plan", query, str(plan), t0)

        # Step 4: Execute tools if needed
        tool_context_parts: list[str] = []
        for tool_name in plan.needs_tools:
            t1 = time.time()
            result = self.tools.execute(ToolCall(tool_name, {"query": query}))
            self._trace(f"tool:{tool_name}", query, result.output, t1)
            if result.success:
                tool_context_parts.append(f"[{tool_name} result]: {result.output}")

        # Step 5: RAG or direct LLM
        t2 = time.time()
        if plan.needs_rag:
            final_answer = self.rag.retrieve_and_answer(query, self.history)
        else:
            context_prefix = "\n".join(tool_context_parts)
            user_content = f"{context_prefix}\n\n{query}".strip() if context_prefix else query
            messages = self.history + [Message("user", user_content)]
            final_answer = self.llm.complete(
                messages,
                system="You are a helpful research assistant.",
            )
        self._trace("generate", query, final_answer, t2)

        # Step 6: Update history and cache
        self.history.append(Message("user", query))
        self.history.append(Message("assistant", final_answer))
        self._cache[key] = final_answer

        # Step 7: Return answer
        return final_answer


# ============================================================
# MILESTONE 6: Observability
# ============================================================

def format_trace_report(traces: list[AgentTrace]) -> str:
    """Format traces as a readable report."""
    lines = ["=== Trace Report ==="]
    if not traces:
        lines.append("(no steps recorded)")
        return "\n".join(lines)

    for i, trace in enumerate(traces, 1):
        input_preview = trace.input[:60].replace("\n", " ")
        output_preview = trace.output[:60].replace("\n", " ")
        line = (
            f"[{i}] {trace.step:<14} | {trace.duration_ms:>6.0f}ms | "
            f"input: \"{input_preview}...\" → output: \"{output_preview}...\""
        )
        lines.append(line)

    total_ms = sum(t.duration_ms for t in traces)
    lines.append("---")
    lines.append(f"Total: {total_ms:.0f}ms across {len(traces)} steps")
    return "\n".join(lines)


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python solution.py <question>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    KNOWLEDGE_BASE = [
        Document("1", "Retrieval Augmented Generation (RAG) combines vector search with LLMs to answer questions from a knowledge base."),
        Document("2", "Embeddings are numerical vector representations of text that capture semantic meaning."),
        Document("3", "An agentic loop is the observe-think-act cycle where an AI agent iteratively solves a task."),
        Document("4", "Fine-tuning adjusts a pre-trained model's weights on a specific dataset to improve task performance."),
        Document("5", "Prompt injection is a security attack where malicious content in prompts overrides system instructions."),
    ]

    llm = LLMClient()
    store = SimpleVectorStore()
    rag = RAGPipeline(store=store, llm=llm)
    rag.ingest(KNOWLEDGE_BASE)
    tools = create_default_tools()
    assistant = ResearchAssistant(llm=llm, rag=rag, tools=tools)

    print("Research Assistant ready. Processing query...")
    answer = assistant.answer(query)
    print()
    print(answer)
    print()
    print(format_trace_report(assistant.traces))


if __name__ == "__main__":
    main()
