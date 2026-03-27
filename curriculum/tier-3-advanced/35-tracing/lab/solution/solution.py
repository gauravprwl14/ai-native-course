"""Lab 35: Tracing & Observability — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
import time
from dataclasses import dataclass, field

COST_PER_1K_TOKENS = {
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
}


@dataclass
class Span:
    name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    error: str = None


@dataclass
class Trace:
    spans: list[Span] = field(default_factory=list)

    def add_span(self, span: Span):
        self.spans.append(span)

    @property
    def total_tokens(self):
        return sum(s.input_tokens + s.output_tokens for s in self.spans)

    @property
    def total_latency_ms(self):
        return sum(s.latency_ms for s in self.spans)


def calculate_cost_from_trace(trace: Trace) -> float:
    """Calculate total USD cost from a trace."""
    total_cost = 0.0
    for span in trace.spans:
        pricing = COST_PER_1K_TOKENS.get(span.model)
        if pricing is None:
            continue
        input_cost = span.input_tokens / 1000 * pricing["input"]
        output_cost = span.output_tokens / 1000 * pricing["output"]
        total_cost += input_cost + output_cost
    return total_cost


def create_span(name: str, fn, *args, **kwargs) -> tuple[Span, any]:
    """Execute fn(*args, **kwargs), record latency and errors. Returns (span, result)."""
    start = time.time()
    error = None
    result = None
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        error = str(e)
    latency_ms = (time.time() - start) * 1000
    span = Span(name=name, latency_ms=latency_ms, error=error)
    return span, result
