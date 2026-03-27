# Lab 06: Run Inference via API

## Overview

In this lab you will implement three functions that demonstrate the core patterns for calling an LLM inference API. You will practice single inference, batch processing, and latency measurement.

## Functions to Implement

### `run_inference(prompt: str, system_prompt: str = None) -> str`

Make a single call to the Anthropic API and return the text response.

**Requirements:**
- Call `client.messages.create()` with `model=MODEL`, `max_tokens=1024`, and `messages=[{"role": "user", "content": prompt}]`
- If `system_prompt` is provided (not None), include `system=system_prompt` in the call
- Return `response.content[0].text`

**Example:**
```python
result = run_inference("What is inference in the context of LLMs?")
# → "Inference refers to the process of using a trained model to generate..."

result = run_inference(
    prompt="Summarise in one sentence.",
    system_prompt="You are a concise technical writer. Always respond in exactly one sentence."
)
# → "Inference is the process of running a trained neural network on new inputs..."
```

---

### `batch_inference(prompts: list[str]) -> list[str]`

Run inference on a list of prompts and return a list of responses.

**Requirements:**
- Call `run_inference` for each prompt in `prompts`
- Return a list of response strings in the same order as the input
- The returned list must have the same length as the input list

**Example:**
```python
responses = batch_inference([
    "What is training?",
    "What is inference?",
    "What is fine-tuning?"
])
# → ["Training is the process...", "Inference is the process...", "Fine-tuning is..."]
assert len(responses) == 3
```

---

### `measure_inference_latency(prompt: str, n: int = 3) -> dict`

Run inference `n` times on the same prompt and measure the latency of each run.

**Requirements:**
- Run `run_inference(prompt)` exactly `n` times
- Record wall-clock time before and after each call using `time.time()`
- Convert each duration to milliseconds (multiply by 1000)
- Return a dict with these exact keys:
  - `"avg_latency_ms"`: average latency across all runs (float)
  - `"min_ms"`: minimum latency across all runs (float)
  - `"max_ms"`: maximum latency across all runs (float)
  - `"n"`: the number of runs (int, same as the `n` parameter)

**Example:**
```python
stats = measure_inference_latency("What is 2 + 2?", n=3)
# → {"avg_latency_ms": 842.3, "min_ms": 731.1, "max_ms": 963.5, "n": 3}
assert isinstance(stats["avg_latency_ms"], float)
assert stats["n"] == 3
```

---

## Hints

- `time.time()` returns the current time in seconds as a float. To get milliseconds: `(end - start) * 1000`
- The `MODEL` constant is already defined in the starter file — use it instead of hardcoding the model name
- Use `get_anthropic_client()` from the shared utils to create the Anthropic client
- The `system` parameter in `client.messages.create()` is optional — only include it when `system_prompt` is not None

## Running Tests

```bash
cd curriculum/tier-1-foundations/06-inference-vs-training/lab
pytest tests/ -v
```
