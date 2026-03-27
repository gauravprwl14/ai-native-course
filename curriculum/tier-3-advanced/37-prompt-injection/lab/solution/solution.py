"""Lab 37: Prompt Injection Security — Reference Solution"""
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

MODEL = "claude-3-haiku-20240307"
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions?",
    r"disregard\s+(your\s+)?(system\s+)?prompt",
    r"you\s+are\s+now",
    r"new\s+persona",
    r"jailbreak",
]


def detect_injection_attempt(text: str) -> tuple[bool, list[str]]:
    """Check for injection patterns. Returns (is_injection, matched_patterns)."""
    matched = []
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            matched.append(pattern)
    return len(matched) > 0, matched


def sanitize_input(user_input: str) -> str:
    """Remove/replace known injection phrases."""
    result = user_input
    for pattern in INJECTION_PATTERNS:
        result = re.sub(pattern, "[REMOVED]", result, flags=re.IGNORECASE)
    return result


def wrap_user_input(user_input: str) -> str:
    """Wrap input in XML tags for prompt isolation."""
    return f"<user_input>{user_input}</user_input>"


def test_injection_resilience(system_prompt: str, injection_attempts: list[str]) -> dict:
    """Test system prompt against injection attempts.
    Returns {"total": int, "blocked": int, "passed": int}.
    """
    total = len(injection_attempts)
    blocked = 0
    for attempt in injection_attempts:
        is_injection, _ = detect_injection_attempt(attempt)
        if is_injection:
            blocked += 1
    return {
        "total": total,
        "blocked": blocked,
        "passed": total - blocked,
    }
