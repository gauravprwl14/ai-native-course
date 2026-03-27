"""Lab 30: LoRA Configuration & Dataset Preparation"""
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
    """
    Create and return a LoRAConfig dataclass with the given parameters.

    # TODO: return LoRAConfig(rank=rank, alpha=alpha, target_modules=target_modules)
    """
    raise NotImplementedError("Implement create_lora_config")


def format_for_trainer(examples: list[dict]) -> list[dict]:
    """
    Format examples for HuggingFace Trainer / SFTTrainer.

    Input:  list of {"instruction": str, "output": str}
    Output: list of {"text": "### Instruction:\\n{instruction}\\n### Response:\\n{output}"}

    The standard alpaca-style prompt format combines instruction and response
    into a single "text" field that the trainer uses for next-token prediction.

    # TODO: return a list where each dict has a "text" key with the formatted string
    """
    raise NotImplementedError("Implement format_for_trainer")


def estimate_trainable_params(
    total_model_params: int,
    rank: int,
    num_lora_layers: int,
    layer_dim: int = 4096,
) -> dict:
    """
    Estimate the number of trainable LoRA parameters vs total model parameters.

    LoRA adds two matrices per layer:
    - Matrix A: shape (layer_dim × rank)  → layer_dim * rank params
    - Matrix B: shape (rank × layer_dim)  → rank * layer_dim params
    - Total per layer: 2 * rank * layer_dim

    Args:
        total_model_params: total parameter count of the base model
        rank: LoRA rank (r)
        num_lora_layers: number of layers LoRA is applied to
        layer_dim: dimension of the weight matrices (default 4096 for 7B models)

    Returns:
        {
            "trainable": int,     # total trainable LoRA params
            "total": int,         # total_model_params (unchanged base)
            "percentage": float,  # trainable / total * 100, rounded to 4dp
        }

    # TODO: trainable = 2 * rank * layer_dim * num_lora_layers
    # TODO: percentage = round(trainable / total_model_params * 100, 4)
    # TODO: return the dict
    """
    raise NotImplementedError("Implement estimate_trainable_params")
