"""
Lab 39 — Cost Estimator CLI (SOLUTION)
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
    """Count tokens in text using tiktoken."""
    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))


def estimate_cost(input_tokens: int, output_tokens: int, model: str) -> dict:
    """Estimate cost for a model given token counts."""
    # Fall back to first model's pricing if model not found
    pricing = MODEL_PRICING.get(model, list(MODEL_PRICING.values())[0])

    input_cost = input_tokens / 1_000_000 * pricing["input"]
    output_cost = output_tokens / 1_000_000 * pricing["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }


def format_cost_table(estimates: list[dict]) -> str:
    """Format a list of cost estimates as a human-readable text table."""
    col_model = 30
    col_tokens = 14
    col_cost = 12

    header = (
        f"{'Model':<{col_model}} "
        f"{'Input Tokens':>{col_tokens}} "
        f"{'Output Tokens':>{col_tokens}} "
        f"{'Input Cost':>{col_cost}} "
        f"{'Output Cost':>{col_cost}} "
        f"{'Total Cost':>{col_cost}}"
    )
    separator = "-" * len(header)

    rows = [header, separator]
    for e in estimates:
        row = (
            f"{e['model']:<{col_model}} "
            f"{e['input_tokens']:>{col_tokens},} "
            f"{e['output_tokens']:>{col_tokens},} "
            f"${e['input_cost']:>{col_cost - 1}.6f} "
            f"${e['output_cost']:>{col_cost - 1}.6f} "
            f"${e['total_cost']:>{col_cost - 1}.6f}"
        )
        rows.append(row)

    return "\n".join(rows)


def estimate_all_models(text: str, estimated_output_tokens: int = 500) -> list[dict]:
    """Estimate cost across all models in MODEL_PRICING for the given text."""
    input_tokens = count_tokens(text)
    estimates = [
        estimate_cost(input_tokens, estimated_output_tokens, model)
        for model in MODEL_PRICING
    ]
    return sorted(estimates, key=lambda e: e["total_cost"])


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
