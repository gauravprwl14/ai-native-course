"""Lab 11: System Prompts — Customer Service Bot (SOLUTION)

Reference implementation — fully working.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def create_customer_service_bot(company_name: str, product_type: str) -> dict:
    """
    Create a bot configuration with a system prompt.
    Returns: {"system_prompt": str, "company": str, "product": str}
    """
    system_prompt = f"""You are a customer service representative for {company_name}.

{company_name} provides {product_type} to its customers. Your role is to help customers \
with questions and issues related to {company_name}'s {product_type} offerings.

When helping customers:
- Answer questions about {company_name}'s {product_type} products and services
- Be helpful, concise, and professional at all times
- If you cannot resolve an issue, let the customer know you will escalate to a specialist
- Always confirm you have understood the customer's issue before providing a solution

If a customer asks about topics unrelated to {company_name} or {product_type}, \
politely decline and redirect: "I can only help with questions about {company_name}'s \
{product_type}. Is there anything I can help you with on that topic?"

Respond in plain text only. No markdown, no bullet points, no headers. \
Maximum 3 sentences per response."""

    return {
        "system_prompt": system_prompt,
        "company": company_name,
        "product": product_type,
    }


def chat(bot_config: dict, user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Send a message to the configured bot.
    Returns (response_text, updated_history).
    """
    client = get_anthropic_client()

    history = history + [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        temperature=0.3,
        system=bot_config["system_prompt"],
        messages=history,
    )

    reply = response.content[0].text
    history = history + [{"role": "assistant", "content": reply}]

    return reply, history


def is_on_topic(user_message: str, allowed_topics: list[str]) -> bool:
    """
    Use the LLM to check if a message is on-topic.
    Returns True if on-topic, False otherwise.
    """
    client = get_anthropic_client()
    topics_list = ", ".join(allowed_topics)

    classification_prompt = (
        f"Allowed topics: {topics_list}\n\n"
        f"Message: {user_message}\n\n"
        f"Is this message about one of the allowed topics? Reply with only 'yes' or 'no'."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": classification_prompt}],
    )

    answer = response.content[0].text.strip().lower()
    return "yes" in answer


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== create_customer_service_bot ===")
    bot = create_customer_service_bot("Acme Corp", "cloud storage")
    print(f"  company: {bot['company']}")
    print(f"  product: {bot['product']}")
    print(f"  system_prompt (first 100 chars): {bot['system_prompt'][:100]}...")

    print("\n=== chat (turn 1) ===")
    reply, history = chat(bot, "How do I reset my password?", [])
    print(f"  Response: {reply}")
    print(f"  History length: {len(history)} messages")

    print("\n=== chat (turn 2 — off-topic) ===")
    reply, history = chat(bot, "Tell me about cryptocurrency investing", history)
    print(f"  Response: {reply}")
    print(f"  History length: {len(history)} messages")

    print("\n=== is_on_topic ===")
    print(f"  Billing question (should be True): {is_on_topic('How do I upgrade my plan?', ['billing', 'account management'])}")
    print(f"  Weather question (should be False): {is_on_topic('What is the weather today?', ['billing', 'account management'])}")
