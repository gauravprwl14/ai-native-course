"""
Lab 02 — Token Counter & Cost Estimator (SOLUTION)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from utils import estimate_cost_usd
import tiktoken


def count_tokens(text: str, encoding: str = "cl100k_base") -> int:
    """Count the number of tokens in a string."""
    enc = tiktoken.get_encoding(encoding)
    return len(enc.encode(text))


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "claude-haiku-4-5-20251001") -> float:
    """Estimate the cost of an API call in USD."""
    return estimate_cost_usd(input_tokens, output_tokens, model)


def truncate_to_tokens(text: str, max_tokens: int, encoding: str = "cl100k_base") -> str:
    """Truncate text to fit within a token limit."""
    enc = tiktoken.get_encoding(encoding)
    token_ids = enc.encode(text)
    if len(token_ids) <= max_tokens:
        return text
    return enc.decode(token_ids[:max_tokens])


def tokenize(text: str, encoding: str = "cl100k_base") -> list[str]:
    """Return a list of token strings for the input text."""
    enc = tiktoken.get_encoding(encoding)
    token_ids = enc.encode(text)
    return [enc.decode([tid]) for tid in token_ids]


if __name__ == "__main__":
    sample = "The quick brown fox jumps over the lazy dog."
    print(f"Text: '{sample}'")
    print(f"Tokens: {count_tokens(sample)}")
    print(f"Token breakdown: {tokenize(sample)}")
    print(f"Cost (1000 input, 200 output, haiku): ${estimate_cost(1000, 200):.6f}")
    long_text = "word " * 1000
    truncated = truncate_to_tokens(long_text, max_tokens=50)
    print(f"\nTruncated token count: {count_tokens(truncated)}")
