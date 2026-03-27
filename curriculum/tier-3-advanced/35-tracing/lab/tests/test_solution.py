"""Tests for Lab 35 — Tracing & Observability"""

import sys
import os
import time
import unittest

_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


class TestSpan(unittest.TestCase):
    def test_span_has_name(self):
        from solution import Span
        s = Span(name="test_span")
        self.assertEqual(s.name, "test_span")

    def test_span_defaults(self):
        from solution import Span
        s = Span(name="test_span")
        self.assertEqual(s.model, "")
        self.assertEqual(s.input_tokens, 0)
        self.assertEqual(s.output_tokens, 0)
        self.assertEqual(s.latency_ms, 0.0)
        self.assertIsNone(s.error)

    def test_span_with_all_fields(self):
        from solution import Span
        s = Span(
            name="generate",
            model="claude-3-haiku-20240307",
            input_tokens=500,
            output_tokens=200,
            latency_ms=350.5,
            error=None,
        )
        self.assertEqual(s.input_tokens, 500)
        self.assertEqual(s.output_tokens, 200)
        self.assertAlmostEqual(s.latency_ms, 350.5)


class TestTrace(unittest.TestCase):
    def _make_trace(self):
        from solution import Span, Trace
        t = Trace()
        t.add_span(Span(name="step1", input_tokens=100, output_tokens=50, latency_ms=100.0))
        t.add_span(Span(name="step2", input_tokens=200, output_tokens=80, latency_ms=200.0))
        return t

    def test_total_tokens(self):
        t = self._make_trace()
        # 100+50 + 200+80 = 430
        self.assertEqual(t.total_tokens, 430)

    def test_total_latency(self):
        t = self._make_trace()
        self.assertAlmostEqual(t.total_latency_ms, 300.0)

    def test_empty_trace_tokens(self):
        from solution import Trace
        t = Trace()
        self.assertEqual(t.total_tokens, 0)

    def test_empty_trace_latency(self):
        from solution import Trace
        t = Trace()
        self.assertEqual(t.total_latency_ms, 0)


class TestCalculateCost(unittest.TestCase):
    def test_returns_float(self):
        from solution import Span, Trace, calculate_cost_from_trace
        t = Trace()
        t.add_span(Span(name="gen", model="claude-3-haiku-20240307",
                        input_tokens=1000, output_tokens=200))
        cost = calculate_cost_from_trace(t)
        self.assertIsInstance(cost, float)

    def test_correct_cost_haiku(self):
        from solution import Span, Trace, calculate_cost_from_trace
        # 1000 input @ 0.00025/1K = 0.00025
        # 200 output @ 0.00125/1K = 0.00025
        # total = 0.00050
        t = Trace()
        t.add_span(Span(name="gen", model="claude-3-haiku-20240307",
                        input_tokens=1000, output_tokens=200))
        cost = calculate_cost_from_trace(t)
        self.assertAlmostEqual(cost, 0.00050, places=6)

    def test_zero_cost_unknown_model(self):
        from solution import Span, Trace, calculate_cost_from_trace
        t = Trace()
        t.add_span(Span(name="gen", model="unknown-model",
                        input_tokens=1000, output_tokens=500))
        cost = calculate_cost_from_trace(t)
        self.assertEqual(cost, 0.0)

    def test_zero_cost_empty_trace(self):
        from solution import Trace, calculate_cost_from_trace
        t = Trace()
        cost = calculate_cost_from_trace(t)
        self.assertEqual(cost, 0.0)

    def test_multi_span_cost(self):
        from solution import Span, Trace, calculate_cost_from_trace
        t = Trace()
        t.add_span(Span(name="s1", model="claude-3-haiku-20240307",
                        input_tokens=1000, output_tokens=0))
        t.add_span(Span(name="s2", model="claude-3-haiku-20240307",
                        input_tokens=0, output_tokens=1000))
        cost = calculate_cost_from_trace(t)
        # 1000 * 0.00025/1000 + 1000 * 0.00125/1000 = 0.00025 + 0.00125 = 0.00150
        self.assertAlmostEqual(cost, 0.00150, places=6)


class TestCreateSpan(unittest.TestCase):
    def test_returns_tuple(self):
        from solution import create_span
        result = create_span("test", lambda: 42)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_span_name(self):
        from solution import create_span
        span, _ = create_span("my_span", lambda: "ok")
        self.assertEqual(span.name, "my_span")

    def test_records_latency(self):
        from solution import create_span
        span, _ = create_span("slow_fn", lambda: time.sleep(0.01))
        self.assertGreater(span.latency_ms, 0.0)

    def test_returns_function_result(self):
        from solution import create_span
        _, result = create_span("add", lambda a, b: a + b, 3, 4)
        self.assertEqual(result, 7)

    def test_captures_exception(self):
        from solution import create_span
        def fail():
            raise ValueError("oops")
        span, result = create_span("failing_fn", fail)
        self.assertIsNotNone(span.error)
        self.assertIn("oops", span.error)
        self.assertIsNone(result)

    def test_no_exception_means_no_error(self):
        from solution import create_span
        span, result = create_span("ok_fn", lambda: "done")
        self.assertIsNone(span.error)
        self.assertEqual(result, "done")


if __name__ == "__main__":
    unittest.main()
