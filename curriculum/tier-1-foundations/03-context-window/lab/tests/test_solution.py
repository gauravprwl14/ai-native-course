"""Tests for Lab 03: Context Window Management"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))


def test_count_history_tokens_empty():
    from solution import count_history_tokens
    assert count_history_tokens([]) == 0


def test_count_history_tokens_single_message():
    from solution import count_history_tokens
    history = [{"role": "user", "content": "Hello world"}]
    tokens = count_history_tokens(history)
    assert tokens > 0
    assert tokens < 50  # "Hello world" is only 2 tokens + overhead


def test_count_history_tokens_multiple_messages():
    from solution import count_history_tokens
    history = [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
        {"role": "user", "content": "Tell me more."},
    ]
    tokens = count_history_tokens(history)
    assert tokens > count_history_tokens(history[:1])


def test_truncate_history_no_truncation_needed():
    from solution import truncate_history
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
    ]
    result = truncate_history(history, max_tokens=1000)
    assert len(result) == 2


def test_truncate_history_removes_oldest():
    from solution import truncate_history, count_history_tokens
    history = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First response"},
        {"role": "user", "content": "Second message"},
        {"role": "assistant", "content": "Second response"},
    ]
    # Set max_tokens very low to force truncation
    result = truncate_history(history, max_tokens=20)
    # Should have fewer messages
    assert len(result) < len(history)
    # Most recent messages should be kept
    if result:
        assert result[-1]["content"] == "Second response"


def test_truncate_history_does_not_mutate_original():
    from solution import truncate_history
    history = [
        {"role": "user", "content": "Hello " * 100},
    ]
    original_len = len(history)
    truncate_history(history, max_tokens=10)
    assert len(history) == original_len


def test_chat_with_history_returns_tuple():
    from solution import chat_with_history
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Paris is the capital of France.")]

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        response_text, updated_history = chat_with_history(
            "What is the capital of France?",
            [],
        )

    assert isinstance(response_text, str)
    assert len(response_text) > 0
    assert isinstance(updated_history, list)


def test_chat_with_history_appends_messages():
    from solution import chat_with_history
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Berlin is the capital of Germany.")]

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        _, updated_history = chat_with_history("What is the capital of Germany?", [])

    assert len(updated_history) == 2
    assert updated_history[0]["role"] == "user"
    assert updated_history[1]["role"] == "assistant"


def test_chat_with_history_preserves_existing_history():
    from solution import chat_with_history
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Berlin.")]

    existing_history = [
        {"role": "user", "content": "What is 2+2?"},
        {"role": "assistant", "content": "4"},
    ]

    with patch("solution.get_anthropic_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        _, updated_history = chat_with_history("Next question", existing_history)

    # Should have original 2 + new user + new assistant = 4
    assert len(updated_history) == 4
