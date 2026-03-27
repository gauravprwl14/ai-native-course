"""Lab 27: Router → Specialist Agents"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from typing import Callable
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"

# Default intent descriptions used in demos and tests
DEFAULT_INTENTS = {
    "code": "Questions about programming, debugging, code review, or software architecture",
    "database": "Questions about SQL, query optimisation, schema design, or database performance",
    "legal": "Questions about contracts, compliance, regulations, or legal interpretation",
    "general": "Any question that does not fit the above categories",
}


def classify_intent(message: str, intents: dict[str, str]) -> str:
    """
    Classify the user message into one of the provided intent labels.
    Returns the label string (e.g. 'code', 'database').
    If the LLM returns a label not in intents, return 'general'.

    # TODO:
    # 1. client = get_anthropic_client()
    # 2. Build a prompt listing each intent label and description
    # 3. Ask the LLM to respond with ONLY the label — no explanation
    # 4. Parse the response: label = response.content[0].text.strip().lower()
    # 5. Return label if label in intents else "general"
    """
    raise NotImplementedError("Implement classify_intent")


def route_and_execute(
    message: str,
    agents: dict[str, Callable],
    conversation_history: list[dict] = None,
) -> str:
    """
    Classify the message intent, select the matching agent callable, and execute it.
    Falls back to the 'general' agent if no specialist matches.

    agents is a dict mapping intent label -> callable(message, context) -> str
    conversation_history is an optional list of prior {"role": ..., "content": ...} dicts.

    # TODO:
    # 1. Build intents dict from agents: {label: label for label in agents}
    #    (or use DEFAULT_INTENTS if agents keys match)
    # 2. intent = classify_intent(message, intents)
    # 3. handler = agents.get(intent) or agents.get("general")
    # 4. If no handler found, return "No agent available for this request."
    # 5. Call handler(message, conversation_history or []) and return the result
    """
    raise NotImplementedError("Implement route_and_execute")


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
        """
        # TODO:
        # self.specialists = specialists
        # self.intents = intents or {label: label for label in specialists}
        # self.fallback = fallback or self._default_fallback
        # self.history: list[dict] = []
        """
        raise NotImplementedError("Implement __init__")

    def chat(self, message: str) -> str:
        """
        Classify the message, dispatch to the right specialist, record history.

        # TODO:
        # 1. intent = classify_intent(message, self.intents)
        # 2. handler = self.specialists.get(intent) or self.fallback
        # 3. response = handler(message, self.history)
        # 4. Append user and assistant turns to self.history
        # 5. Return response
        """
        raise NotImplementedError("Implement chat")

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
    # Demo: build specialist agents backed by different system prompts
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
