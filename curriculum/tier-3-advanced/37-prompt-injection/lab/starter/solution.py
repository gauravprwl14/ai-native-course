"""Lab 37: Prompt Injection Security"""
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
    """Check for injection patterns.
    Returns (is_injection: bool, matched_patterns: list[str]).
    # TODO: loop over INJECTION_PATTERNS.
    # Use re.search(pattern, text, re.IGNORECASE) for each.
    # Collect matched patterns in a list.
    # Return (len(matched) > 0, matched).
    """
    raise NotImplementedError()


def sanitize_input(user_input: str) -> str:
    """Remove/replace known injection phrases with '[REMOVED]'.
    # TODO: for each pattern in INJECTION_PATTERNS,
    # apply re.sub(pattern, '[REMOVED]', text, flags=re.IGNORECASE).
    # Return the final sanitized string.
    """
    raise NotImplementedError()


def wrap_user_input(user_input: str) -> str:
    """Wrap input in XML tags for prompt isolation.
    # TODO: return f'<user_input>{user_input}</user_input>'
    """
    raise NotImplementedError()


def test_injection_resilience(system_prompt: str, injection_attempts: list[str]) -> dict:
    """Test system prompt against injection attempts using detect_injection_attempt.
    Returns {"total": int, "blocked": int, "passed": int}.
    # TODO: for each attempt in injection_attempts:
    #   call detect_injection_attempt(attempt)
    #   count as blocked if is_injection=True, passed otherwise.
    # Return the counts.
    """
    raise NotImplementedError()
