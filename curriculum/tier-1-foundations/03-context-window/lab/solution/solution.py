"""
Lab 03: Context Window Management — Reference Solution
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import tiktoken
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"
ENCODING = tiktoken.get_encoding("cl100k_base")


def count_history_tokens(history: list[dict]) -> int:
    total = 0
    for message in history:
        total += len(ENCODING.encode(message["content"])) + 4  # role overhead
    return total


def truncate_history(history: list[dict], max_tokens: int) -> list[dict]:
    result = list(history)
    while result and count_history_tokens(result) > max_tokens:
        result.pop(0)
    return result


def chat_with_history(
    user_message: str,
    history: list[dict],
    max_tokens: int = 4000,
) -> tuple[str, list[dict]]:
    client = get_anthropic_client()

    history = truncate_history(history, max_tokens)
    history = history + [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=history,
    )

    response_text = response.content[0].text
    history = history + [{"role": "assistant", "content": response_text}]

    return response_text, history
