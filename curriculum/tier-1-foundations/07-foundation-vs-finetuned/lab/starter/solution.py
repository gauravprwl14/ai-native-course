"""Lab 07: Compare Foundation vs Fine-tuned Model Outputs"""
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

    # TODO:
    # Use get_anthropic_client() to call the specified model
    # Look up the model ID using MODELS[model]
    # Format SENTIMENT_PROMPT with the text
    # Use temperature=0 for deterministic output
    # Return the response text stripped and lowercased
    """
    raise NotImplementedError("Implement classify_sentiment")


def compare_model_outputs(texts: list[str], models: list[str] = None) -> dict:
    """
    Run the same classification task on multiple texts using multiple models.

    Returns: {model_name: [result1, result2, ...]}

    # TODO:
    # If models is None, default to list(MODELS.keys())
    # For each model, classify each text in order
    # Return dict mapping model name to list of results
    """
    raise NotImplementedError("Implement compare_model_outputs")


def calculate_agreement_rate(results: dict) -> float:
    """
    Calculate how often all models agree on the same classification.

    Args:
        results: {model_name: [result1, result2, ...]} from compare_model_outputs

    Returns: fraction (0.0-1.0) of texts where all models agreed

    # TODO:
    # Get the list of model names from results
    # Determine total_texts from the length of any value list
    # For each text index, check if all models returned the same result
    # Return count_agreed / total_texts
    """
    raise NotImplementedError("Implement calculate_agreement_rate")
