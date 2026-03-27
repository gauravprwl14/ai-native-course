"""
Lab 04 — Compare Outputs at Different Temperatures (SOLUTION)
--------------------------------------------------------------
Reference implementation — fully working.
"""

import sys
import json
from pathlib import Path

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
    """
    client = anthropic.Anthropic()
    responses = []

    for _ in range(n):
        response = client.messages.create(
            model=MODEL,
            max_tokens=300,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        responses.append(response.content[0].text)

    return responses


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
    """
    results = {}
    for temp in temperatures:
        results[temp] = generate_at_temperature(prompt, temp, n=3)
    return results


def is_valid_json_output(text: str) -> bool:
    """
    Check whether `text` is valid JSON.

    Args:
        text: The string to validate

    Returns:
        True if json.loads(text) succeeds, False otherwise
    """
    try:
        json.loads(text)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Manual smoke test
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
