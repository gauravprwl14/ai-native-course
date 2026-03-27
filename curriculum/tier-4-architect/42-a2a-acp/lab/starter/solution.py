"""Lab 42: A2A & ACP — Agent Communication Protocols (simplified in-process simulation)"""
from dataclasses import dataclass, field


@dataclass
class AgentCard:
    name: str
    description: str
    capabilities: list[str]  # e.g. ["research", "web-search"]
    endpoint: str = "local"  # simplified: "local" means in-process


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
        # TODO: Store card in self._agents keyed by card.name
        # TODO: Store handler in self._handlers keyed by card.name
        pass

    def discover(self, capability: str) -> list[AgentCard]:
        # TODO: Return list of AgentCards where capability is in card.capabilities
        # Return an empty list if no agents match
        pass

    def get_handler(self, agent_name: str):
        # TODO: Return handler for agent_name, raise KeyError if not found
        pass


def delegate_task(task: str, required_capability: str, registry: AgentRegistry) -> TaskResult:
    """Find the best agent for the task and delegate to it."""
    # TODO: Discover agents with required_capability
    # TODO: If no agents found, return TaskResult(agent_name="none", task=task,
    #         result="No agent found", success=False)
    # TODO: Pick first available agent (candidates[0])
    # TODO: Call handler(task) to get result string
    # TODO: Return TaskResult with agent name, task, result, success=True
    pass


def compose_multi_agent(tasks: list[tuple[str, str]], registry: AgentRegistry) -> list[TaskResult]:
    """Delegate multiple tasks to appropriate agents in sequence."""
    # TODO: For each (task, capability) tuple, call delegate_task
    # TODO: Return list of all TaskResults
    pass
