"""
Lab 02 — Token Counter & Cost Estimator
-----------------------------------------
Fill in the TODOs to complete this lab.

Run: python solution.py
Test: cd .. && pytest tests/ -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from utils import estimate_cost_usd


def count_tokens(text: str, encoding: str = "cl100k_base") -> int:
    """
    Count the number of tokens in a string.

    Args:
        text: The input string
        encoding: tiktoken encoding name (default: cl100k_base)

    Returns:
        Number of tokens
    """
    # TODO: Import tiktoken and use it to count tokens
    # Hint: enc = tiktoken.get_encoding(encoding)
    # Then: len(enc.encode(text))
    pass


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "claude-haiku-4-5-20251001") -> float:
    """
    Estimate the cost of an API call in USD.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model identifier

    Returns:
        Estimated cost in USD
    """
    # TODO: Use estimate_cost_usd from shared utils
    pass


def truncate_to_tokens(text: str, max_tokens: int, encoding: str = "cl100k_base") -> str:
    """
    Truncate text to fit within a token limit.

    Args:
        text: Input text to potentially truncate
        max_tokens: Maximum number of tokens allowed
        encoding: tiktoken encoding name

    Returns:
        Original text if within limit, otherwise truncated text
    """
    # TODO:
    # 1. Encode the text to get token IDs
    # 2. If len(token_ids) <= max_tokens, return original text unchanged
    # 3. Otherwise, take the first max_tokens token IDs and decode back to string
    pass


def tokenize(text: str, encoding: str = "cl100k_base") -> list[str]:
    """
    Return a list of token strings for the input text.

    Args:
        text: Input string
        encoding: tiktoken encoding name

    Returns:
        List of token strings (each token decoded individually)
    """
    # TODO:
    # 1. Encode text to get token IDs
    # 2. Decode each token ID individually back to a string
    # Hint: enc.decode([token_id]) for each token_id
    pass


if __name__ == "__main__":
    sample = "The quick brown fox jumps over the lazy dog."

    print(f"Text: '{sample}'")
    print(f"Tokens: {count_tokens(sample)}")
    print(f"Token breakdown: {tokenize(sample)}")
    print(f"Cost (1000 input, 200 output, haiku): ${estimate_cost(1000, 200):.6f}")

    long_text = "word " * 1000
    truncated = truncate_to_tokens(long_text, max_tokens=50)
    print(f"\nTruncated (50 tokens): '{truncated[:80]}...'")
    print(f"Truncated token count: {count_tokens(truncated)}")
