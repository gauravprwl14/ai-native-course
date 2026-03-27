"""Lab 24: Multi-Agent Systems — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = get_anthropic_client()

    def run(self, task: str) -> str:
        """Call the Anthropic API and return the text response."""
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=self.system_prompt,
            messages=[{"role": "user", "content": task}]
        )
        return response.content[0].text


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt=(
                "You are a research assistant. When given a topic, "
                "provide key facts and data points in bullet form."
            )
        )


class WriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Writer",
            system_prompt=(
                "You are a professional writer. "
                "Turn research notes into a clear, concise paragraph."
            )
        )


class Orchestrator:
    def __init__(self):
        self.researcher = ResearchAgent()
        self.writer = WriterAgent()

    def run(self, topic: str) -> dict:
        """
        Run the two-agent pipeline: research -> write.
        Returns {"topic": str, "research": str, "article": str}
        """
        research = self.researcher.run(f"Research: {topic}")
        article = self.writer.run(
            f"Write a paragraph based on these notes:\n{research}"
        )
        return {"topic": topic, "research": research, "article": article}


if __name__ == "__main__":
    topic = "The history of the internet"
    print(f"Topic: {topic}\n")

    orch = Orchestrator()
    result = orch.run(topic)

    print("=== Research Notes ===")
    print(result["research"])
    print("\n=== Article ===")
    print(result["article"])
