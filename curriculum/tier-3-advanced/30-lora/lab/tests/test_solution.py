"""Tests for Lab 30: LoRA Configuration & Dataset Preparation"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest

from solution import LoRAConfig, create_lora_config, format_for_trainer, estimate_trainable_params


class TestCreateLoRAConfig(unittest.TestCase):
    """Tests for create_lora_config()"""

    def test_returns_lora_config_instance(self):
        config = create_lora_config(8, 16.0, ["q_proj", "v_proj"])
        self.assertIsInstance(config, LoRAConfig)

    def test_rank_is_set_correctly(self):
        config = create_lora_config(16, 32.0, ["q_proj"])
        self.assertEqual(config.rank, 16)

    def test_alpha_is_set_correctly(self):
        config = create_lora_config(8, 16.0, ["q_proj"])
        self.assertAlmostEqual(config.alpha, 16.0)

    def test_target_modules_is_set_correctly(self):
        modules = ["q_proj", "v_proj", "k_proj"]
        config = create_lora_config(8, 8.0, modules)
        self.assertEqual(config.target_modules, modules)

    def test_default_dropout(self):
        config = create_lora_config(8, 16.0, ["q_proj"])
        self.assertAlmostEqual(config.dropout, 0.1)

    def test_scaling_property(self):
        """scaling = alpha / rank"""
        config = create_lora_config(8, 16.0, ["q_proj"])
        self.assertAlmostEqual(config.scaling, 2.0)

    def test_scaling_when_alpha_equals_rank(self):
        """scaling = 1.0 when alpha == rank (common convention)"""
        config = create_lora_config(16, 16.0, ["q_proj"])
        self.assertAlmostEqual(config.scaling, 1.0)


class TestFormatForTrainer(unittest.TestCase):
    """Tests for format_for_trainer()"""

    def test_returns_list(self):
        result = format_for_trainer([{"instruction": "Say hi", "output": "Hi!"}])
        self.assertIsInstance(result, list)

    def test_each_item_has_text_key(self):
        examples = [
            {"instruction": "Summarise this", "output": "Summary here."},
            {"instruction": "Translate to French", "output": "Bonjour"},
        ]
        result = format_for_trainer(examples)
        for item in result:
            self.assertIn("text", item)

    def test_text_contains_instruction_header(self):
        result = format_for_trainer([{"instruction": "What is LoRA?", "output": "A technique."}])
        self.assertIn("### Instruction:", result[0]["text"])

    def test_text_contains_response_header(self):
        result = format_for_trainer([{"instruction": "What is LoRA?", "output": "A technique."}])
        self.assertIn("### Response:", result[0]["text"])

    def test_instruction_content_in_text(self):
        result = format_for_trainer([{"instruction": "Explain QLoRA", "output": "QLoRA is..."}])
        self.assertIn("Explain QLoRA", result[0]["text"])

    def test_output_content_in_text(self):
        result = format_for_trainer([{"instruction": "What is LoRA?", "output": "Low-Rank Adaptation"}])
        self.assertIn("Low-Rank Adaptation", result[0]["text"])

    def test_empty_list_returns_empty_list(self):
        self.assertEqual(format_for_trainer([]), [])

    def test_length_preserved(self):
        examples = [{"instruction": f"Q{i}", "output": f"A{i}"} for i in range(5)]
        result = format_for_trainer(examples)
        self.assertEqual(len(result), 5)


class TestEstimateTrainableParams(unittest.TestCase):
    """Tests for estimate_trainable_params()"""

    def test_returns_dict_with_required_keys(self):
        result = estimate_trainable_params(7_000_000_000, 8, 12)
        self.assertIn("trainable", result)
        self.assertIn("total", result)
        self.assertIn("percentage", result)

    def test_trainable_calculation(self):
        """trainable = 2 * rank * layer_dim * num_lora_layers"""
        result = estimate_trainable_params(
            total_model_params=7_000_000_000,
            rank=8,
            num_lora_layers=12,
            layer_dim=4096,
        )
        expected_trainable = 2 * 8 * 4096 * 12
        self.assertEqual(result["trainable"], expected_trainable)

    def test_total_equals_model_params(self):
        result = estimate_trainable_params(7_000_000_000, 8, 12)
        self.assertEqual(result["total"], 7_000_000_000)

    def test_percentage_is_small(self):
        """LoRA trainable % should be much less than 1% for typical configs."""
        result = estimate_trainable_params(7_000_000_000, 8, 12)
        self.assertLess(result["percentage"], 1.0)
        self.assertGreater(result["percentage"], 0.0)

    def test_percentage_increases_with_rank(self):
        """Higher rank means more trainable params."""
        low = estimate_trainable_params(7_000_000_000, 4, 12)
        high = estimate_trainable_params(7_000_000_000, 16, 12)
        self.assertGreater(high["percentage"], low["percentage"])

    def test_percentage_increases_with_more_layers(self):
        """More LoRA layers means more trainable params."""
        few = estimate_trainable_params(7_000_000_000, 8, 4)
        many = estimate_trainable_params(7_000_000_000, 8, 32)
        self.assertGreater(many["percentage"], few["percentage"])


if __name__ == "__main__":
    unittest.main()
