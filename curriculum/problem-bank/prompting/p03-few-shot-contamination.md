# Few-Shot Contamination

**Category:** prompting
**Difficulty:** Medium
**Key Concepts:** few-shot contamination, distribution shift, in-context learning limitations, entity anchoring
**Time:** 25–40 min

---

## Problem Statement

You're building a sentiment classifier for product reviews. You add 5 few-shot examples to your prompt:

```
Example 1: "The iPhone camera is incredible, best I've ever used." → POSITIVE
Example 2: "My AirPods stopped working after 2 weeks. Terrible quality." → NEGATIVE
Example 3: "This iPhone case fits perfectly and ships fast." → POSITIVE
Example 4: "Battery drains in 3 hours on my MacBook. Very disappointing." → NEGATIVE
Example 5: "Great AirPods sound quality, worth every penny." → POSITIVE
```

You deploy. After one week you analyze accuracy by product segment:

| Product Segment | Accuracy |
|---|---|
| Apple products (iPhone, AirPods, MacBook) | 95% |
| Samsung products | 67% |
| Generic accessories | 71% |
| Audio equipment | 69% |

The overall accuracy looks acceptable at 76%, but the product-level breakdown reveals the bug. What's happening, and how do you fix it?

---

## What Makes This Hard

The few-shot examples look reasonable — they're balanced (3 positive, 2 negative), they cover multiple product types, and the sentiment is clear. Nothing obviously wrong.

The bug is structural, not content-based. All 5 examples happen to use Apple products (iPhone, AirPods, MacBook). The model learns two things from your examples:

1. The intended signal: sentiment words like "incredible", "terrible", "disappointing"
2. An unintended signal: Apple products are the reference class for what a review looks like

When the model encounters a Samsung review, it's classifying something that looks different from all 5 examples. The model's in-context learning is pattern-matching on surface features, not just the abstract sentiment concept.

The second non-obvious issue: adding more Samsung examples seems like the fix, but you'd need to keep adding examples for every new product category — a maintenance trap. The real fix is to make examples brand-agnostic.

---

## Naive Approach

"Add 5 Samsung examples to the few-shot set. Also add some generic product examples."

```
Example 6: "My Samsung Galaxy takes amazing photos." → POSITIVE
Example 7: "Samsung TV has terrible customer support." → NEGATIVE
...
```

**Why this fails:**

1. You now have 10 examples taking up ~500 tokens of context. At scale, this inflates input costs.
2. Every new product category entering your review stream creates a coverage gap. You'll be chasing the distribution forever.
3. The root problem — examples that anchor to specific named entities — is not fixed. You've just added more anchors.
4. Validated accuracy on your Samsung test set improves, but you haven't fixed the underlying mechanism. New product categories still underperform.

---

## Expert Approach

**Step 1: Make few-shot examples brand-agnostic**

Replace specific product names with generic placeholders. The model should learn to classify sentiment, not recognize products.

```
Example 1: "The camera on this phone is incredible, best I've ever used." → POSITIVE
Example 2: "My headphones stopped working after 2 weeks. Terrible quality." → NEGATIVE
Example 3: "This phone case fits perfectly and ships fast." → POSITIVE
Example 4: "Battery drains in 3 hours on my laptop. Very disappointing." → NEGATIVE
Example 5: "Great sound quality on these earbuds, worth every penny." → POSITIVE
```

Same sentiment, same structure, no brand anchoring. Now the pattern the model learns is purely about language.

**Step 2: Use chain-of-thought in few-shot examples**

Make the reasoning visible so the model learns the decision process, not just the surface pattern:

```
Example 1:
Review: "The camera on this phone is incredible, best I've ever used."
Reasoning: The reviewer uses "incredible" (strong positive adjective) and "best I've ever used" (superlative comparison). No negative qualifiers. Sentiment: clearly positive.
Label: POSITIVE

Example 2:
Review: "My headphones stopped working after 2 weeks. Terrible quality."
Reasoning: "Stopped working" indicates product failure. "Terrible quality" is a direct negative judgment. Time frame "2 weeks" emphasizes disappointment. Sentiment: clearly negative.
Label: NEGATIVE
```

CoT examples teach the model to attend to sentiment-bearing language (adjectives, failure words, comparisons) rather than context features like brand names.

**Step 3: Validate on an entity-disjoint held-out set**

Your validation set must not overlap with the named entities in your few-shot examples. If your few-shot examples mention iPhone, your validation set should contain zero iPhone reviews.

```python
def validate_entity_disjoint(few_shot_examples: list[str], val_set: list[str]) -> bool:
    """
    Extract named entities from few-shot examples.
    Verify none appear in validation set.
    """
    few_shot_entities = extract_entities(few_shot_examples)  # NER
    val_text = " ".join(val_set).lower()
    contaminated = [e for e in few_shot_entities if e.lower() in val_text]
    if contaminated:
        print(f"Contamination detected: {contaminated}")
        return False
    return True
```

**Step 4: Track accuracy stratified by entity presence**

Add production monitoring that breaks accuracy down by whether the input shares entities with your few-shot examples:

```python
def classify_with_entity_audit(review: str, few_shot_entities: set[str]) -> dict:
    prediction = classify(review)
    entity_overlap = any(e.lower() in review.lower() for e in few_shot_entities)
    return {
        "prediction": prediction,
        "entity_overlap": entity_overlap,
        # log both — alert if accuracy gap > 10% between groups
    }
```

This is the monitoring that would have caught this bug in production.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import anthropic
import json
import re
from collections import defaultdict

client = anthropic.Anthropic()

# BAD: Brand-anchored examples
FEW_SHOT_CONTAMINATED = """
Example 1: "The iPhone camera is incredible, best I've ever used." → POSITIVE
Example 2: "My AirPods stopped working after 2 weeks. Terrible quality." → NEGATIVE
Example 3: "This iPhone case fits perfectly and ships fast." → POSITIVE
Example 4: "Battery drains in 3 hours on my MacBook. Very disappointing." → NEGATIVE
Example 5: "Great AirPods sound quality, worth every penny." → POSITIVE
"""

# GOOD: Brand-agnostic examples with chain-of-thought
FEW_SHOT_CLEAN = """
Example 1:
Review: "The camera on this phone is incredible, best I've ever used."
Reasoning: Strong positive adjective "incredible" + superlative "best I've ever used". No negatives.
Label: POSITIVE

Example 2:
Review: "My headphones stopped working after 2 weeks. Terrible quality."
Reasoning: "Stopped working" = product failure. "Terrible quality" = direct negative judgment. Short 2-week lifespan amplifies disappointment.
Label: NEGATIVE

Example 3:
Review: "This phone case fits perfectly and ships fast."
Reasoning: "Fits perfectly" + "ships fast" are both positive functional outcomes. No negatives.
Label: POSITIVE

Example 4:
Review: "Battery drains in 3 hours on my laptop. Very disappointing."
Reasoning: "Drains in 3 hours" describes poor performance. "Very disappointing" is explicit negative sentiment.
Label: NEGATIVE

Example 5:
Review: "Great sound quality on these earbuds, worth every penny."
Reasoning: "Great sound quality" is positive quality assessment. "Worth every penny" signals value satisfaction.
Label: POSITIVE
"""

SYSTEM_PROMPT_TEMPLATE = """You are a sentiment classifier for product reviews.

Classify each review as POSITIVE or NEGATIVE.

{few_shot_examples}

Now classify the following review. Show your reasoning, then output the label.

Review: {review}
Reasoning:"""

def classify_review(review: str, use_clean_examples: bool = True) -> dict:
    examples = FEW_SHOT_CLEAN if use_clean_examples else FEW_SHOT_CONTAMINATED
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        few_shot_examples=examples,
        review=review
    )
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text
    label = "POSITIVE" if "POSITIVE" in text.upper() else "NEGATIVE"
    return {"label": label, "reasoning": text}


def audit_entity_disjoint(few_shot_text: str, val_reviews: list[str]) -> list[str]:
    """Detect if named entities from few-shot examples appear in validation set."""
    # Simplified entity detection — use spaCy in production
    known_entities = {"iphone", "airpods", "macbook", "apple"}
    contaminated = []
    for review in val_reviews:
        found = [e for e in known_entities if e in review.lower()]
        if found:
            contaminated.append(f"Review '{review[:50]}...' contains entities: {found}")
    return contaminated


def benchmark_accuracy(reviews_with_labels: list[dict], use_clean: bool) -> dict:
    """
    Run classification and compute accuracy stratified by
    whether review mentions Apple products (the few-shot entities).
    """
    apple_entities = {"iphone", "airpods", "macbook", "apple", "ipad"}
    results = defaultdict(lambda: {"correct": 0, "total": 0})

    for item in reviews_with_labels:
        review = item["review"]
        true_label = item["label"]
        has_entity_overlap = any(e in review.lower() for e in apple_entities)
        group = "entity_overlap" if has_entity_overlap else "no_overlap"

        pred = classify_review(review, use_clean_examples=use_clean)
        if pred["label"] == true_label:
            results[group]["correct"] += 1
        results[group]["total"] += 1

    return {
        group: {
            "accuracy": data["correct"] / data["total"] if data["total"] else 0,
            "n": data["total"]
        }
        for group, data in results.items()
    }


# Example test cases
test_reviews = [
    {"review": "iPhone 15 Pro has the best camera I've seen. Absolutely love it.", "label": "POSITIVE"},
    {"review": "My AirPods Max broke after one month. Terrible for the price.", "label": "NEGATIVE"},
    {"review": "This Samsung Galaxy S24 takes stunning photos in low light.", "label": "POSITIVE"},
    {"review": "Sony headphones crackle at high volume. Very disappointing.", "label": "NEGATIVE"},
    {"review": "Generic USB-C cable charges fast and feels durable.", "label": "POSITIVE"},
    {"review": "This stand wobbles constantly. Returned immediately.", "label": "NEGATIVE"},
]

if __name__ == "__main__":
    # Check for contamination in test set
    contamination_issues = audit_entity_disjoint(FEW_SHOT_CONTAMINATED, [r["review"] for r in test_reviews])
    if contamination_issues:
        print("CONTAMINATION DETECTED:")
        for issue in contamination_issues:
            print(f"  {issue}")

    # Classify one example with both approaches
    test_review = "My Samsung Galaxy's battery barely lasts half a day. Frustrating."
    print("\nContaminated examples:")
    result_bad = classify_review(test_review, use_clean_examples=False)
    print(f"  Label: {result_bad['label']}")
    print(f"  Reasoning: {result_bad['reasoning'][:200]}")

    print("\nClean examples:")
    result_good = classify_review(test_review, use_clean_examples=True)
    print(f"  Label: {result_good['label']}")
    print(f"  Reasoning: {result_good['reasoning'][:200]}")
```

**The fix, in one sentence:** Replace brand-specific entities in few-shot examples with generic category labels, and add chain-of-thought to teach reasoning process rather than surface pattern recognition.

</details>

---

## Interview Version

**Opening (20 seconds):** "This is a distribution shift problem caused by few-shot anchoring. The accuracy gap between 95% and 67% is a diagnostic signal — it tells you the model learned something correlated with Apple products, not just sentiment."

**Draw the mechanism:**
```
Few-shot examples → Model learns:
  [INTENDED]   "incredible", "stopped working", "terrible" → sentiment words
  [UNINTENDED] "iPhone", "AirPods", "MacBook" → "this is what a review looks like"

Samsung review:
  Matches sentiment pattern: YES
  Matches surface entity pattern: NO
  → Model is less confident → accuracy drops
```

**The two fixes:**
1. Remove named entities from examples (brand-agnostic)
2. Add chain-of-thought to explicitly teach the reasoning path

**Key insight:** "Validation accuracy on your training distribution will look fine. You need an entity-disjoint validation set — one that shares zero entities with your few-shot examples — to catch this before deployment."

---

## Follow-up Questions

1. You replace brand names with generic labels and accuracy improves. Then you add CoT reasoning. How would you measure whether the CoT actually helped, independent of the brand-name change?
2. Your classifier needs to handle mixed-sentiment reviews ("Great camera, terrible battery life"). How do you adapt your few-shot examples and output schema to handle this?
3. At 10,000 reviews/day, you want to detect distribution shift early. What metric would you monitor, and at what threshold would you trigger a few-shot example refresh?
