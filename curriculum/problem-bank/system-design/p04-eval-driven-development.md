# Eval-Driven Development: Safe System Prompt Deployment

**Category:** system-design
**Difficulty:** Hard
**Key Concepts:** LLM evals, A/B testing, regression testing, eval-driven development, shadow deployment
**Time:** 35–45 min

---

## Problem Statement

Your team runs a customer service bot for an e-commerce platform. It currently uses a 400-word system prompt that has been refined over 6 months. Current performance: **80% positive user ratings** (thumbs up), measured over 50,000 weekly interactions.

A product manager has drafted a new system prompt that:
- Adds a friendlier, more conversational tone
- Includes explicit instructions for handling returns and refund edge cases
- Removes some overly formal language the team felt was robotic

The team consensus: "The new prompt is better." They want to deploy it.

**The problem:** "Better according to the team" is not data. System prompt changes can cause regressions in unexpected areas — a prompt that improves tone might inadvertently reduce accuracy on order status queries. One edge case regression could cost the company $X in wrongly-issued refunds.

**The 80% rating took 6 months to achieve. It could be destroyed in a day.**

Design the evaluation and deployment process that allows you to deploy confidently, detect regressions before they reach users at scale, and roll back automatically if something goes wrong.

---

## What Makes This Hard

The naive instinct — "just do a 10% A/B test and watch the ratings" — has two fatal flaws that are not obvious:

**Flaw 1: Statistical significance takes weeks.** At 50,000 interactions/week, a 10% A/B test gives you 5,000 interactions per week in the new prompt group. To detect a 3-point drop in ratings (80% → 77%) with 95% confidence, you need roughly 3,000–4,000 samples per variant — about a week of data. During that week, users in the new prompt group are getting potentially degraded service. You've already paid the cost before you know there's a problem.

**Flaw 2: User ratings are a lagging indicator.** A user who gets a wrong refund policy answer might not give a thumbs-down immediately — they might call support two days later when the wrong policy was applied. The rating doesn't capture downstream damage.

The deeper problem: you're trying to use production user behavior as your primary test signal, which means real users pay for your experiments.

The expert insight: **build the eval set before deploying, run it offline, and use production as validation — not as the experiment.**

---

## Naive Approach

**Deploy to 10% of users, monitor ratings for a week.**

```python
# Gradual rollout via feature flag
def get_system_prompt(user_id: str) -> str:
    if hash(user_id) % 100 < 10:  # 10% bucket
        return NEW_SYSTEM_PROMPT
    return OLD_SYSTEM_PROMPT
```

Wait one week. If ratings don't drop, roll out to 100%.

**Why it fails:**

1. **Users in the 10% bucket are the experiment.** They received potentially worse service while you collected data. This is ethically and commercially questionable.

2. **Statistical power is insufficient for early detection.** At 5,000 interactions/week in the test group, you need the full week to detect a 3-point drop. A catastrophic regression (80% → 50%) would be detectable in hours, but subtle regressions — the dangerous kind — take weeks.

3. **User ratings don't capture all failure modes.** A bot that confidently gives wrong refund policy answers will get thumbs-up from users who don't know the answer was wrong. The downstream support ticket or chargeback is the real signal, but it's 48–72 hours delayed.

4. **No regression test for edge cases.** The new prompt might handle common cases identically but fail on a specific edge case (e.g., "I want to return a final sale item"). You'll never see this in aggregate ratings unless that exact scenario appears in your 5,000 test interactions — which it may not.

5. **Manual rollback only.** By the time you detect the problem, it's already happened. You need automated rollback, not a human checking dashboards.

---

## Expert Approach

### The Four-Stage Process

#### Stage 1: Build the Eval Set Before Touching the Prompt

This is the most critical step and the one most teams skip. Before the new prompt exists, build an eval set from production logs.

```python
import random
from typing import List
from dataclasses import dataclass

@dataclass
class EvalCase:
    conversation_id: str
    user_message: str
    expected_behavior: str  # What a good response should do
    category: str           # "refund", "order_status", "return_policy", "complaint"
    is_edge_case: bool

def build_eval_set_from_logs(production_logs, n_samples: int = 200) -> List[EvalCase]:
    """
    Build eval set before prompt changes.
    Oversample edge cases — they're where regressions happen.
    """
    # Stratified sampling: ensure coverage across query categories
    categories = ["refund", "order_status", "return_policy", "complaint", "shipping", "edge_case"]
    samples_per_category = n_samples // len(categories)

    eval_cases = []

    for category in categories:
        category_logs = [log for log in production_logs if log.category == category]

        # Get representative cases (high-rated responses — these are ground truth)
        high_quality = [log for log in category_logs if log.user_rating == "positive"]
        eval_cases.extend(random.sample(high_quality, min(samples_per_category, len(high_quality))))

        # Oversample edge cases — these are where new prompts break
        edge_cases = [log for log in category_logs if log.is_edge_case]
        eval_cases.extend(edge_cases[:samples_per_category // 2])

    return eval_cases
```

Each eval case needs a **ground truth label** — what a good response should do. This does not mean the exact text; it means the behavioral expectation:

```python
# Examples of behavioral expectations (not exact response matching)
eval_cases = [
    EvalCase(
        user_message="I bought this 6 months ago and it broke. Can I return it?",
        expected_behavior="Acknowledge the situation, check return policy (30-day window), "
                         "offer alternative resolution (warranty claim, store credit), "
                         "do NOT promise a full refund if outside return window",
        category="return_policy",
        is_edge_case=True,
    ),
    EvalCase(
        user_message="Where is my order #12345?",
        expected_behavior="Provide order status from the order lookup tool. "
                         "If delayed, acknowledge and offer tracking link. "
                         "Do not invent a delivery date.",
        category="order_status",
        is_edge_case=False,
    ),
]
```

#### Stage 2: Offline Evaluation with LLM-as-Judge

Run both prompts against the eval set offline. This takes minutes and costs cents — not days and user goodwill.

```python
async def evaluate_prompt(
    system_prompt: str,
    eval_cases: List[EvalCase],
    judge_model: str = "claude-opus-4-5",  # Use the smartest available model as judge
) -> dict:
    """Run eval set against a prompt and score with LLM-as-judge."""
    results = []

    for case in eval_cases:
        # Generate response with the prompt being evaluated
        response = await generate_response(
            system_prompt=system_prompt,
            user_message=case.user_message,
        )

        # Judge the response against expected behavior
        judgment = await judge_response(
            judge_model=judge_model,
            user_message=case.user_message,
            response=response,
            expected_behavior=case.expected_behavior,
        )

        results.append({
            "case_id": case.conversation_id,
            "category": case.category,
            "is_edge_case": case.is_edge_case,
            "score": judgment.score,  # 1–5
            "pass": judgment.score >= 3,
            "issues": judgment.issues,
        })

    return {
        "overall_pass_rate": sum(r["pass"] for r in results) / len(results),
        "by_category": group_by(results, "category"),
        "edge_case_pass_rate": pass_rate([r for r in results if r["is_edge_case"]]),
        "regressions": [r for r in results if r["score"] < 3],
    }

JUDGE_PROMPT = """You are evaluating a customer service bot response.

User message: {user_message}
Bot response: {response}
Expected behavior: {expected_behavior}

Score the response 1–5 where:
5 = Fully meets expected behavior
4 = Mostly correct, minor issues
3 = Acceptable but missing something
2 = Notable problems
1 = Wrong, misleading, or violates policy

Return JSON: {{"score": X, "issues": ["..."], "reasoning": "..."}}"""

async def judge_response(judge_model, user_message, response, expected_behavior) -> dict:
    result = await anthropic_client.messages.create(
        model=judge_model,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(
                user_message=user_message,
                response=response,
                expected_behavior=expected_behavior,
            )
        }]
    )
    return parse_json(result.content[0].text)
```

#### Stage 3: Define Guardrails Before Comparing Results

Before you run the comparison, write down the conditions under which you will block the deploy. Do this before seeing the numbers — otherwise there is a temptation to rationalize.

```python
@dataclass
class DeploymentGuardrails:
    # Block deploy if new prompt is worse by these margins
    max_overall_regression: float = 0.05      # New prompt can be at most 5% worse overall
    max_category_regression: float = 0.08     # At most 8% worse in any category
    max_edge_case_regression: float = 0.10    # At most 10% worse on edge cases
    min_improvement_to_justify_risk: float = 0.03  # New prompt should be 3%+ better somewhere

def evaluate_deployment_decision(
    old_results: dict,
    new_results: dict,
    guardrails: DeploymentGuardrails,
) -> dict:
    decision = {"deploy": True, "reasons": [], "warnings": []}

    # Check overall regression
    overall_delta = new_results["overall_pass_rate"] - old_results["overall_pass_rate"]
    if overall_delta < -guardrails.max_overall_regression:
        decision["deploy"] = False
        decision["reasons"].append(
            f"BLOCKED: Overall pass rate dropped {abs(overall_delta):.1%} "
            f"(threshold: {guardrails.max_overall_regression:.1%})"
        )

    # Check per-category regressions
    for category, new_cat_results in new_results["by_category"].items():
        old_cat_rate = old_results["by_category"][category]["pass_rate"]
        new_cat_rate = new_cat_results["pass_rate"]
        delta = new_cat_rate - old_cat_rate

        if delta < -guardrails.max_category_regression:
            decision["deploy"] = False
            decision["reasons"].append(
                f"BLOCKED: '{category}' category dropped {abs(delta):.1%} "
                f"(threshold: {guardrails.max_category_regression:.1%})"
            )
        elif delta < 0:
            decision["warnings"].append(
                f"WARNING: '{category}' category down {abs(delta):.1%} — monitor closely"
            )

    # Check edge case regression
    edge_delta = new_results["edge_case_pass_rate"] - old_results["edge_case_pass_rate"]
    if edge_delta < -guardrails.max_edge_case_regression:
        decision["deploy"] = False
        decision["reasons"].append(
            f"BLOCKED: Edge case pass rate dropped {abs(edge_delta):.1%}"
        )

    return decision
```

#### Stage 4: Shadow Deployment + Staged Rollout with Auto-Rollback

After offline evals pass, deploy in shadow mode before showing results to users.

**Shadow mode:** Run both prompts on every request. Only show the old response to users. Compare quality offline.

```python
async def shadow_run_comparison(user_message: str, user_id: str) -> dict:
    """Run both prompts, show old result to user, log both for analysis."""

    # Run both in parallel — no latency cost to the user
    old_response, new_response = await asyncio.gather(
        generate_response(OLD_PROMPT, user_message),
        generate_response(NEW_PROMPT, user_message),
    )

    # Show user the OLD response (safe, proven)
    user_sees = old_response

    # Log both for offline analysis
    log_shadow_comparison(user_id, user_message, old_response, new_response)

    return user_sees

# After 24 hours of shadow mode (5,000+ comparisons):
# Run LLM-as-judge on all shadow pairs
# Confirm new prompt is better or equal on every category
# Only then proceed to staged rollout
```

**Staged rollout with automated rollback:**

```python
ROLLOUT_STAGES = [1, 5, 20, 100]  # Percentage of traffic

class PromptRollout:
    def __init__(self, old_prompt, new_prompt, guardrails):
        self.old_prompt = old_prompt
        self.new_prompt = new_prompt
        self.guardrails = guardrails
        self.current_stage = 0
        self.live_ratings = {"old": [], "new": []}

    def get_prompt_for_user(self, user_id: str) -> str:
        rollout_pct = ROLLOUT_STAGES[self.current_stage]
        if hash(user_id) % 100 < rollout_pct:
            return self.new_prompt
        return self.old_prompt

    def record_rating(self, user_id: str, rating: bool):
        rollout_pct = ROLLOUT_STAGES[self.current_stage]
        group = "new" if hash(user_id) % 100 < rollout_pct else "old"
        self.live_ratings[group].append(rating)

        # Check for rollback condition after minimum sample size
        if len(self.live_ratings["new"]) >= 200:
            self.check_rollback()

    def check_rollback(self):
        new_rate = sum(self.live_ratings["new"]) / len(self.live_ratings["new"])
        old_rate = sum(self.live_ratings["old"]) / len(self.live_ratings["old"])

        if old_rate - new_rate > 0.03:  # New prompt is 3+ points worse in live traffic
            self.rollback()
            alert_team(f"AUTO-ROLLBACK: New prompt is {old_rate - new_rate:.1%} worse in live traffic")

    def advance_stage(self):
        if self.current_stage < len(ROLLOUT_STAGES) - 1:
            self.current_stage += 1
            self.live_ratings = {"old": [], "new": []}  # Reset for new stage

    def rollback(self):
        self.current_stage = 0
        # All users now get old prompt
```

### The Full Deployment Checklist

```
Pre-deployment (offline):
  ✅ Built eval set from 200 production logs (stratified by category, edge cases oversampled)
  ✅ Labeled each eval case with behavioral expectations (not exact text)
  ✅ Ran both prompts against eval set with LLM-as-judge
  ✅ Guardrails defined BEFORE comparing results
  ✅ New prompt passes all guardrails (or team accepts documented regression)

Shadow deployment (24–48 hours):
  ✅ Both prompts run on 100% of traffic
  ✅ Old prompt responses shown to users
  ✅ Offline comparison of shadow pairs confirms new prompt behavior
  ✅ No new failure categories identified in shadow data

Staged rollout:
  ✅ 1% rollout → 24 hours → ratings check → advance
  ✅ 5% rollout → 24 hours → ratings check → advance
  ✅ 20% rollout → 48 hours → ratings check → advance
  ✅ 100% rollout
  ✅ Automated rollback if live rating delta > 3 points
  ✅ Rollback capability tested BEFORE starting rollout
```

---

## Solution

<details>
<summary>Show Solution</summary>

### Cost of This Process

| Step | Time | LLM Cost | Engineering Time |
|---|---|---|---|
| Build eval set (200 cases, label with GPT-4) | 2 hours | ~$5 | 4 hours |
| Run offline eval (both prompts × 200 cases) | 20 minutes | ~$2 | 0 hours (automated) |
| Review eval results | — | — | 1 hour |
| Shadow deployment (24 hours) | 24 hours | ~$0 (users don't pay) | 2 hours setup |
| Staged rollout monitoring | 3–5 days | — | 1 hour/day |

**Total:** ~1 week, ~$10 in LLM costs, ~15 hours of engineering time.

**Cost of NOT doing this:** One regression that issues wrong refunds to 1,000 users at $25 average = $25,000. Plus support overhead, NPS impact, and 6 months of trust rebuilding.

### What Makes a Good Eval Case

Good eval cases are:
- **Specific:** "I want to return a final sale item purchased 45 days ago" not "return question"
- **Behavioral:** Expected behavior is what the bot should DO, not what it should SAY
- **Edge-case rich:** Common cases rarely reveal regressions. The 15% of interactions that are unusual cause 80% of regressions.
- **Category-balanced:** Cover every user intent, not just the most common ones
- **Regularly updated:** Add new cases from any production incident or user complaint

### Eval Set Maintenance

```python
def add_incident_to_eval_set(incident: dict, eval_set: List[EvalCase]):
    """After any production incident, add the triggering case to the eval set."""
    new_case = EvalCase(
        conversation_id=incident["conversation_id"],
        user_message=incident["user_message"],
        expected_behavior=incident["correct_behavior"],  # Determined in postmortem
        category=incident["category"],
        is_edge_case=True,  # It was an incident — it's an edge case by definition
    )
    eval_set.append(new_case)
    # This ensures the same failure can never regress silently again
```

</details>

---

## Interview Version

"Your team wants to update the system prompt for a bot with 80% positive ratings. How do you deploy safely?"

**Start with the diagnosis:**
"The problem with 'deploy to 10% and watch ratings' is that it uses real users as your experiment. Statistical significance takes a week, regressions cost real money, and ratings are a lagging indicator of actual failures."

**Present the four stages:**
```
1. Build eval set (before touching the prompt)
   → 200 representative + edge cases from production logs

2. Run offline eval (LLM-as-judge on both prompts)
   → Takes 20 minutes, costs $2, detects regressions before any user sees them

3. Shadow deployment
   → Both prompts run on 100% of traffic, users see only old prompt
   → 24-48 hours of offline comparison

4. Staged rollout with auto-rollback
   → 1% → 5% → 20% → 100%
   → Automated rollback if live rating drops > 3 points
```

**Emphasize the order:**
"Guardrails are defined before you see the comparison results. If you look at the data first, there's always a temptation to rationalize 'the edge case regression is acceptable.' Define the bar in advance."

**Close with cost framing:**
"This process costs $10 and two weeks. A single regression event — 1,000 users getting wrong refund policy — costs $25,000 in refunds and 6 months of trust rebuilding."

---

## Follow-up Questions

1. Your LLM-as-judge uses Claude Opus to evaluate responses. You discover that Opus systematically prefers the tone of the new prompt — responses that are "friendlier" score higher even when the factual accuracy is identical. How do you detect and correct for judge bias in your eval framework?
2. After deploying the new prompt at 100%, you receive a complaint 10 days later: a user received wrong information about a return deadline that was explicitly covered in the old prompt but not the new one. The eval set missed this case. How do you build a process that catches this class of "known good behavior that disappeared" regression?
3. Your team wants to move faster — instead of evaluating prompt changes against 200 cases, they propose reducing to 20 "golden cases" that represent the most critical scenarios. What are the trade-offs of a smaller eval set, and how small is too small before the eval process stops providing meaningful signal?
