"""Tests for Lab 29: Prepare a Fine-tuning Dataset"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock, patch


def _make_example(user="What is your return policy?", assistant="We accept returns within 30 days."):
    """Helper: build a valid messages example."""
    return {"messages": [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]}


class TestValidateJsonlExample(unittest.TestCase):
    """Tests for validate_jsonl_example — no API calls needed."""

    def setUp(self):
        from solution import validate_jsonl_example
        self.validate = validate_jsonl_example

    def test_valid_example_returns_true(self):
        example = _make_example()
        ok, err = self.validate(example)
        self.assertTrue(ok)
        self.assertEqual(err, "")

    def test_missing_messages_key(self):
        ok, err = self.validate({"data": []})
        self.assertFalse(ok)
        self.assertIn("messages", err.lower())

    def test_not_a_dict_returns_false(self):
        ok, err = self.validate([{"role": "user", "content": "hi"}])
        self.assertFalse(ok)

    def test_too_few_messages(self):
        ok, err = self.validate({"messages": [{"role": "user", "content": "hi"}]})
        self.assertFalse(ok)

    def test_invalid_role_returns_false(self):
        example = {"messages": [
            {"role": "human", "content": "hi"},
            {"role": "assistant", "content": "hello"}
        ]}
        ok, err = self.validate(example)
        self.assertFalse(ok)
        self.assertIn("role", err.lower())

    def test_last_message_must_be_assistant(self):
        example = {"messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "thanks"}
        ]}
        ok, err = self.validate(example)
        self.assertFalse(ok)
        self.assertIn("assistant", err.lower())

    def test_empty_content_returns_false(self):
        example = {"messages": [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "response"}
        ]}
        ok, err = self.validate(example)
        self.assertFalse(ok)

    def test_system_message_allowed(self):
        example = {"messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"}
        ]}
        ok, err = self.validate(example)
        self.assertTrue(ok)
        self.assertEqual(err, "")


class TestSplitDataset(unittest.TestCase):
    """Tests for split_dataset — pure logic, no API calls."""

    def setUp(self):
        from solution import split_dataset
        self.split = split_dataset

    def test_correct_split_sizes(self):
        examples = [_make_example() for _ in range(10)]
        train, val = self.split(examples, val_ratio=0.1)
        self.assertEqual(len(train), 9)
        self.assertEqual(len(val), 1)

    def test_all_examples_preserved(self):
        examples = [_make_example() for _ in range(20)]
        train, val = self.split(examples, val_ratio=0.2)
        self.assertEqual(len(train) + len(val), 20)

    def test_deterministic_with_seed(self):
        examples = [_make_example(user=f"question {i}") for i in range(10)]
        train1, val1 = self.split(examples)
        train2, val2 = self.split(examples)
        self.assertEqual(train1, train2)
        self.assertEqual(val1, val2)

    def test_returns_tuple_of_lists(self):
        examples = [_make_example() for _ in range(5)]
        result = self.split(examples)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], list)
        self.assertIsInstance(result[1], list)


class TestGenerateTrainingExample(unittest.TestCase):
    """Tests for generate_training_example — mocks the API."""

    def _mock_response(self, user="What is your policy?", assistant="Our policy is X."):
        import json
        text_block = MagicMock()
        text_block.text = json.dumps({"user": user, "assistant": assistant})
        response = MagicMock()
        response.content = [text_block]
        return response

    def test_returns_messages_dict(self):
        from solution import generate_training_example
        mock_response = self._mock_response()
        with patch("solution.get_anthropic_client") as mock_factory:
            mock_client = MagicMock()
            mock_factory.return_value = mock_client
            mock_client.messages.create.return_value = mock_response
            result = generate_training_example("return policy")

        self.assertIn("messages", result)
        self.assertIsInstance(result["messages"], list)

    def test_messages_have_user_and_assistant(self):
        from solution import generate_training_example
        mock_response = self._mock_response()
        with patch("solution.get_anthropic_client") as mock_factory:
            mock_client = MagicMock()
            mock_factory.return_value = mock_client
            mock_client.messages.create.return_value = mock_response
            result = generate_training_example("shipping")

        roles = [m["role"] for m in result["messages"]]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)


if __name__ == "__main__":
    unittest.main()
