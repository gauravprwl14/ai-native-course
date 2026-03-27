"""
Lab 04 — Compare Outputs at Different Temperatures
----------------------------------------------------
Temperature controls how "random" the LLM's output is:
  - temperature=0.0 → deterministic (same output every time)
  - temperature=1.0 → natural variation
  - temperature=2.0 → chaotic, often incoherent

Your job: implement the three functions below.

Run:  python solution.py
Test: cd .. && pytest tests/ -v
"""

import sys
import os
import json
from pathlib import Path

# Make the anthropic package importable from the shared environment
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import anthropic

MODEL = "claude-haiku-4-5-20251001"


def generate_at_temperature(prompt: str, temperature: float, n: int = 3) -> list[str]:
    """
    Generate n responses from the API using the given temperature.

    Args:
        prompt: The user message to send to the model
        temperature: Sampling temperature (0.0 to 2.0)
        n: Number of separate API calls to make (default 3)

    Returns:
        A list of n response strings

    TODO:
        1. Create an Anthropic client: client = anthropic.Anthropic()
        2. Create an empty list `responses = []`
        3. Loop `n` times:
           a. Call client.messages.create() with:
              - model=MODEL
              - max_tokens=300
              - temperature=temperature   ← pass it through exactly
              - messages=[{"role": "user", "content": prompt}]
           b. Extract the text: response.content[0].text
           c. Append the text to `responses`
        4. Return `responses`
    """
    raise NotImplementedError("TODO: implement generate_at_temperature")


def compare_temperatures(
    prompt: str,
    temperatures: list[float] = [0.0, 0.5, 1.0],
) -> dict[float, list[str]]:
    """
    Run the same prompt at each temperature and collect all responses.

    Args:
        prompt: The user message to send
        temperatures: List of temperature values to compare

    Returns:
        A dict mapping each temperature to a list of 3 response strings.
        Example: {0.0: ["resp1", "resp2", "resp3"], 0.5: [...], 1.0: [...]}

    TODO:
        1. Create an empty dict `results = {}`
        2. For each `temp` in `temperatures`:
           a. Call generate_at_temperature(prompt, temp, n=3)
           b. Store the returned list in results[temp]
        3. Return `results`
    """
    raise NotImplementedError("TODO: implement compare_temperatures")


def is_valid_json_output(text: str) -> bool:
    """
    Check whether `text` is valid JSON.

    Args:
        text: The string to validate

    Returns:
        True if json.loads(text) succeeds, False otherwise

    TODO:
        1. Try to call json.loads(text) inside a try/except block
        2. If it succeeds (no exception), return True
        3. If any exception is raised (json.JSONDecodeError, TypeError, etc.), return False
    """
    raise NotImplementedError("TODO: implement is_valid_json_output")


# ---------------------------------------------------------------------------
# Manual smoke test — run this to see your functions in action
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_prompt = "Name one planet in our solar system."

    print("=== generate_at_temperature (temp=0.0, n=3) ===")
    responses = generate_at_temperature(test_prompt, temperature=0.0, n=3)
    for i, r in enumerate(responses, 1):
        print(f"  [{i}] {r.strip()}")

    print("\n=== generate_at_temperature (temp=1.2, n=3) ===")
    responses = generate_at_temperature(test_prompt, temperature=1.2, n=3)
    for i, r in enumerate(responses, 1):
        print(f"  [{i}] {r.strip()}")

    print("\n=== compare_temperatures ===")
    results = compare_temperatures(test_prompt, temperatures=[0.0, 0.5, 1.0])
    for temp, resps in results.items():
        print(f"  temp={temp}: {[r.strip() for r in resps]}")

    print("\n=== is_valid_json_output ===")
    print(f'  valid JSON:   {is_valid_json_output(\'{"key": "value"}\')!r}')
    print(f'  invalid JSON: {is_valid_json_output("not json")!r}')
    print(f'  empty string: {is_valid_json_output("")!r}')
