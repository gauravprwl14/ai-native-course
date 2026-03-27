"""
Lab 01 — Your First LLM API Call (SOLUTION)
--------------------------------------------
Reference implementation. Try the starter version first!
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))

from utils import get_anthropic_client, estimate_cost_usd, print_response


def call_claude(prompt: str, temperature: float = 0.7) -> str:
    """Make a single API call to Claude and return the text response."""
    client = get_anthropic_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def compare_temperatures(prompt: str) -> dict:
    """Call Claude three times with the same prompt at different temperatures."""
    results = {}
    for temp in [0.0, 0.7, 1.0]:
        results[str(temp)] = call_claude(prompt, temperature=temp)
    return results


def estimate_call_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate the cost of an API call in USD."""
    return estimate_cost_usd(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model="claude-haiku-4-5-20251001"
    )


if __name__ == "__main__":
    prompt = "Explain what a large language model is in 2-3 sentences."

    print("=" * 60)
    print("Comparing Claude responses at different temperatures")
    print("=" * 60)
    print(f"Prompt: {prompt}\n")

    results = compare_temperatures(prompt)
    for temp, response in results.items():
        print_response(response, title=f"Temperature = {temp}")
