"""Lab 07: Compare Foundation vs Fine-tuned Model Outputs — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODELS = {
    "haiku": "claude-3-haiku-20240307",
    "sonnet": "claude-3-5-sonnet-20241022",
}

SENTIMENT_PROMPT = """Classify the sentiment of this text as exactly one word: positive, negative, or neutral.
Text: {text}
Sentiment:"""


def classify_sentiment(text: str, model: str = "haiku") -> str:
    """
    Classify text sentiment using specified model.
    Returns "positive", "negative", or "neutral".
    """
    client = get_anthropic_client()
    response = client.messages.create(
        model=MODELS[model],
        max_tokens=10,
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": SENTIMENT_PROMPT.format(text=text),
            }
        ],
    )
    return response.content[0].text.strip().lower()


def compare_model_outputs(texts: list[str], models: list[str] = None) -> dict:
    """
    Run the same classification task on multiple texts using multiple models.

    Returns: {model_name: [result1, result2, ...]}
    """
    if models is None:
        models = list(MODELS.keys())

    results = {}
    for model_key in models:
        results[model_key] = [classify_sentiment(text, model_key) for text in texts]
    return results


def calculate_agreement_rate(results: dict) -> float:
    """
    Calculate how often all models agree on the same classification.

    Args:
        results: {model_name: [result1, result2, ...]} from compare_model_outputs

    Returns: fraction (0.0-1.0) of texts where all models agreed
    """
    model_keys = list(results.keys())
    if len(model_keys) == 0:
        return 0.0
    if len(model_keys) == 1:
        return 1.0

    total_texts = len(results[model_keys[0]])
    if total_texts == 0:
        return 0.0

    count_agreed = sum(
        len({results[m][i] for m in model_keys}) == 1
        for i in range(total_texts)
    )
    return count_agreed / total_texts
