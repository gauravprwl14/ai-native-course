"""
Lab 39 — Cost Estimator CLI
----------------------------
Fill in the TODOs to complete this lab.

Run:  python solution.py
Test: cd .. && pytest tests/ -v
"""

import tiktoken

# Per-model pricing (USD per 1,000,000 tokens)
MODEL_PRICING = {
    "claude-3-haiku-20240307":    {"input": 0.25,  "output": 1.25},
    "claude-3-5-sonnet-20241022": {"input": 3.0,   "output": 15.0},
    "gpt-4o-mini":                {"input": 0.15,  "output": 0.60},
    "gpt-4o":                     {"input": 5.0,   "output": 15.0},
}


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken.

    Args:
        text:  The input string to count tokens for.
        model: tiktoken encoding name (use "cl100k_base" as fallback for all models).

    Returns:
        Number of tokens as an integer.
    """
    # TODO: Load the tiktoken encoding using tiktoken.get_encoding(model)
    # Hint: enc = tiktoken.get_encoding(model)
    # TODO: Encode the text and return the length of the token list
    # Hint: return len(enc.encode(text))
    pass


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> dict:
    """Estimate cost for a model given token counts.

    Args:
        input_tokens:  Number of input tokens.
        output_tokens: Number of output tokens.
        model:         Model identifier string (must be a key in MODEL_PRICING).

    Returns:
        dict with keys: model, input_tokens, output_tokens,
                        input_cost, output_cost, total_cost
    """
    # TODO: Look up pricing for the model in MODEL_PRICING
    #       If model is not found, use the first model's pricing as a default
    # TODO: Calculate input_cost:  input_tokens / 1_000_000 * input_price
    # TODO: Calculate output_cost: output_tokens / 1_000_000 * output_price
    # TODO: Return a dict with keys:
    #         model, input_tokens, output_tokens, input_cost, output_cost, total_cost
    pass


def format_cost_table(estimates: list[dict]) -> str:
    """Format a list of cost estimates as a human-readable text table.

    Args:
        estimates: List of dicts returned by estimate_cost().

    Returns:
        A formatted string with a header row, separator row, and one row per estimate.
        The header must contain the word 'Model'.
    """
    # TODO: Create header row with columns:
    #         Model | Input Tokens | Output Tokens | Input Cost | Output Cost | Total Cost
    # TODO: Create a separator row of dashes (-------)
    # TODO: Format each estimate dict as a row in the table
    # TODO: Return the full table as a single string (join rows with newlines)
    pass


def estimate_all_models(text: str, estimated_output_tokens: int = 500) -> list[dict]:
    """Estimate cost across all models in MODEL_PRICING for the given text.

    Args:
        text:                    The prompt/context text to evaluate.
        estimated_output_tokens: Assumed number of output tokens for the response.

    Returns:
        A list of estimate dicts (one per model), sorted by total_cost ascending.
    """
    # TODO: Count input tokens for the text using count_tokens()
    # TODO: For each model in MODEL_PRICING, call estimate_cost() and collect results
    # TODO: Sort the list by total_cost ascending
    # TODO: Return the sorted list
    pass


if __name__ == "__main__":
    sample_text = (
        "You are a helpful assistant. The user is asking about the history of the "
        "Roman Empire. Please provide a detailed and accurate answer covering the "
        "founding, expansion, and fall of Rome."
    )

    print("=== LLM Cost Estimator ===\n")
    print(f"Input text ({count_tokens(sample_text)} tokens):\n'{sample_text[:80]}...'\n")

    estimates = estimate_all_models(sample_text, estimated_output_tokens=500)
    print(format_cost_table(estimates))
