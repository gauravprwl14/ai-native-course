# Lab 10: Chain-of-Thought Prompting — Problem Statement

## Goal

Implement a math word problem solver that uses chain-of-thought prompting to reason step by step. You will build four functions that together form a complete CoT pipeline.

---

## Functions to Implement

### 1. `solve_with_cot(problem: str) -> str`

Use **zero-shot chain-of-thought** to solve a math word problem.

- Format the `COT_PROMPT` template with the given `problem`
- Call the Claude API at `temperature=0` (deterministic)
- Return the full model response as a string (including the reasoning steps)

**Example:**

```python
response = solve_with_cot("A box has 4 rows of 6 apples. 7 are bruised. How many are good?")
# Returns something like:
# "There are 4 × 6 = 24 apples total.
#  7 are bruised, so 24 − 7 = 17 are good.
#  Therefore, the answer is: 17"
```

---

### 2. `extract_answer(response: str) -> str | None`

Extract the final numerical answer from a CoT response.

- Use `re.search` to find the pattern `r"Therefore, the answer is:\s*(\d+(?:\.\d+)?)"`
- Return `match.group(1)` (the number as a string) if found
- Return `None` if the pattern is not present in the response

**Examples:**

```python
extract_answer("Step 1: 3×4=12. Therefore, the answer is: 12")  # "12"
extract_answer("Therefore, the answer is: 3.14")                 # "3.14"
extract_answer("I don't know the answer.")                       # None
```

---

### 3. `solve_with_self_consistency(problem: str, n: int = 5) -> str | None`

Use **self-consistency** to improve answer reliability.

1. Generate `n` independent responses by calling the API `n` times at `temperature=0.7`
2. Call `extract_answer()` on each response
3. Filter out `None` values
4. Return the most common extracted answer using `Counter` from `collections`
5. Return `None` if no answers were successfully extracted

**Note:** Each of the `n` API calls must be made independently — do not reuse the same response.

---

### 4. `evaluate_math_accuracy(predictions: list[str | None], answers: list[str]) -> float`

Evaluate accuracy of predicted answers against ground truth.

- Compare each prediction to the corresponding correct answer
- `None` predictions count as wrong (no match)
- Return the fraction correct as a float between 0.0 and 1.0

**Examples:**

```python
evaluate_math_accuracy(["42", "17", "5"], ["42", "17", "5"])      # 1.0
evaluate_math_accuracy(["42", None, "99"], ["42", "17", "5"])     # 0.333...
evaluate_math_accuracy(["1", "2", "3"], ["4", "5", "6"])          # 0.0
```

---

## Files

| File | Description |
|------|-------------|
| `starter/solution.py` | Skeleton with TODOs — edit this file |
| `solution/solution.py` | Reference solution |
| `tests/test_solution.py` | Automated tests |

## Running

```bash
# Run your implementation
cd curriculum/tier-2-builder/10-chain-of-thought/lab/starter
python solution.py

# Run tests
cd curriculum/tier-2-builder/10-chain-of-thought/lab
pytest tests/ -v
```
