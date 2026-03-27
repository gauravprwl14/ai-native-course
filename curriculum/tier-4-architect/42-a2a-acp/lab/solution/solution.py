"""Lab 42: A2A & ACP — Agent Communication Protocols — Reference Solution"""
from dataclasses import dataclass, field


@dataclass
class AgentCard:
    name: str
    description: str
    capabilities: list[str]
    endpoint: str = "local"


@dataclass
class TaskResult:
    agent_name: str
    task: str
    result: str
    success: bool


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, AgentCard] = {}
        self._handlers: dict[str, callable] = {}

    def register(self, card: AgentCard, handler) -> None:
        self._agents[card.name] = card
        self._handlers[card.name] = handler

    def discover(self, capability: str) -> list[AgentCard]:
        return [
            card for card in self._agents.values()
            if capability in card.capabilities
        ]

    def get_handler(self, agent_name: str):
        return self._handlers[agent_name]


def delegate_task(task: str, required_capability: str, registry: AgentRegistry) -> TaskResult:
    """Find the best agent for the task and delegate to it."""
    candidates = registry.discover(required_capability)

    if not candidates:
        return TaskResult(
            agent_name="none",
            task=task,
            result="No agent found",
            success=False,
        )

    chosen = candidates[0]
    handler = registry.get_handler(chosen.name)
    result = handler(task)

    return TaskResult(
        agent_name=chosen.name,
        task=task,
        result=result,
        success=True,
    )


def compose_multi_agent(tasks: list[tuple[str, str]], registry: AgentRegistry) -> list[TaskResult]:
    """Delegate multiple tasks to appropriate agents in sequence."""
    results = []
    for task, capability in tasks:
        results.append(delegate_task(task, capability, registry))
    return results
