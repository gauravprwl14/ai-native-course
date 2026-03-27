"""Tests for Lab 46 — AI Gateway"""

import sys
import os
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


def _make_mock_provider(response_text="Mock response", input_tokens=100, output_tokens=50):
    """Return a mock provider callable."""
    def provider(model, prompt, max_tokens):
        return (response_text, input_tokens, output_tokens)
    return provider


class TestRateLimiter(unittest.TestCase):

    def test_allows_first_request(self):
        from solution import RateLimiter
        rl = RateLimiter(requests_per_minute=5)
        assert rl.is_allowed("key-a") is True

    def test_allows_up_to_limit(self):
        from solution import RateLimiter
        rl = RateLimiter(requests_per_minute=3)
        assert rl.is_allowed("key-a") is True
        assert rl.is_allowed("key-a") is True
        assert rl.is_allowed("key-a") is True

    def test_rejects_over_limit(self):
        from solution import RateLimiter
        rl = RateLimiter(requests_per_minute=3)
        rl.is_allowed("key-a")
        rl.is_allowed("key-a")
        rl.is_allowed("key-a")
        # 4th request should be rejected
        assert rl.is_allowed("key-a") is False

    def test_different_keys_independent(self):
        from solution import RateLimiter
        rl = RateLimiter(requests_per_minute=2)
        rl.is_allowed("key-a")
        rl.is_allowed("key-a")
        # key-a is at limit, but key-b should be allowed
        assert rl.is_allowed("key-a") is False
        assert rl.is_allowed("key-b") is True


class TestRegisterProvider(unittest.TestCase):

    def test_register_and_retrieve(self):
        from solution import AIGateway
        gw = AIGateway()
        handler = _make_mock_provider()
        gw.register_provider("anthropic", handler)
        assert "anthropic" in gw._providers
        assert gw._providers["anthropic"] is handler

    def test_register_multiple_providers(self):
        from solution import AIGateway
        gw = AIGateway()
        gw.register_provider("anthropic", _make_mock_provider())
        gw.register_provider("openai", _make_mock_provider())
        assert len(gw._providers) == 2


class TestGetProvider(unittest.TestCase):

    def test_claude_maps_to_anthropic(self):
        from solution import AIGateway
        gw = AIGateway()
        assert gw._get_provider("claude-sonnet-4-5") == "anthropic"

    def test_gpt_maps_to_openai(self):
        from solution import AIGateway
        gw = AIGateway()
        assert gw._get_provider("gpt-4o") == "openai"

    def test_llama_maps_to_local(self):
        from solution import AIGateway
        gw = AIGateway()
        assert gw._get_provider("llama-3-8b") == "local"

    def test_unknown_defaults_to_openai(self):
        from solution import AIGateway
        gw = AIGateway()
        assert gw._get_provider("unknown-model-xyz") == "openai"


class TestCalculateCost(unittest.TestCase):

    def test_anthropic_cost(self):
        from solution import AIGateway
        gw = AIGateway()
        # 1M input tokens at $3/M = $3.00
        cost = gw._calculate_cost("anthropic", 1_000_000, 0)
        assert abs(cost - 3.0) < 0.0001

    def test_local_cost_is_zero(self):
        from solution import AIGateway
        gw = AIGateway()
        cost = gw._calculate_cost("local", 100_000, 50_000)
        assert cost == 0.0

    def test_cost_scales_with_tokens(self):
        from solution import AIGateway
        gw = AIGateway()
        cost_small = gw._calculate_cost("openai", 100, 50)
        cost_large = gw._calculate_cost("openai", 1000, 500)
        assert cost_large > cost_small


class TestGatewayRoute(unittest.TestCase):

    def _make_gateway(self, rpm=100):
        from solution import AIGateway, RateLimiter
        gw = AIGateway(rate_limiter=RateLimiter(requests_per_minute=rpm))
        gw.register_provider("anthropic", _make_mock_provider())
        gw.register_provider("openai", _make_mock_provider())
        gw.register_provider("local", _make_mock_provider())
        return gw

    def test_basic_route_returns_response(self):
        from solution import GatewayRequest
        gw = self._make_gateway()
        resp = gw.route(GatewayRequest(key="k", model="claude-sonnet", prompt="Hi"))
        assert resp.response == "Mock response"
        assert resp.provider == "anthropic"
        assert resp.cached is False

    def test_second_identical_call_is_cached(self):
        from solution import GatewayRequest
        gw = self._make_gateway()
        gw.route(GatewayRequest(key="k", model="claude-sonnet", prompt="Hi"))
        resp2 = gw.route(GatewayRequest(key="k", model="claude-sonnet", prompt="Hi"))
        assert resp2.cached is True

    def test_rate_limit_raises_value_error(self):
        from solution import AIGateway, RateLimiter, GatewayRequest
        gw = AIGateway(rate_limiter=RateLimiter(requests_per_minute=2))
        gw.register_provider("openai", _make_mock_provider())
        gw.route(GatewayRequest(key="k", model="gpt-4o", prompt="a"))
        gw.route(GatewayRequest(key="k", model="gpt-4o", prompt="b"))
        with self.assertRaises(ValueError):
            gw.route(GatewayRequest(key="k", model="gpt-4o", prompt="c"))

    def test_log_entry_created(self):
        from solution import GatewayRequest
        gw = self._make_gateway()
        gw.route(GatewayRequest(key="team-a", model="gpt-4o", prompt="Hello"))
        assert len(gw.logs) == 1
        assert gw.logs[0].key == "team-a"
        assert gw.logs[0].provider == "openai"

    def test_cost_is_positive_for_paid_provider(self):
        from solution import GatewayRequest
        gw = self._make_gateway()
        resp = gw.route(GatewayRequest(key="k", model="claude-sonnet", prompt="Hi"))
        assert resp.cost_usd > 0


class TestCostByKey(unittest.TestCase):

    def test_cost_by_key_sums_correctly(self):
        from solution import AIGateway, RateLimiter, GatewayRequest
        gw = AIGateway(rate_limiter=RateLimiter(requests_per_minute=100))
        gw.register_provider("openai", _make_mock_provider(input_tokens=1_000_000, output_tokens=0))
        gw.route(GatewayRequest(key="team-a", model="gpt-4o", prompt="Q1"))
        gw.route(GatewayRequest(key="team-a", model="gpt-4o", prompt="Q2"))
        gw.route(GatewayRequest(key="team-b", model="gpt-4o", prompt="Q3"))
        costs = gw.get_cost_by_key()
        # team-a made 2 requests with 1M input tokens each at $5/M = $5.00 each = $10.00
        assert "team-a" in costs
        assert "team-b" in costs
        assert costs["team-a"] > costs["team-b"]

    def test_empty_logs_returns_empty_dict(self):
        from solution import AIGateway
        gw = AIGateway()
        assert gw.get_cost_by_key() == {}
