"""Lab 09: Zero/Few-shot Prompting (SOLUTION)
---------------------------------------------
Reference implementation. Try the starter version first!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

ZERO_SHOT_PROMPT = """Classify the sentiment of the following text.
Respond with exactly one word: positive, negative, or neutral.

Text: {text}
Sentiment:"""

FEW_SHOT_TEMPLATE = """Classify the sentiment of text. Respond with exactly one word: positive, negative, or neutral.

Examples:
{examples}

Text: {text}
Sentiment:"""


def classify_zero_shot(text: str) -> str:
    """Classify sentiment using zero-shot prompting."""
    client = get_anthropic_client()
    prompt = ZERO_SHOT_PROMPT.format(text=text)
    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip().lower()


def build_few_shot_prompt(examples: list[dict], text: str) -> str:
    """Build a few-shot prompt string from examples and input text."""
    formatted = []
    for ex in examples:
        formatted.append(f"Text: {ex['text']}\nSentiment: {ex['label']}")
    examples_str = "\n\n".join(formatted)
    return FEW_SHOT_TEMPLATE.format(examples=examples_str, text=text)


def classify_few_shot(text: str, examples: list[dict]) -> str:
    """Classify sentiment using few-shot prompting."""
    client = get_anthropic_client()
    prompt = build_few_shot_prompt(examples, text)
    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip().lower()


def evaluate_accuracy(predictions: list[str], labels: list[str]) -> float:
    """Calculate accuracy of predictions vs ground truth labels."""
    if not labels:
        return 0.0
    matches = sum(1 for p, l in zip(predictions, labels) if p == l)
    return matches / len(labels)


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

EXAMPLES = [
    {"text": "Best purchase I've made this year!", "label": "positive"},
    {"text": "Arrived damaged and two weeks late.", "label": "negative"},
    {"text": "It's fine, does what it says.", "label": "neutral"},
    {"text": "Absolutely love it, exceeded expectations.", "label": "positive"},
    {"text": "Terrible customer service, won't buy again.", "label": "negative"},
]

TEST_INPUTS = [
    ("The product is amazing, highly recommend.", "positive"),
    ("Broken on arrival, very disappointed.", "negative"),
    ("It works okay, nothing special.", "neutral"),
    ("Yeah, great service — waited 3 hours.", "negative"),  # sarcasm
]

if __name__ == "__main__":
    print("=" * 60)
    print("Zero-shot vs Few-shot Sentiment Classification")
    print("=" * 60)

    zero_preds = []
    few_preds = []
    true_labels = []

    for text, label in TEST_INPUTS:
        z = classify_zero_shot(text)
        f = classify_few_shot(text, EXAMPLES)
        zero_preds.append(z)
        few_preds.append(f)
        true_labels.append(label)
        print(f"\nText:       {text}")
        print(f"True label: {label}")
        print(f"Zero-shot:  {z}  {'✓' if z == label else '✗'}")
        print(f"Few-shot:   {f}  {'✓' if f == label else '✗'}")

    zero_acc = evaluate_accuracy(zero_preds, true_labels)
    few_acc = evaluate_accuracy(few_preds, true_labels)

    print("\n" + "=" * 60)
    print(f"Zero-shot accuracy: {zero_acc:.0%}")
    print(f"Few-shot accuracy:  {few_acc:.0%}")
    print("=" * 60)
