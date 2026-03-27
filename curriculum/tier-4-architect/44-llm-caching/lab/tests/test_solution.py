import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call

sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

from solution import CacheEntry, ExactCache, CachedLLMClient


class TestExactCacheMakeKey(unittest.TestCase):
    def setUp(self):
        self.cache = ExactCache()

    def test_same_inputs_produce_same_key(self):
        k1 = self.cache._make_key("Hello", "gpt-4")
        k2 = self.cache._make_key("Hello", "gpt-4")
        self.assertEqual(k1, k2)

    def test_different_prompts_produce_different_keys(self):
        k1 = self.cache._make_key("Hello", "gpt-4")
        k2 = self.cache._make_key("World", "gpt-4")
        self.assertNotEqual(k1, k2)

    def test_different_models_produce_different_keys(self):
        k1 = self.cache._make_key("Hello", "gpt-4")
        k2 = self.cache._make_key("Hello", "gpt-3.5-turbo")
        self.assertNotEqual(k1, k2)

    def test_different_params_produce_different_keys(self):
        k1 = self.cache._make_key("Hello", "gpt-4", temperature=0.0)
        k2 = self.cache._make_key("Hello", "gpt-4", temperature=0.5)
        self.assertNotEqual(k1, k2)

    def test_key_is_a_hex_string(self):
        key = self.cache._make_key("Hello", "gpt-4")
        self.assertIsInstance(key, str)
        # SHA256 hex digest is 64 chars
        self.assertEqual(len(key), 64)
        int(key, 16)  # should not raise — must be valid hex

    def test_param_order_does_not_matter(self):
        k1 = self.cache._make_key("Hello", "gpt-4", a=1, b=2)
        k2 = self.cache._make_key("Hello", "gpt-4", b=2, a=1)
        self.assertEqual(k1, k2)


class TestExactCacheGetSet(unittest.TestCase):
    def setUp(self):
        self.cache = ExactCache(ttl_seconds=60)

    def test_miss_returns_none(self):
        result = self.cache.get("Hello", "gpt-4")
        self.assertIsNone(result)

    def test_set_then_get_returns_value(self):
        self.cache.set("Hello", "gpt-4", "Hi there!")
        result = self.cache.get("Hello", "gpt-4")
        self.assertEqual(result, "Hi there!")

    def test_expired_entry_returns_none(self):
        self.cache.set("Hello", "gpt-4", "Hi!")
        # Manually expire the entry by backdating created_at
        key = self.cache._make_key("Hello", "gpt-4")
        self.cache._store[key].created_at = time.time() - 7200  # 2 hours ago
        result = self.cache.get("Hello", "gpt-4")
        self.assertIsNone(result)

    def test_expired_entry_is_removed_from_store(self):
        self.cache.set("Hello", "gpt-4", "Hi!")
        key = self.cache._make_key("Hello", "gpt-4")
        self.cache._store[key].created_at = time.time() - 7200
        self.cache.get("Hello", "gpt-4")  # trigger expiry check
        self.assertNotIn(key, self.cache._store)

    def test_different_params_are_separate_entries(self):
        self.cache.set("Hello", "gpt-4", "response-a", temperature=0.0)
        self.cache.set("Hello", "gpt-4", "response-b", temperature=0.5)
        r_a = self.cache.get("Hello", "gpt-4", temperature=0.0)
        r_b = self.cache.get("Hello", "gpt-4", temperature=0.5)
        self.assertEqual(r_a, "response-a")
        self.assertEqual(r_b, "response-b")


class TestCachedLLMClient(unittest.TestCase):
    def _make_client(self, ttl: float = 60):
        self.call_count = 0

        def mock_llm(prompt: str, model: str, **params) -> str:
            self.call_count += 1
            return f"Answer: {prompt}"

        self.mock_llm = mock_llm
        cache = ExactCache(ttl_seconds=ttl)
        return CachedLLMClient(llm_caller=mock_llm, cache=cache)

    def test_first_call_is_a_miss(self):
        client = self._make_client()
        client.generate("Hello", "gpt-4")
        self.assertEqual(self.call_count, 1)
        self.assertEqual(client.misses, 1)
        self.assertEqual(client.hits, 0)

    def test_second_identical_call_is_a_hit(self):
        client = self._make_client()
        r1 = client.generate("Hello", "gpt-4")
        r2 = client.generate("Hello", "gpt-4")
        self.assertEqual(self.call_count, 1)  # LLM called only once
        self.assertEqual(r1, r2)
        self.assertEqual(client.hits, 1)
        self.assertEqual(client.misses, 1)

    def test_different_prompts_are_both_misses(self):
        client = self._make_client()
        client.generate("Hello", "gpt-4")
        client.generate("World", "gpt-4")
        self.assertEqual(self.call_count, 2)
        self.assertEqual(client.misses, 2)
        self.assertEqual(client.hits, 0)

    def test_hit_rate_is_correct(self):
        client = self._make_client()
        client.generate("A", "gpt-4")  # miss
        client.generate("A", "gpt-4")  # hit
        client.generate("B", "gpt-4")  # miss
        self.assertAlmostEqual(client.hit_rate, 1 / 3, places=5)

    def test_hit_rate_is_zero_before_any_requests(self):
        client = self._make_client()
        self.assertEqual(client.hit_rate, 0.0)

    def test_hit_rate_is_one_when_all_hits(self):
        client = self._make_client()
        client.generate("X", "gpt-4")  # miss
        client.generate("X", "gpt-4")  # hit
        client.generate("X", "gpt-4")  # hit
        self.assertAlmostEqual(client.hit_rate, 2 / 3, places=5)

    def test_cached_response_equals_llm_response(self):
        client = self._make_client()
        r1 = client.generate("Hello", "gpt-4")
        r2 = client.generate("Hello", "gpt-4")
        self.assertEqual(r1, "Answer: Hello")
        self.assertEqual(r2, "Answer: Hello")


if __name__ == "__main__":
    unittest.main()
