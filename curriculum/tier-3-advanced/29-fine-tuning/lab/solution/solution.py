"""Lab 29: Prepare a Fine-tuning Dataset — Solution"""
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
    Returns {"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}
    """
    client = get_anthropic_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=(
            "You generate customer service training examples. "
            "Respond ONLY with a valid JSON object in this exact format, no extra text: "
            '{"user": "customer question here", "assistant": "helpful response here"}'
        ),
        messages=[{
            "role": "user",
            "content": f"Generate a customer service training example about: {topic}"
        }]
    )
    text = response.content[0].text.strip()
    data = json.loads(text)
    return {
        "messages": [
            {"role": "user", "content": data["user"]},
            {"role": "assistant", "content": data["assistant"]},
        ]
    }


def validate_jsonl_example(example: dict) -> tuple[bool, str]:
    """
    Validate a single fine-tuning example.
    Returns (True, "") if valid, or (False, "error message") if not.
    """
    if not isinstance(example, dict):
        return False, "Example must be a dict"

    if "messages" not in example:
        return False, "Missing 'messages' key"

    messages = example["messages"]
    if not isinstance(messages, list):
        return False, "'messages' must be a list"

    if len(messages) < 2:
        return False, "'messages' must contain at least 2 items"

    valid_roles = {"user", "assistant", "system"}
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return False, f"Message {i} must be a dict"
        if "role" not in msg:
            return False, f"Message {i} missing 'role'"
        if "content" not in msg:
            return False, f"Message {i} missing 'content'"
        if msg["role"] not in valid_roles:
            return False, f"Message {i} has invalid role: {msg['role']!r}"
        if not isinstance(msg["content"], str) or not msg["content"].strip():
            return False, f"Message {i} has empty or non-string content"

    if messages[-1]["role"] != "assistant":
        return False, "Last message must be from 'assistant'"

    return True, ""


def create_training_dataset(topics: list[str], n_per_topic: int = 3) -> list[dict]:
    """
    Generate n_per_topic examples per topic. Return only validated examples.
    """
    examples = []
    for topic in topics:
        for _ in range(n_per_topic):
            try:
                example = generate_training_example(topic)
                ok, _ = validate_jsonl_example(example)
                if ok:
                    examples.append(example)
            except Exception:
                pass
    return examples


def split_dataset(
    examples: list[dict],
    val_ratio: float = 0.1,
) -> tuple[list[dict], list[dict]]:
    """
    Shuffle with seed=42 and split into (train, val).
    """
    shuffled = examples.copy()
    random.Random(42).shuffle(shuffled)
    split_idx = max(1, int(len(shuffled) * (1 - val_ratio)))
    return shuffled[:split_idx], shuffled[split_idx:]
