# Chapter 43 Lab — Ollama Client Wrapper

## Goal

Build a robust `OllamaClient` that communicates with a local Ollama instance using only Python's standard library (`urllib`). The client must handle both streaming and non-streaming responses, and fall back gracefully when Ollama is not running.

## Tasks

1. **`OllamaClient.is_available()`** — Check if the Ollama server is reachable by making a GET request to `/api/tags`. Return `True` on success, `False` on any connection error.

2. **`OllamaClient.list_models()`** — Fetch the list of locally available models from `/api/tags`. Parse the response JSON and return a list of `OllamaModel` dataclass instances, each with `name`, `size`, and `digest` fields.

3. **`OllamaClient.generate(model, prompt, stream=False)`** — Send a prompt to the model via POST `/api/generate`.
   - When `stream=False`: parse the single JSON response object and return `response["response"]`.
   - When `stream=True`: read the response body line by line. Each line is a JSON object with a `"response"` field (a token) and a `"done"` field. Concatenate all `"response"` values until `done` is `True`.

4. **`OllamaClient.pull_model(model_name)`** — Pull a model from the Ollama registry by POSTing to `/api/pull` with `{"name": model_name, "stream": false}`. Return `True` on success, `False` on error.

5. **`get_client_with_fallback(base_url)`** — Create an `OllamaClient`, call `is_available()`, and return a tuple `(client, is_available_bool)`.

## Constraints

- Use only Python standard library — no `requests`, no `httpx`.
- All HTTP is via `urllib.request`.
- Tests use `unittest.mock` and do not require a running Ollama instance.

## Expected Behaviour

```python
client, available = get_client_with_fallback()
if available:
    models = client.list_models()
    response = client.generate("llama3.2:3b", "What is 2+2?")
    print(response)  # "4"
else:
    print("Ollama not running — use a stub fallback")
```

## Files

| File | Purpose |
|------|---------|
| `starter/solution.py` | Skeleton with `# TODO:` comments |
| `solution/solution.py` | Reference implementation |
| `tests/test_solution.py` | Pytest tests (mocked, no real Ollama) |
