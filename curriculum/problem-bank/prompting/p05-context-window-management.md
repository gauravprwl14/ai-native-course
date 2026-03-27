# Context Window Management

**Category:** prompting
**Difficulty:** Hard
**Key Concepts:** attention dilution, context compression, conversation summarization, memory management
**Time:** 30–45 min

---

## Problem Statement

You're building a long-running coding assistant. Users define requirements in the first few turns, then work through implementation across 20+ turns.

After turn 22, users report the assistant behaves as if the early requirements don't exist:

- Turn 1: "We're building a REST API. Use FastAPI. All endpoints must return ISO 8601 timestamps. No UUID fields — use slug-based IDs."
- Turn 22: The assistant suggests a `uuid4()` call and returns a Python `datetime` object instead of an ISO 8601 string.

Your telemetry shows:
- Average conversation length at failure: 45,000 tokens
- Model context window: 200k tokens
- **The model is not hitting the context limit**

Why is it "forgetting" requirements that are still in the window? How do you fix it?

---

## What Makes This Hard

LLMs don't "forget" due to context length — they forget due to **attention dilution**.

The transformer attention mechanism gives each token a weighted attention score over all other tokens. In a 45,000-token conversation, turn 1 (your requirements) competes with 44,000+ other tokens for the model's attention. Empirically, models attend most strongly to:

1. **The most recent tokens** (strong recency bias)
2. **The first tokens in the context** (primacy effect — less strong but real)
3. **Tokens that are semantically relevant to the current query**

A requirement like "use slug-based IDs" mentioned once in turn 1, surrounded by 44,000 tokens of implementation discussion, has effectively diluted to near-zero attention weight by turn 22.

The non-obvious challenge: **truncating old messages makes this worse, not better**. Truncation removes the requirements from the context entirely. You need to reinforce them, not remove them.

---

## Naive Approach

**Strategy: Truncate old messages when conversation gets long.**

```python
MAX_TOKENS = 40000

def truncate_to_fit(messages: list[dict], max_tokens: int) -> list[dict]:
    """Keep the most recent messages that fit in the token budget."""
    total = 0
    result = []
    for message in reversed(messages):
        tokens = count_tokens(message["content"])
        if total + tokens > max_tokens:
            break
        result.insert(0, message)
        total += tokens
    return result

# In the main loop:
trimmed_messages = truncate_to_fit(conversation_history, MAX_TOKENS)
response = client.messages.create(messages=trimmed_messages, ...)
```

**Why this fails:**

1. **Removes the requirements.** Turn 1 is the first thing truncated. The assistant no longer has access to any of the constraints defined at the start.
2. **Doesn't fix the root cause.** Even before truncation, the model was already ignoring early context due to attention dilution. Truncation just makes it official.
3. **No visibility.** The user sees a capable assistant that silently ignores their requirements. The failure mode is invisible until something ships wrong.
4. **Asymmetric damage.** Recent code snippets (low-value context) are preserved. Architectural requirements (high-value context) are dropped.

---

## Expert Approach

Four mechanisms that work together:

**Mechanism 1: Attention primacy — pin requirements at the start AND end of context**

The transformer's attention has a U-shaped pattern: highest at the beginning and end of the context, weakest in the middle. Use this. Place critical requirements in the system prompt AND append a compressed summary at the bottom of every request.

```
System prompt:
  [Project requirements — always here, never moves]
  [Architecture constraints — always here]

Middle of context:
  [Conversation turns 1–20 — diluted, low attention]

Bottom of context (injected each call):
  [Requirements reminder: "Remember: FastAPI, ISO 8601 timestamps, slug IDs"]
```

**Mechanism 2: Maintain a living requirements document in the system prompt**

Don't put raw requirements in the conversation. Extract them into a structured block in the system prompt that you update as requirements evolve.

```python
def build_system_prompt(requirements: dict) -> str:
    reqs = "\n".join(f"- {k}: {v}" for k, v in requirements.items())
    return f"""You are a coding assistant for this project.

## Project Requirements (ALWAYS FOLLOW THESE)
{reqs}

These requirements were established by the user and must be respected in every response.
Before generating code, verify it complies with each requirement above.
"""
```

**Mechanism 3: Periodic middle-context compression**

The "diluted middle" is where old code discussions live. Compress them periodically. After every 10 turns, summarize the last 10 turns into a compact decisions log:

```python
compression_prompt = """Summarize the last 10 turns of this conversation as a compact log.
Focus on: decisions made, code written, problems solved, open questions.
Output format: bullet points. Maximum 200 tokens. Do not include actual code — just describe it."""
```

Replace turns 10–20 with a single system message: `[Summary of turns 10–20: ...]`.
This keeps recent context fresh without ballooning to 100k tokens.

**Mechanism 4: Requirements extraction after each turn**

After each assistant response, run a cheap background call to extract any new requirements or decisions and update the requirements document:

```python
extraction_prompt = """Did the user's message add, change, or clarify any project requirements?
If yes, return JSON: {"change": true, "key": "requirement_name", "value": "..."}
If no, return JSON: {"change": false}"""
```

This converts the requirements from "mentioned once in turn 1" to a living document that grows with the conversation.

---

## Solution

<details>
<summary>Show Solution</summary>

```python
import json
import anthropic
from dataclasses import dataclass, field
from typing import Optional

client = anthropic.Anthropic()

# --- Data structures ---

@dataclass
class Requirements:
    """Living requirements document. Updated as the conversation evolves."""
    items: dict[str, str] = field(default_factory=dict)

    def update(self, key: str, value: str):
        self.items[key] = value

    def to_prompt_block(self) -> str:
        if not self.items:
            return "(No requirements established yet)"
        lines = [f"- {k}: {v}" for k, v in self.items.items()]
        return "\n".join(lines)


@dataclass
class ConversationManager:
    requirements: Requirements = field(default_factory=Requirements)
    messages: list[dict] = field(default_factory=list)
    turn_count: int = 0
    compression_interval: int = 10  # Compress every N turns

    def build_system_prompt(self) -> str:
        return f"""You are a coding assistant. You help users build software.

## Project Requirements — ALWAYS FOLLOW THESE
{self.requirements.to_prompt_block()}

These requirements were established by the user and are non-negotiable.
Before writing any code, verify it complies with every requirement above.
If you are ever unsure whether a requirement applies, ask before generating code."""

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self.turn_count += 1

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def get_messages_with_bottom_reminder(self) -> list[dict]:
        """
        Inject a requirements reminder at the bottom of the message list.
        This exploits the recency bias — recent tokens get high attention weight.
        """
        if not self.requirements.items:
            return self.messages

        reminder = (
            "\n\n[REMINDER — Active project requirements: "
            + "; ".join(f"{k}={v}" for k, v in self.requirements.items.items())
            + ". Verify your response complies before replying.]"
        )

        # Append reminder to the last user message (not as a new message)
        if self.messages and self.messages[-1]["role"] == "user":
            modified = self.messages[:-1] + [{
                "role": "user",
                "content": self.messages[-1]["content"] + reminder
            }]
            return modified
        return self.messages

    def should_compress(self) -> bool:
        """Compress the middle of the conversation every N turns."""
        return self.turn_count > 0 and self.turn_count % self.compression_interval == 0

    def compress_middle(self):
        """
        Replace the oldest half of messages with a compact summary.
        Preserves the most recent messages which have highest attention weight.
        """
        if len(self.messages) < 20:
            return  # Not enough history to compress

        # Keep the last 10 messages fresh
        preserve_recent = 10
        to_compress = self.messages[:-preserve_recent]
        to_keep = self.messages[-preserve_recent:]

        if not to_compress:
            return

        # Summarize the old messages
        compression_input = "\n\n".join(
            f"{m['role'].upper()}: {m['content'][:500]}"  # Truncate very long messages for summary input
            for m in to_compress
        )

        summary_response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "Summarize the following conversation turns as a compact bullet-point log. "
                    "Focus on: decisions made, code written (describe, don't reproduce), "
                    "problems solved, open questions. Max 200 tokens.\n\n"
                    + compression_input
                )
            }]
        )
        summary_text = summary_response.content[0].text

        # Replace compressed messages with a single context-injection message
        compression_marker = {
            "role": "user",
            "content": f"[Context from earlier in this conversation: {summary_text}]"
        }
        self.messages = [compression_marker] + to_keep
        print(f"Compressed {len(to_compress)} messages into summary block.")


def extract_requirements_from_turn(user_message: str, assistant_response: str) -> Optional[dict]:
    """
    Background call: check if this turn introduced or changed any requirements.
    Returns {"key": ..., "value": ...} if a new requirement was found, else None.
    """
    extraction_response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": (
                "Did the user's message below add, change, or clarify a project requirement "
                "(e.g., technology choice, naming convention, output format, constraint)?\n\n"
                f"User message: {user_message}\n\n"
                "If yes, return JSON: {\"change\": true, \"key\": \"requirement_name\", \"value\": \"description\"}\n"
                "If no, return JSON: {\"change\": false}"
            )
        }]
    )
    try:
        result = json.loads(extraction_response.content[0].text)
        if result.get("change"):
            return {"key": result["key"], "value": result["value"]}
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def chat(manager: ConversationManager, user_input: str) -> str:
    """
    Main chat function. Handles requirements extraction, compression, and context management.
    """
    manager.add_user_message(user_input)

    # Compress if needed (happens before the API call to reduce tokens)
    if manager.should_compress():
        manager.compress_middle()

    # Get messages with bottom-of-context requirements reminder
    messages_to_send = manager.get_messages_with_bottom_reminder()

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=manager.build_system_prompt(),
        messages=messages_to_send
    )

    assistant_reply = response.content[0].text
    manager.add_assistant_message(assistant_reply)

    # Background: extract any new requirements from this turn
    new_req = extract_requirements_from_turn(user_input, assistant_reply)
    if new_req:
        manager.requirements.update(new_req["key"], new_req["value"])
        print(f"[Requirements updated] {new_req['key']}: {new_req['value']}")

    return assistant_reply


if __name__ == "__main__":
    manager = ConversationManager()

    # Simulate a long conversation where requirements are set early and tested late
    conversation = [
        "We're building a REST API. Use FastAPI. All timestamps must be ISO 8601 strings. "
        "Never use UUID fields — use slug-based IDs (e.g., 'user-john-smith'). "
        "All responses must include a 'request_id' field.",
        "Great. Start with the user model.",
        "Now add an endpoint to create a user.",
        "Add an endpoint to list all users.",
        "Add filtering by created_at date range.",
        "Now add soft delete support.",
        "Add an audit log model.",
        "Connect the audit log to user creation and deletion.",
        "Add pagination to the list endpoint.",
        "Add rate limiting middleware.",
        # Turn 10+ — requirements should still be honored
        "Now create the order model.",
        "Add an endpoint to create an order.",
        "Show me how to generate IDs for orders.",  # This is the trap — will it use UUID or slugs?
    ]

    for user_input in conversation:
        print(f"\nUser: {user_input[:80]}...")
        reply = chat(manager, user_input)
        print(f"Assistant: {reply[:200]}...")
        print(f"[Active requirements: {manager.requirements.items}]")
        print(f"[Messages in context: {len(manager.messages)}]")
```

</details>

---

## Interview Version

**Opening (20 seconds):** "The model is not forgetting — it's attending less. A 45,000-token conversation with requirements in turn 1 means those requirements compete with 44,000 other tokens for attention weight. The fix is not truncation — truncation removes the requirements entirely. The fix is strategic context reinforcement."

**Draw the attention profile:**
```
Token position in 45k-token context:
  [Turn 1: requirements]  ← moderate attention (primacy)
  [Turns 2–21: discussion] ← LOW attention (buried middle)
  [Turn 22: current query] ← HIGH attention (recency)

Fix:
  [System prompt: living requirements doc] ← always high (outside context window)
  [Turns 2–21: compressed summaries]       ← low, but short
  [Turn 22: current query + reminder]      ← HIGH attention, requirements repeated here
```

**The three-part fix:**
```
1. Pin requirements in system prompt — never in conversation turns
2. Compress old turns into summaries — keep middle thin
3. Append requirements reminder to every user message — exploit recency bias
```

**Close:** "The background requirement-extraction call is the compound interest. Each turn enriches the requirements document. By turn 22, the document is more complete than anything the user said in turn 1."

---

## Follow-up Questions

1. The requirements extraction background call adds cost and latency. At 500 conversations/day with 30 turns each, estimate the monthly cost and latency impact. Is the background call worth running synchronously or should it be fire-and-forget?
2. Your compression call summarizes the last 10 turns every 10 turns. But compression is lossy — some code details will be lost. What categories of information should you never compress (preserve verbatim), and how would you implement selective preservation?
3. A user says "actually, forget the slug-based IDs — let's use UUIDs." Your requirements document now has a contradiction. How do you handle requirement updates, and how do you ensure the old constraint ("no UUID fields") is cleanly replaced rather than coexisting with the new one?
