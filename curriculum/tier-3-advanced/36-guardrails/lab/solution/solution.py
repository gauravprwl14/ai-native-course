"""Lab 36: Guardrails — Reference Solution"""
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

TOPIC_PROMPT = """You are a topic classifier. The assistant is ONLY allowed to help with: {topics}

Is the following message on one of those topics? Reply with exactly "yes" or "no".

Message: {text}"""


def is_safe_input(text: str) -> tuple[bool, str]:
    """Check input for blocked patterns. Returns (safe: bool, reason: str)."""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"Blocked pattern: {pattern}"
    return True, "ok"


def is_on_topic(text: str, allowed_topics: list[str]) -> bool:
    """Use LLM to check if text is about one of the allowed topics."""
    client = get_anthropic_client()
    prompt = TOPIC_PROMPT.format(topics=", ".join(allowed_topics), text=text)
    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.content[0].text.strip().lower()
    return answer.startswith("yes")


def filter_output(response: str, max_length: int = 2000) -> str:
    """Trim response to max_length at a sentence boundary."""
    if len(response) <= max_length:
        return response
    truncated = response[:max_length]
    last_period = max(truncated.rfind(". "), truncated.rfind(".\n"))
    if last_period > max_length * 0.5:
        return truncated[:last_period + 1]
    return truncated.rstrip() + "..."


class GuardrailPipeline:
    def __init__(self, allowed_topics: list[str], max_output_length: int = 2000):
        self.allowed_topics = allowed_topics
        self.max_output_length = max_output_length

    def run(self, user_input: str, model_response_fn) -> dict:
        """Apply input checks, call model, apply output checks."""
        # 1. Input safety check
        safe, reason = is_safe_input(user_input)
        if not safe:
            return {"safe": False, "response": "", "blocked_reason": reason}

        # 2. Topic check
        if not is_on_topic(user_input, self.allowed_topics):
            return {"safe": False, "response": "", "blocked_reason": "off_topic"}

        # 3. Call the model
        raw_response = model_response_fn(user_input)

        # 4. Output filtering
        filtered_response = filter_output(raw_response, self.max_output_length)

        return {"safe": True, "response": filtered_response, "blocked_reason": None}
