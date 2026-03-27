"""
Shared utilities for AI-Native Course labs.

Usage:
    from shared.utils import get_anthropic_client, get_openai_client, print_response
"""

import os
import sys
from pathlib import Path
from typing import Optional


def _load_env() -> None:
    """Load .env file — searches current dir and parents up to repo root."""
    try:
        from dotenv import load_dotenv
        candidates = [
            Path(__file__).parent / ".env",
            Path(__file__).parent.parent.parent / ".env",
        ]
        for path in candidates:
            if path.exists():
                load_dotenv(path)
                return
        load_dotenv()
    except ImportError:
        pass


_load_env()


def get_anthropic_client():
    """Return a configured Anthropic client. Raises clearly if key is missing."""
    try:
        import anthropic
    except ImportError:
        raise ImportError("Run: pip install anthropic")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set.\n"
            "1. Copy curriculum/shared/.env.example to curriculum/shared/.env\n"
            "2. Add your key from https://console.anthropic.com"
        )
    return anthropic.Anthropic(api_key=api_key)


def get_openai_client():
    """Return a configured OpenAI client. Raises clearly if key is missing."""
    try:
        import openai
    except ImportError:
        raise ImportError("Run: pip install openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not set.\n"
            "1. Copy curriculum/shared/.env.example to curriculum/shared/.env\n"
            "2. Add your key from https://platform.openai.com"
        )
    return openai.OpenAI(api_key=api_key)


def simple_chat(prompt: str, model: str = "claude-haiku-4-5-20251001", system: Optional[str] = None) -> str:
    """
    Single-turn chat with Claude. Returns the text response.

    Args:
        prompt: The user message
        model: Claude model ID (default: haiku for cost efficiency in labs)
        system: Optional system prompt

    Returns:
        The assistant's text response
    """
    client = get_anthropic_client()
    messages = [{"role": "user", "content": prompt}]
    kwargs = {"model": model, "max_tokens": 1024, "messages": messages}
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)
    return response.content[0].text


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count the number of tokens in a string using tiktoken.

    Args:
        text: Input string
        model: Tiktoken encoding name

    Returns:
        Token count
    """
    try:
        import tiktoken
    except ImportError:
        raise ImportError("Run: pip install tiktoken")

    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-haiku-4-5-20251001",
) -> float:
    """
    Estimate API cost in USD for a given token count.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier

    Returns:
        Estimated cost in USD
    """
    pricing = {
        "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
        "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
        "claude-opus-4-6": {"input": 15.00, "output": 75.00},
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    if model not in pricing:
        raise ValueError(f"Unknown model: {model}. Add pricing to utils.py")

    rates = pricing[model]
    cost = (input_tokens / 1_000_000) * rates["input"]
    cost += (output_tokens / 1_000_000) * rates["output"]
    return round(cost, 6)


def print_response(text: str, title: str = "Response") -> None:
    """Pretty-print an LLM response using Rich."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown

        console = Console()
        console.print(Panel(Markdown(text), title=title, border_style="bright_blue"))
    except ImportError:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        print(text)
        print(f"{'='*60}\n")
