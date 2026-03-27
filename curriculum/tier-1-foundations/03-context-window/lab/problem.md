# Lab 03: Build a Context-Aware Q&A System

## Problem Statement

Build a chatbot that remembers conversation history while staying within token limits.

## Functions to Implement

### `count_history_tokens(history: list[dict]) -> int`

Count total tokens for a list of message dicts (each has `role` and `content`).

- Use `tiktoken` with the `cl100k_base` encoding
- Add ~4 tokens per message for role/format overhead
- An empty list returns 0

### `truncate_history(history: list[dict], max_tokens: int) -> list[dict]`

Remove the oldest messages from history until it fits within `max_tokens`.

- Never mutate the input list — return a new list
- Remove messages from the front (oldest first)
- Return the truncated history (most recent messages kept)
- If history already fits, return a copy unchanged

### `chat_with_history(user_message: str, history: list[dict], max_tokens: int = 4000) -> tuple[str, list[dict]]`

Send a message to Claude with conversation history.

- Truncate history to `max_tokens` before sending
- Append new user message to history as `{"role": "user", "content": user_message}`
- Call the Anthropic client with `messages=history`
- Extract response text from the response
- Append assistant response as `{"role": "assistant", "content": response_text}`
- Return `(response_text, updated_history)`

## Acceptance Criteria

- `count_history_tokens` returns correct token count
- `truncate_history` removes oldest messages to fit budget without mutating the original
- `chat_with_history` returns response and updated history with all messages appended
- All tests pass: `pytest tests/ -v`
