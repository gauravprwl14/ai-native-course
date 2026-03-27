"""Lab 31: DPO Dataset Construction — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

GOOD_RESPONSE_PROMPT = """Answer the following question clearly, accurately, and helpfully.
Provide a complete, well-structured response.

Question: {prompt}"""

DEGRADATION_PROMPT = """You are helping construct a preference dataset for AI alignment training.

Given a prompt and a high-quality response, generate a WORSE version of the response.
The worse version should be realistic — something a less capable model might produce.
Make it vague, incomplete, or subtly inaccurate. Do NOT make it obviously nonsensical.

Prompt: {prompt}

High-quality response:
{chosen}

Generate a worse version (rejected response):"""


def create_preference_pair(prompt: str, chosen: str, rejected: str) -> dict:
    """Returns {"prompt": str, "chosen": str, "rejected": str}"""
    return {
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
    }


def validate_preference_pair(pair: dict) -> tuple[bool, list[str]]:
    """Validate DPO pair. Returns (valid, errors).
    Checks: all keys exist, none are empty, chosen != rejected.
    """
    errors = []
    required_keys = ["prompt", "chosen", "rejected"]

    # Check all required keys are present
    for key in required_keys:
        if key not in pair:
            errors.append(f"missing key: '{key}'")

    if errors:
        # Can't do further checks without all keys
        return False, errors

    # Check none are empty
    for key in required_keys:
        if not pair[key].strip():
            errors.append(f"'{key}' must not be empty")

    # Check chosen != rejected
    if pair["chosen"].strip() == pair["rejected"].strip():
        errors.append("chosen and rejected must differ")

    return len(errors) == 0, errors


def generate_rejection(prompt: str, chosen: str) -> str:
    """Use LLM to generate a deliberately worse version of the chosen response."""
    client = get_anthropic_client()
    formatted = DEGRADATION_PROMPT.format(prompt=prompt, chosen=chosen)
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0.7,
        messages=[{"role": "user", "content": formatted}]
    )
    return response.content[0].text.strip()


def build_dpo_dataset(prompts: list[str]) -> list[dict]:
    """For each prompt, generate a chosen response and a rejected response.
    Returns a list of valid (prompt, chosen, rejected) dicts.
    """
    client = get_anthropic_client()
    dataset = []

    for prompt in prompts:
        # Step 1: Generate a high-quality chosen response
        chosen_prompt = GOOD_RESPONSE_PROMPT.format(prompt=prompt)
        chosen_response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            temperature=0,
            messages=[{"role": "user", "content": chosen_prompt}]
        )
        chosen = chosen_response.content[0].text.strip()

        # Step 2: Generate a worse rejected response
        rejected = generate_rejection(prompt, chosen)

        # Step 3: Assemble and validate the pair
        pair = create_preference_pair(prompt, chosen, rejected)
        valid, _ = validate_preference_pair(pair)
        if valid:
            dataset.append(pair)

    return dataset


if __name__ == "__main__":
    test_prompts = [
        "What is the difference between supervised and unsupervised learning?",
        "Explain what a transformer neural network does.",
    ]

    print("Building DPO dataset...")
    dataset = build_dpo_dataset(test_prompts)
    print(f"\nBuilt {len(dataset)} preference pairs\n")

    for i, pair in enumerate(dataset):
        print(f"--- Pair {i + 1} ---")
        print(f"Prompt:   {pair['prompt'][:80]}")
        print(f"Chosen:   {pair['chosen'][:120]}...")
        print(f"Rejected: {pair['rejected'][:120]}...")
        print()
