"""
Lab 01 — Your First LLM API Call
---------------------------------
Fill in the TODOs below to complete this lab.

Run: python solution.py
Test: cd .. && pytest tests/ -v
"""

import sys
import os

# Add the curriculum root to path so we can import shared utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from utils import get_anthropic_client, estimate_cost_usd, print_response


def call_claude(prompt: str, temperature: float = 0.7) -> str:
    """
    Make a single API call to Claude and return the text response.

    Args:
        prompt: The user's question or instruction
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)

    Returns:
        The assistant's text response as a string
    """
    client = get_anthropic_client()

    # TODO: Call client.messages.create() with:
    # - model: "claude-haiku-4-5-20251001"
    # - max_tokens: 1024
    # - temperature: the temperature parameter
    # - messages: [{"role": "user", "content": prompt}]
    # Store the result in a variable called `response`

    # TODO: Return the text content from the response
    # Hint: response.content[0].text
    pass


def compare_temperatures(prompt: str) -> dict:
    """
    Call Claude three times with the same prompt at different temperatures.

    Args:
        prompt: The question to ask

    Returns:
        Dict with keys "0.0", "0.7", "1.0" mapping to response strings
    """
    results = {}

    # TODO: Call call_claude() three times with temperatures 0.0, 0.7, and 1.0
    # Store results in the dict with string keys "0.0", "0.7", "1.0"

    return results


def estimate_call_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Estimate the cost of an API call in USD.

    Args:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated

    Returns:
        Estimated cost in USD
    """
    # TODO: Use estimate_cost_usd() from shared utils
    # Pass model="claude-haiku-4-5-20251001"
    pass


if __name__ == "__main__":
    prompt = "Explain what a large language model is in 2-3 sentences."

    print("=" * 60)
    print("Comparing Claude responses at different temperatures")
    print("=" * 60)
    print(f"Prompt: {prompt}\n")

    # TODO: Call compare_temperatures() and print each response
    # Show: temperature value, response text
    # Hint: use print_response() from shared utils for pretty output
