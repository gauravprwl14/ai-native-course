"""
Lab 03: Context Window Management
Build a context-aware Q&A system that manages conversation history.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import tiktoken
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"
ENCODING = tiktoken.get_encoding("cl100k_base")


def count_history_tokens(history: list[dict]) -> int:
    """
    Count total tokens in a conversation history.

    Args:
        history: List of message dicts with 'role' and 'content' keys

    Returns:
        Total token count for all messages

    # TODO: Use ENCODING.encode() to count tokens for each message's content
    # and return the total. Add ~4 tokens per message for role/format overhead.
    """
    raise NotImplementedError("Implement count_history_tokens")


def truncate_history(history: list[dict], max_tokens: int) -> list[dict]:
    """
    Remove oldest messages from history until it fits within max_tokens.

    Args:
        history: List of message dicts
        max_tokens: Maximum allowed tokens

    Returns:
        Truncated history with most recent messages kept

    # TODO: While the history exceeds max_tokens, remove the first message.
    # Return a copy of the list (don't mutate the original).
    """
    raise NotImplementedError("Implement truncate_history")


def chat_with_history(
    user_message: str,
    history: list[dict],
    max_tokens: int = 4000,
) -> tuple[str, list[dict]]:
    """
    Send a message to Claude with conversation history managed within token budget.

    Args:
        user_message: The new user message
        history: Existing conversation history
        max_tokens: Maximum tokens for history (not counting new message)

    Returns:
        Tuple of (response_text, updated_history)

    # TODO:
    # 1. Truncate history to max_tokens
    # 2. Add user_message to history as {"role": "user", "content": user_message}
    # 3. Call the Anthropic client with messages=history
    # 4. Extract response text from the response
    # 5. Append assistant response to history as {"role": "assistant", "content": response_text}
    # 6. Return (response_text, updated_history)
    """
    raise NotImplementedError("Implement chat_with_history")
