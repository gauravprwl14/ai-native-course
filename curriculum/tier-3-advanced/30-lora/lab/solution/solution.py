"""Lab 30: LoRA Configuration & Dataset Preparation — Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))
from dataclasses import dataclass


@dataclass
class LoRAConfig:
    rank: int
    alpha: float
    target_modules: list[str]
    dropout: float = 0.1

    @property
    def scaling(self) -> float:
        """Scaling factor applied to LoRA output: alpha / rank."""
        return self.alpha / self.rank


def create_lora_config(rank: int, alpha: float, target_modules: list[str]) -> LoRAConfig:
    """Create and return a LoRAConfig with the given parameters."""
    return LoRAConfig(rank=rank, alpha=alpha, target_modules=target_modules)


def format_for_trainer(examples: list[dict]) -> list[dict]:
    """
    Format {"instruction", "output"} examples for HuggingFace Trainer.
    Returns list of {"text": "### Instruction:\\n...\\n### Response:\\n..."} dicts.
    """
    return [
        {
            "text": (
                f"### Instruction:\n{ex['instruction']}\n"
                f"### Response:\n{ex['output']}"
            )
        }
        for ex in examples
    ]


def estimate_trainable_params(
    total_model_params: int,
    rank: int,
    num_lora_layers: int,
    layer_dim: int = 4096,
) -> dict:
    """
    Estimate trainable LoRA parameters vs total model parameters.

    Per LoRA layer: 2 matrices of size (layer_dim × rank) and (rank × layer_dim)
    Total trainable = 2 * rank * layer_dim * num_lora_layers
    """
    trainable = 2 * rank * layer_dim * num_lora_layers
    percentage = round(trainable / total_model_params * 100, 4)
    return {
        "trainable": trainable,
        "total": total_model_params,
        "percentage": percentage,
    }
