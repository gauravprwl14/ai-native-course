"""Lab 11: System Prompts — Customer Service Bot"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def create_customer_service_bot(company_name: str, product_type: str) -> dict:
    """
    Create a bot configuration with a system prompt.
    Returns: {"system_prompt": str, "company": str, "product": str}

    # TODO: Create a detailed system prompt that:
    # - Sets persona as customer service rep for company_name
    # - Specifies product_type context
    # - Instructs to be helpful, concise, professional
    # - Instructs to politely decline off-topic questions
    # - Specifies response format (no markdown, plain text, max 3 sentences)
    # Return as dict with "system_prompt", "company", "product" keys
    """
    raise NotImplementedError("Implement create_customer_service_bot")


def chat(bot_config: dict, user_message: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Send a message to the configured bot.
    Returns (response_text, updated_history).

    # TODO:
    # 1. Get client via get_anthropic_client(), add user message to history
    # 2. Call API with system=bot_config["system_prompt"], messages=history,
    #    temperature=0.3, max_tokens=512
    # 3. Append assistant response to history
    # 4. Return (response_text, updated_history)
    """
    raise NotImplementedError("Implement chat")


def is_on_topic(user_message: str, allowed_topics: list[str]) -> bool:
    """
    Use the LLM to check if a message is on-topic.
    Returns True if on-topic, False otherwise.

    # TODO:
    # Build a classification prompt that lists allowed_topics
    # Ask: "Is this message about one of these topics: [topics]?
    #       Reply with only 'yes' or 'no'."
    # Call API with temperature=0 for deterministic classification
    # Return True if response contains 'yes' (case-insensitive), False otherwise
    """
    raise NotImplementedError("Implement is_on_topic")


# ---------------------------------------------------------------------------
# Manual smoke test — run this to see your functions in action
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
