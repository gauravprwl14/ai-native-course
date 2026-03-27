"""Tests for Lab 42 — A2A Agent Delegation System"""

import os
import sys
import unittest
from pathlib import Path

# LAB_TARGET=solution runs tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


def _make_registry_with_agents():
    """Helper: create a registry with two registered mock agents."""
    from solution import AgentCard, AgentRegistry

    registry = AgentRegistry()

    registry.register(
        AgentCard(
            name="ResearchAgent",
            description="Searches for and summarises factual information",
            capabilities=["research", "fact-finding"],
        ),
        handler=lambda task: f"[Research] Key facts about: {task}",
    )

    registry.register(
        AgentCard(
            name="SummaryAgent",
            description="Creates concise summaries",
            capabilities=["summarise", "writing"],
        ),
        handler=lambda task: f"[Summary] {task[:30]}...",
    )

    return registry


class TestAgentCard(unittest.TestCase):
    def test_stores_name(self):
        from solution import AgentCard
        card = AgentCard(name="TestAgent", description="A test agent",
                         capabilities=["test"])
        self.assertEqual(card.name, "TestAgent")

    def test_stores_description(self):
        from solution import AgentCard
        card = AgentCard(name="A", description="Does things", capabilities=["things"])
        self.assertEqual(card.description, "Does things")

    def test_stores_capabilities(self):
        from solution import AgentCard
        card = AgentCard(name="A", description="d", capabilities=["research", "writing"])
        self.assertEqual(card.capabilities, ["research", "writing"])

    def test_default_endpoint_is_local(self):
        from solution import AgentCard
        card = AgentCard(name="A", description="d", capabilities=[])
        self.assertEqual(card.endpoint, "local")

    def test_custom_endpoint(self):
        from solution import AgentCard
        card = AgentCard(name="A", description="d", capabilities=[],
                         endpoint="https://agents.example.com")
        self.assertEqual(card.endpoint, "https://agents.example.com")


class TestTaskResult(unittest.TestCase):
    def test_stores_agent_name(self):
        from solution import TaskResult
        r = TaskResult(agent_name="ResearchAgent", task="do research",
                       result="facts here", success=True)
        self.assertEqual(r.agent_name, "ResearchAgent")

    def test_stores_task(self):
        from solution import TaskResult
        r = TaskResult(agent_name="A", task="my task", result="output", success=True)
        self.assertEqual(r.task, "my task")

    def test_stores_result(self):
        from solution import TaskResult
        r = TaskResult(agent_name="A", task="t", result="my result", success=True)
        self.assertEqual(r.result, "my result")

    def test_stores_success_true(self):
        from solution import TaskResult
        r = TaskResult(agent_name="A", task="t", result="r", success=True)
        self.assertTrue(r.success)

    def test_stores_success_false(self):
        from solution import TaskResult
        r = TaskResult(agent_name="none", task="t", result="No agent found", success=False)
        self.assertFalse(r.success)


class TestAgentRegistryRegister(unittest.TestCase):
    def test_register_stores_card(self):
        from solution import AgentCard, AgentRegistry
        registry = AgentRegistry()
        card = AgentCard(name="MyAgent", description="d", capabilities=["cap"])
        registry.register(card, handler=lambda t: "result")
        agents = registry.discover("cap")
        self.assertTrue(any(a.name == "MyAgent" for a in agents))

    def test_register_stores_handler(self):
        from solution import AgentCard, AgentRegistry
        registry = AgentRegistry()
        card = AgentCard(name="MyAgent", description="d", capabilities=["cap"])
        handler = lambda t: "handled"
        registry.register(card, handler=handler)
        retrieved = registry.get_handler("MyAgent")
        self.assertIs(retrieved, handler)

    def test_register_multiple_agents(self):
        from solution import AgentCard, AgentRegistry
        registry = AgentRegistry()
        registry.register(
            AgentCard("A1", "d", ["cap1"]), handler=lambda t: "a1"
        )
        registry.register(
            AgentCard("A2", "d", ["cap2"]), handler=lambda t: "a2"
        )
        self.assertEqual(len(registry.discover("cap1")), 1)
        self.assertEqual(len(registry.discover("cap2")), 1)


class TestAgentRegistryDiscover(unittest.TestCase):
    def test_discover_returns_matching_agents(self):
        registry = _make_registry_with_agents()
        agents = registry.discover("research")
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0].name, "ResearchAgent")

    def test_discover_returns_empty_for_unknown_capability(self):
        registry = _make_registry_with_agents()
        agents = registry.discover("translation")
        self.assertEqual(agents, [])

    def test_discover_returns_multiple_matches(self):
        from solution import AgentCard, AgentRegistry
        registry = AgentRegistry()
        registry.register(AgentCard("A", "d", ["cap"]), handler=lambda t: "a")
        registry.register(AgentCard("B", "d", ["cap"]), handler=lambda t: "b")
        agents = registry.discover("cap")
        self.assertEqual(len(agents), 2)

    def test_discover_returns_list(self):
        registry = _make_registry_with_agents()
        result = registry.discover("research")
        self.assertIsInstance(result, list)

    def test_discover_capability_not_in_list(self):
        from solution import AgentCard, AgentRegistry
        registry = AgentRegistry()
        registry.register(
            AgentCard("A", "d", ["writing"]), handler=lambda t: "a"
        )
        # "write" is not the same as "writing"
        agents = registry.discover("write")
        self.assertEqual(agents, [])


class TestAgentRegistryGetHandler(unittest.TestCase):
    def test_get_handler_returns_callable(self):
        registry = _make_registry_with_agents()
        handler = registry.get_handler("ResearchAgent")
        self.assertTrue(callable(handler))

    def test_get_handler_unknown_raises_key_error(self):
        registry = _make_registry_with_agents()
        with self.assertRaises(KeyError):
            registry.get_handler("NonExistentAgent")

    def test_get_handler_result_matches_registration(self):
        from solution import AgentCard, AgentRegistry
        registry = AgentRegistry()
        registry.register(
            AgentCard("MyAgent", "d", ["cap"]),
            handler=lambda t: f"custom: {t}",
        )
        handler = registry.get_handler("MyAgent")
        self.assertEqual(handler("test input"), "custom: test input")


class TestDelegateTask(unittest.TestCase):
    def test_returns_task_result(self):
        from solution import delegate_task, TaskResult
        registry = _make_registry_with_agents()
        result = delegate_task("climate change facts", "research", registry)
        self.assertIsInstance(result, TaskResult)

    def test_success_true_when_agent_found(self):
        from solution import delegate_task
        registry = _make_registry_with_agents()
        result = delegate_task("solar energy", "research", registry)
        self.assertTrue(result.success)

    def test_agent_name_in_result(self):
        from solution import delegate_task
        registry = _make_registry_with_agents()
        result = delegate_task("solar energy", "research", registry)
        self.assertEqual(result.agent_name, "ResearchAgent")

    def test_task_preserved_in_result(self):
        from solution import delegate_task
        registry = _make_registry_with_agents()
        task = "what is the capital of France?"
        result = delegate_task(task, "research", registry)
        self.assertEqual(result.task, task)

    def test_result_string_from_handler(self):
        from solution import delegate_task
        registry = _make_registry_with_agents()
        result = delegate_task("solar energy", "research", registry)
        self.assertIsInstance(result.result, str)
        self.assertGreater(len(result.result), 0)

    def test_unknown_capability_returns_failure(self):
        from solution import delegate_task
        registry = _make_registry_with_agents()
        result = delegate_task("translate this", "translation", registry)
        self.assertFalse(result.success)
        self.assertEqual(result.agent_name, "none")

    def test_unknown_capability_result_message(self):
        from solution import delegate_task
        registry = _make_registry_with_agents()
        result = delegate_task("something", "nonexistent", registry)
        self.assertIn("No agent found", result.result)

    def test_summarise_capability_routes_to_summary_agent(self):
        from solution import delegate_task
        registry = _make_registry_with_agents()
        result = delegate_task("long text to summarise", "summarise", registry)
        self.assertTrue(result.success)
        self.assertEqual(result.agent_name, "SummaryAgent")

    def test_handler_output_in_result(self):
        from solution import AgentCard, AgentRegistry, delegate_task
        registry = AgentRegistry()
        registry.register(
            AgentCard("SpecialAgent", "d", ["special"]),
            handler=lambda t: f"SPECIAL_OUTPUT:{t}",
        )
        result = delegate_task("my task", "special", registry)
        self.assertIn("SPECIAL_OUTPUT", result.result)


class TestComposeMultiAgent(unittest.TestCase):
    def test_returns_list(self):
        from solution import compose_multi_agent
        registry = _make_registry_with_agents()
        results = compose_multi_agent(
            [("task1", "research"), ("task2", "summarise")],
            registry,
        )
        self.assertIsInstance(results, list)

    def test_returns_correct_number_of_results(self):
        from solution import compose_multi_agent
        registry = _make_registry_with_agents()
        tasks = [("t1", "research"), ("t2", "summarise"), ("t3", "research")]
        results = compose_multi_agent(tasks, registry)
        self.assertEqual(len(results), 3)

    def test_each_result_is_task_result(self):
        from solution import compose_multi_agent, TaskResult
        registry = _make_registry_with_agents()
        results = compose_multi_agent([("task", "research")], registry)
        for r in results:
            self.assertIsInstance(r, TaskResult)

    def test_empty_tasks_returns_empty_list(self):
        from solution import compose_multi_agent
        registry = _make_registry_with_agents()
        results = compose_multi_agent([], registry)
        self.assertEqual(results, [])

    def test_failed_tasks_included_in_results(self):
        from solution import compose_multi_agent
        registry = _make_registry_with_agents()
        results = compose_multi_agent(
            [("research task", "research"), ("unknown task", "translation")],
            registry,
        )
        self.assertEqual(len(results), 2)
        success_flags = [r.success for r in results]
        self.assertIn(True, success_flags)
        self.assertIn(False, success_flags)

    def test_tasks_delegated_to_correct_agents(self):
        from solution import compose_multi_agent
        registry = _make_registry_with_agents()
        results = compose_multi_agent(
            [("research task", "research"), ("summarise task", "summarise")],
            registry,
        )
        agent_names = [r.agent_name for r in results]
        self.assertIn("ResearchAgent", agent_names)
        self.assertIn("SummaryAgent", agent_names)


if __name__ == "__main__":
    unittest.main()
