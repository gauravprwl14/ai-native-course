# Lab 11 — System Prompts: Customer Service Bot

## Overview

You will build a configurable customer service chatbot backed by the Anthropic API. The bot's behavior is entirely controlled by a system prompt you write. You'll also implement a lightweight LLM-powered topic classifier to gate off-topic requests.

---

## Background

System prompts are the most powerful tool for controlling model behavior in production. Every serious LLM application starts with one. In this lab you'll:

1. Write a structured system prompt from scratch
2. Manage multi-turn conversation history correctly
3. Use the LLM as a classifier (the `is_on_topic` function)

---

## Functions to Implement

### `create_customer_service_bot(company_name, product_type) -> dict`

Create and return a bot configuration dictionary containing:
- `"system_prompt"`: A detailed system prompt string that:
  - Sets the persona as a customer service representative for `company_name`
  - Provides context about the `product_type`
  - Instructs the model to be helpful, concise, and professional
  - Instructs the model to politely decline off-topic questions
  - Specifies response format: plain text only, no markdown, maximum 3 sentences
- `"company"`: The `company_name` string
- `"product"`: The `product_type` string

Your system prompt should follow the five-part anatomy from the course:
`Role → Context → Instructions → Constraints → Output Format`

---

### `chat(bot_config, user_message, history) -> (str, list)`

Send one turn of conversation to the configured bot.

Steps:
1. Get an Anthropic client using `get_anthropic_client()` from shared utils
2. Append the user message to history: `{"role": "user", "content": user_message}`
3. Call the API with:
   - `system=bot_config["system_prompt"]`
   - `messages=history`
   - `temperature=0.3`
   - `max_tokens=512`
4. Extract the response text from `response.content[0].text`
5. Append the assistant response to history: `{"role": "assistant", "content": response_text}`
6. Return `(response_text, updated_history)`

---

### `is_on_topic(user_message, allowed_topics) -> bool`

Use the LLM to classify whether a user message is relevant to the allowed topics.

Steps:
1. Build a classification prompt that:
   - Lists the `allowed_topics`
   - Asks: "Is this message about one of these topics: [topics]? Reply with only 'yes' or 'no'."
   - Includes the `user_message` to classify
2. Call the API (use `temperature=0` for deterministic classification)
3. Return `True` if the response text contains `"yes"` (case-insensitive), `False` otherwise

---

## Running Your Solution

```bash
cd curriculum/tier-2-builder/11-system-prompts/lab/starter
export ANTHROPIC_API_KEY=your_key_here
python solution.py
```

## Running Tests

```bash
cd curriculum/tier-2-builder/11-system-prompts/lab
pytest tests/ -v
```

Tests use `unittest.mock` — no real API calls are made during testing.

---

## Example Usage

```python
# Create the bot
bot = create_customer_service_bot("Acme Corp", "cloud storage")

# Start a conversation
reply, history = chat(bot, "How do I reset my password?", [])
print(reply)
# Expected: A helpful, professional response about password reset, plain text, ≤3 sentences

reply, history = chat(bot, "Tell me about cryptocurrency", history)
print(reply)
# Expected: A polite decline explaining the bot only covers cloud storage topics

# Topic classification
print(is_on_topic("How do I upgrade my plan?", ["billing", "account management"]))
# Expected: True

print(is_on_topic("What's the best programming language?", ["billing", "account management"]))
# Expected: False
```
