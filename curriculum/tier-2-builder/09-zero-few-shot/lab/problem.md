# Lab 09 — Zero/Few-shot Prompting: Problem Statement

## Overview

Build a sentiment classifier that compares zero-shot vs few-shot prompting accuracy.

You will implement four functions in `starter/solution.py`.

---

## Function 1: `classify_zero_shot(text: str) -> str`

Classify the sentiment of `text` using a zero-shot prompt (no examples).

**Requirements:**
- Format `ZERO_SHOT_PROMPT` with the input text
- Call the Anthropic API with `temperature=0` and `max_tokens=10`
- Return the sentiment label as a lowercase, stripped string: `"positive"`, `"negative"`, or `"neutral"`

**Example:**
```python
classify_zero_shot("The product arrived broken.")
# returns: "negative"
```

---

## Function 2: `build_few_shot_prompt(examples: list[dict], text: str) -> str`

Build a formatted few-shot prompt string from a list of examples and an input text.

**Requirements:**
- Each example is a dict with `"text"` and `"label"` keys
- Format each example as:
  ```
  Text: {text}
  Sentiment: {label}
  ```
- Join multiple examples with double newlines (`\n\n`)
- Insert the formatted examples string into `FEW_SHOT_TEMPLATE`
- The final prompt must also contain the input `text`

**Example:**
```python
examples = [
    {"text": "Great product!", "label": "positive"},
    {"text": "Broken on arrival.", "label": "negative"},
]
prompt = build_few_shot_prompt(examples, "Okay I guess.")
# prompt contains "Great product!" and "Okay I guess."
```

---

## Function 3: `classify_few_shot(text: str, examples: list[dict]) -> str`

Classify the sentiment of `text` using a few-shot prompt built from `examples`.

**Requirements:**
- Call `build_few_shot_prompt(examples, text)` to construct the prompt
- Call the Anthropic API with `temperature=0` and `max_tokens=10`
- Return the sentiment label as a lowercase, stripped string

**Example:**
```python
examples = [
    {"text": "Best purchase ever!", "label": "positive"},
    {"text": "Arrived two weeks late.", "label": "negative"},
    {"text": "It's fine, nothing special.", "label": "neutral"},
    {"text": "Absolutely love it.", "label": "positive"},
    {"text": "Terrible service.", "label": "negative"},
]
classify_few_shot("Yeah, great — waited 3 hours.", examples)
# returns: "negative"  (sarcasm correctly detected with examples)
```

---

## Function 4: `evaluate_accuracy(predictions: list[str], labels: list[str]) -> float`

Calculate the accuracy of a list of predictions against ground truth labels.

**Requirements:**
- Count the number of positions where `predictions[i] == labels[i]`
- Divide by the total number of items
- Return a float between `0.0` and `1.0`

**Examples:**
```python
evaluate_accuracy(["positive", "negative"], ["positive", "negative"])
# returns: 1.0

evaluate_accuracy(["positive", "positive"], ["negative", "neutral"])
# returns: 0.0

evaluate_accuracy(["positive", "negative", "positive", "neutral"],
                  ["positive", "positive", "positive", "neutral"])
# returns: 0.75
```

---

## Running Your Solution

```bash
cd curriculum/tier-2-builder/09-zero-few-shot/lab/starter
python solution.py
```

## Running Tests

```bash
cd curriculum/tier-2-builder/09-zero-few-shot/lab
pytest tests/ -v
```
