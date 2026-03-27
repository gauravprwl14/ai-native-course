"""Lab 27: Router → Specialist Agents — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from typing import Callable
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

DEFAULT_INTENTS = {
    "code": "Questions about programming, debugging, code review, or software architecture",
    "database": "Questions about SQL, query optimisation, schema design, or database performance",
    "legal": "Questions about contracts, compliance, regulations, or legal interpretation",
    "general": "Any question that does not fit the above categories",
}


def classify_intent(message: str, intents: dict[str, str]) -> str:
    """
    Classify the user message into one of the provided intent labels.
    Returns the label string. Falls back to 'general' for unrecognised labels.
    """
    client = get_anthropic_client()
    intent_list = "\n".join(
        f"- {label}: {description}" for label, description in intents.items()
    )
    prompt = (
        f"Classify the following user message into exactly one of these categories:\n"
        f"{intent_list}\n\n"
        f"User message: {message}\n\n"
        "Respond with only the category label. No explanation, no punctuation."
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=32,
        messages=[{"role": "user", "content": prompt}],
    )
    label = response.content[0].text.strip().lower()
    return label if label in intents else "general"


def route_and_execute(
    message: str,
    agents: dict[str, Callable],
    conversation_history: list[dict] = None,
) -> str:
    """
    Classify the message intent, select the matching agent, and execute it.
    Falls back to the 'general' agent if no specialist matches.
    """
    if conversation_history is None:
        conversation_history = []

    intents = {label: label for label in agents}
    intent = classify_intent(message, intents)
    handler = agents.get(intent) or agents.get("general")

    if handler is None:
        return "No agent available for this request."

    return handler(message, conversation_history)


class AgentRouter:
    """
    A router that maintains conversation history and dispatches messages
    to the right specialist agent.
    """

    def __init__(
        self,
        specialists: dict[str, Callable],
        intents: dict[str, str] = None,
        fallback: Callable = None,
    ):
        self.specialists = specialists
        self.intents = intents or {label: label for label in specialists}
        self.fallback = fallback or self._default_fallback
        self.history: list[dict] = []

    def chat(self, message: str) -> str:
        """Classify the message, dispatch to the right specialist, record history."""
        intent = classify_intent(message, self.intents)
        handler = self.specialists.get(intent) or self.fallback
        response = handler(message, self.history)

        self.history.append({"role": "user", "content": message})
        self.history.append({"role": "assistant", "content": response})

        return response

    def _default_fallback(self, message: str, context: list[dict]) -> str:
        """A simple general-purpose fallback using the Anthropic client."""
        client = get_anthropic_client()
        messages = list(context) + [{"role": "user", "content": message}]
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system="You are a helpful general-purpose assistant.",
            messages=messages,
        )
        return response.content[0].text


if __name__ == "__main__":
    def make_specialist(system_prompt: str) -> Callable:
        def specialist(message: str, context: list[dict]) -> str:
            client = get_anthropic_client()
            messages = list(context) + [{"role": "user", "content": message}]
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )
            return response.content[0].text
        return specialist

    specialists = {
        "code": make_specialist("You are an expert software engineer."),
        "database": make_specialist("You are a database and SQL expert."),
        "general": make_specialist("You are a helpful assistant."),
    }

    router = AgentRouter(specialists=specialists, intents=DEFAULT_INTENTS)

    questions = [
        "How do I reverse a linked list in Python?",
        "Why is my SELECT query slow even though I have an index?",
        "What is the capital of Australia?",
    ]

    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {router.chat(q)}")
