"""Tests for Lab 25: Agent with Persistent Memory"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_embedding(seed: float, dim: int = 4) -> list[float]:
    """Make a tiny deterministic embedding for testing."""
    return [seed * (i + 1) for i in range(dim)]


def mock_embed_side_effect(text: str) -> list[float]:
    """Return a unique embedding based on a hash of the text."""
    h = abs(hash(text)) % 1000 / 1000.0
    return make_embedding(h + 0.01)


# ---------------------------------------------------------------------------
# MemoryStore.save
# ---------------------------------------------------------------------------

class TestMemoryStoreSave(unittest.TestCase):
    """Tests for MemoryStore.save()"""

    @patch("solution.MemoryStore._embed")
    def test_save_stores_value_and_embedding(self, mock_embed):
        """save() stores value and embedding under the given key."""
        from solution import MemoryStore

        mock_embed.return_value = [0.1, 0.2, 0.3, 0.4]
        store = MemoryStore()
        store.save("name", "Alice")

        self.assertIn("name", store.memories)
        self.assertEqual(store.memories["name"]["value"], "Alice")
        self.assertEqual(store.memories["name"]["embedding"], [0.1, 0.2, 0.3, 0.4])

    @patch("solution.MemoryStore._embed")
    def test_save_calls_embed_with_value(self, mock_embed):
        """save() calls _embed with the value string."""
        from solution import MemoryStore

        mock_embed.return_value = [0.5, 0.5, 0.5, 0.5]
        store = MemoryStore()
        store.save("project", "fraud detection")

        mock_embed.assert_called_with("fraud detection")

    @patch("solution.MemoryStore._embed")
    def test_save_persists_when_storage_path_set(self, mock_embed):
        """save() calls _persist() when storage_path is configured."""
        from solution import MemoryStore

        mock_embed.return_value = [0.1, 0.2, 0.3, 0.4]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        store = MemoryStore(storage_path=path)
        store.save("key", "value")

        # File should now contain our memory
        with open(path) as f:
            data = json.load(f)
        self.assertIn("key", data)
        self.assertEqual(data["key"]["value"], "value")

    @patch("solution.MemoryStore._embed")
    @patch("solution.MemoryStore._persist")
    def test_save_does_not_persist_when_no_storage_path(self, mock_persist, mock_embed):
        """save() does not call _persist() when storage_path is None."""
        from solution import MemoryStore

        mock_embed.return_value = [0.1, 0.2, 0.3, 0.4]
        store = MemoryStore()  # no storage_path
        store.save("key", "value")

        mock_persist.assert_not_called()


# ---------------------------------------------------------------------------
# MemoryStore.get
# ---------------------------------------------------------------------------

class TestMemoryStoreGet(unittest.TestCase):
    """Tests for MemoryStore.get()"""

    def test_get_returns_value_for_known_key(self):
        """get() returns the stored string value for a known key."""
        from solution import MemoryStore

        store = MemoryStore()
        store.memories["name"] = {"value": "Alice", "embedding": [0.1]}
        self.assertEqual(store.get("name"), "Alice")

    def test_get_returns_none_for_unknown_key(self):
        """get() returns None for a key that was never saved."""
        from solution import MemoryStore

        store = MemoryStore()
        self.assertIsNone(store.get("nonexistent_key"))


# ---------------------------------------------------------------------------
# MemoryStore.search
# ---------------------------------------------------------------------------

class TestMemoryStoreSearch(unittest.TestCase):
    """Tests for MemoryStore.search()"""

    def _make_store_with_memories(self):
        """Create a MemoryStore pre-populated with test memories (no real embeddings)."""
        from solution import MemoryStore

        store = MemoryStore()
        # Use orthogonal embeddings so we can control similarity scores
        store.memories = {
            "bug": {"value": "Fixed race condition", "embedding": [1.0, 0.0, 0.0, 0.0]},
            "project": {"value": "Fraud detection pipeline", "embedding": [0.0, 1.0, 0.0, 0.0]},
            "name": {"value": "Alice", "embedding": [0.0, 0.0, 1.0, 0.0]},
        }
        return store

    @patch("solution.MemoryStore._embed")
    def test_search_returns_list_of_tuples(self, mock_embed):
        """search() returns a list of (key, value) tuples."""
        from solution import MemoryStore

        mock_embed.return_value = [1.0, 0.0, 0.0, 0.0]  # closest to "bug"
        store = self._make_store_with_memories()

        results = store.search("bug", top_k=2)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        for item in results:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)

    @patch("solution.MemoryStore._embed")
    def test_search_returns_most_similar_first(self, mock_embed):
        """search() returns results sorted by cosine similarity descending."""
        from solution import MemoryStore

        # Query embedding is [1,0,0,0] — cosine sim=1.0 with "bug", 0.0 with others
        mock_embed.return_value = [1.0, 0.0, 0.0, 0.0]
        store = self._make_store_with_memories()

        results = store.search("race condition", top_k=3)

        # "bug" should come first
        self.assertEqual(results[0][0], "bug")
        self.assertEqual(results[0][1], "Fixed race condition")

    @patch("solution.MemoryStore._embed")
    def test_search_respects_top_k(self, mock_embed):
        """search() returns at most top_k results."""
        from solution import MemoryStore

        mock_embed.return_value = [1.0, 0.0, 0.0, 0.0]
        store = self._make_store_with_memories()

        results = store.search("anything", top_k=1)
        self.assertEqual(len(results), 1)

    @patch("solution.MemoryStore._embed")
    def test_search_returns_empty_list_for_empty_store(self, mock_embed):
        """search() returns [] when the store has no memories."""
        from solution import MemoryStore

        mock_embed.return_value = [0.1, 0.2, 0.3, 0.4]
        store = MemoryStore()

        results = store.search("anything", top_k=3)
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# MemoryAgent
# ---------------------------------------------------------------------------

class TestMemoryAgent(unittest.TestCase):
    """Tests for MemoryAgent.chat()"""

    @patch("solution.get_anthropic_client")
    @patch("solution.MemoryStore.search")
    def test_chat_returns_string(self, mock_search, mock_get_client):
        """chat() returns a non-empty string."""
        from solution import MemoryAgent, MemoryStore

        mock_search.return_value = [("name", "Alice")]
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello Alice!")]
        mock_client.messages.create.return_value = mock_response

        store = MemoryStore()
        agent = MemoryAgent(store)
        result = agent.chat("Who am I?")

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("solution.get_anthropic_client")
    @patch("solution.MemoryStore.search")
    def test_chat_includes_memories_in_system_prompt(self, mock_search, mock_get_client):
        """chat() includes retrieved memories in the system prompt."""
        from solution import MemoryAgent, MemoryStore

        mock_search.return_value = [("name", "Alice"), ("project", "fraud detection")]
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Here is what I know...")]
        mock_client.messages.create.return_value = mock_response

        store = MemoryStore()
        agent = MemoryAgent(store)
        agent.chat("Tell me about my project")

        call_kwargs = mock_client.messages.create.call_args[1]
        system_prompt = call_kwargs.get("system", "")
        self.assertIn("Alice", system_prompt)
        self.assertIn("fraud detection", system_prompt)


if __name__ == "__main__":
    unittest.main()
