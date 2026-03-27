"""Lab 35: Tracing & Observability"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
import time
import functools
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
    """Calculate total USD cost from a trace.
    # TODO: for each span, look up COST_PER_1K_TOKENS[span.model].
    # If model not found, skip. Sum input_cost + output_cost for each span.
    # input_cost = input_tokens / 1000 * pricing["input"]
    # output_cost = output_tokens / 1000 * pricing["output"]
    """
    raise NotImplementedError()


def create_span(name: str, fn, *args, **kwargs) -> tuple[Span, any]:
    """Execute fn(*args, **kwargs), record latency and any exception.
    Returns (span, result). Result is None if an exception occurred.
    # TODO: record start time, call fn, record end time.
    # Catch exceptions, store str(e) in span.error, return (span, None).
    # On success return (span, result).
    """
    raise NotImplementedError()
