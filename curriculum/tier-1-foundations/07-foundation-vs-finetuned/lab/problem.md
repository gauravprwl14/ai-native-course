# Lab 07: Compare Model Outputs on the Same Task

## Problem Statement

Run the same sentiment classification task across multiple Claude model configurations and measure how consistently they agree.

## Functions to Implement

### `classify_sentiment(text: str, model: str = "haiku") -> str`

Classify the sentiment of a piece of text using the specified model.

- Use `get_anthropic_client()` from the shared `utils` module to obtain the Anthropic client
- Use the `MODELS` dict to look up the model ID from the `model` key
- Use `SENTIMENT_PROMPT` as the user message template, formatting in `text`
- Call the API with `temperature=0` for deterministic output
- Return the response text stripped of whitespace and lowercased
- The return value must be one of: `"positive"`, `"negative"`, `"neutral"`

### `compare_model_outputs(texts: list[str], models: list[str] = None) -> dict`

Run the classification task on every text using every specified model.

- If `models` is `None`, default to all keys in the `MODELS` dict
- For each model, classify each text in order
- Return a dict mapping model name to a list of results: `{model_name: [result1, result2, ...]}`
- The list length must equal the number of input texts

### `calculate_agreement_rate(results: dict) -> float`

Compute the fraction of texts where all models returned the same label.

- `results` is the dict returned by `compare_model_outputs`
- For each text index, check whether all models produced identical output
- Return `count_agreed / total_texts` as a float between 0.0 and 1.0
- If there is only one model, all texts trivially agree — return 1.0

## Acceptance Criteria

- `classify_sentiment` returns one of "positive", "negative", "neutral"
- `classify_sentiment` calls the API with `temperature=0`
- `compare_model_outputs` returns a dict with one key per model
- Each value is a list of the same length as `texts`
- `calculate_agreement_rate` returns `1.0` when all models agree on every text
- `calculate_agreement_rate` returns `0.0` when no models agree on any text
- `calculate_agreement_rate` returns `0.5` when models agree on exactly half the texts
- All tests pass: `pytest tests/ -v`
