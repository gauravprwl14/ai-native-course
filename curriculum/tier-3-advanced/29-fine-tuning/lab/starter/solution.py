"""Lab 29: Prepare a Fine-tuning Dataset"""
import sys
import json
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def generate_training_example(topic: str) -> dict:
    """
    Use an LLM to generate one JSONL fine-tuning example for a customer service bot.

    The example should be in the format:
        {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

    Steps:
    1. Call the LLM with a prompt asking for a JSON object with "user" and "assistant" keys
    2. Parse the response as JSON
    3. Wrap it in the messages format

    # TODO: call client.messages.create(), parse JSON from response, return messages dict
    """
    raise NotImplementedError("Implement generate_training_example")


def validate_jsonl_example(example: dict) -> tuple[bool, str]:
    """
    Validate a single fine-tuning example.

    Returns (True, "") if valid.
    Returns (False, "error message") if invalid.

    Checks:
    - example is a dict
    - "messages" key exists
    - "messages" is a list with at least 2 items
    - each message has "role" and "content"
    - each role is one of: "user", "assistant", "system"
    - each content is a non-empty string
    - last message role is "assistant"

    # TODO: implement all checks; return (True, "") or (False, "error message")
    """
    raise NotImplementedError("Implement validate_jsonl_example")


def create_training_dataset(topics: list[str], n_per_topic: int = 3) -> list[dict]:
    """
    Generate n_per_topic examples per topic and return only the valid ones.

    Steps:
    1. For each topic, call generate_training_example() n_per_topic times
    2. Validate each example with validate_jsonl_example()
    3. Only include examples that pass validation
    4. Return the collected valid examples

    # TODO: loop over topics and counts, generate, validate, collect valid examples
    """
    raise NotImplementedError("Implement create_training_dataset")


def split_dataset(
    examples: list[dict],
    val_ratio: float = 0.1,
) -> tuple[list[dict], list[dict]]:
    """
    Shuffle examples (with seed=42) and split into train and validation sets.

    Returns (train_examples, val_examples).

    Steps:
    1. Make a copy of examples
    2. Shuffle with random.Random(42) for deterministic results
    3. Calculate split index: int(len * (1 - val_ratio)), minimum 1
    4. Return (examples[:split_idx], examples[split_idx:])

    # TODO: copy, shuffle with seed=42, split by val_ratio, return (train, val)
    """
    raise NotImplementedError("Implement split_dataset")
