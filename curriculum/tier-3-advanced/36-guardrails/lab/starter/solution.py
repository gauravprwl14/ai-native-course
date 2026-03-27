"""Lab 36: Guardrails"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
import re
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"
BLOCKED_PATTERNS = [
    r"\b(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)\b",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
]


def is_safe_input(text: str) -> tuple[bool, str]:
    """Check input for blocked patterns.
    Returns (safe: bool, reason: str).
    # TODO: loop over BLOCKED_PATTERNS, use re.search with re.IGNORECASE.
    # Return (False, f"Blocked pattern: {pattern}") on first match.
    # Return (True, "ok") if no match found.
    """
    raise NotImplementedError()


def is_on_topic(text: str, allowed_topics: list[str]) -> bool:
    """Use LLM to check if text is about one of the allowed topics.
    Returns True if on topic, False otherwise.
    # TODO: build a prompt with the allowed topics list.
    # Call API with max_tokens=10. Parse "yes"/"no" from response.
    """
    raise NotImplementedError()


def filter_output(response: str, max_length: int = 2000) -> str:
    """Trim response to max_length at a sentence boundary.
    # TODO: if len(response) > max_length, truncate.
    # Find last '. ' or '.\n' in truncated string using rfind.
    # If found at a reasonable position, cut there. Otherwise add '...'.
    """
    raise NotImplementedError()


class GuardrailPipeline:
    def __init__(self, allowed_topics: list[str], max_output_length: int = 2000):
        self.allowed_topics = allowed_topics
        self.max_output_length = max_output_length

    def run(self, user_input: str, model_response_fn) -> dict:
        """Apply input checks, call model, apply output checks.
        Returns {"safe": bool, "response": str, "blocked_reason": str|None}.
        # TODO:
        # 1. Call is_safe_input(user_input) — return early if not safe.
        # 2. Call is_on_topic(user_input, self.allowed_topics) — return early if off-topic.
        # 3. Call model_response_fn(user_input) to get raw response.
        # 4. Call filter_output(raw_response, self.max_output_length).
        # 5. Return {"safe": True, "response": filtered, "blocked_reason": None}.
        """
        raise NotImplementedError()
