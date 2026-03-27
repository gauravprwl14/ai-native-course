"""Lab 06: Inference via API"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import time
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def run_inference(prompt: str, system_prompt: str = None) -> str:
    """
    Run a single inference call.
    # TODO: Call the Anthropic client with messages=[{"role": "user", "content": prompt}]
    # If system_prompt is provided, include system=system_prompt in the call
    # Return response.content[0].text
    """
    raise NotImplementedError("Implement run_inference")


def batch_inference(prompts: list[str]) -> list[str]:
    """
    Run inference on multiple prompts.
    # TODO: Call run_inference for each prompt, return list of responses
    """
    raise NotImplementedError("Implement batch_inference")


def measure_inference_latency(prompt: str, n: int = 3) -> dict:
    """
    Measure average inference latency over n runs.
    # TODO:
    # Run inference n times, record time.time() before and after each call
    # Return {"avg_latency_ms": float, "min_ms": float, "max_ms": float, "n": n}
    """
    raise NotImplementedError("Implement measure_inference_latency")


if __name__ == "__main__":
    print("Running single inference...")
    response = run_inference("What is inference in the context of LLMs? Answer in one sentence.")
    print(f"Response: {response}\n")

    print("Running batch inference on 3 prompts...")
    prompts = [
        "What is inference? (one sentence)",
        "What is training? (one sentence)",
        "What is fine-tuning? (one sentence)",
    ]
    responses = batch_inference(prompts)
    for i, (p, r) in enumerate(zip(prompts, responses)):
        print(f"[{i}] {p}\n    → {r}\n")

    print("Measuring latency over 3 runs...")
    stats = measure_inference_latency("What is 2 + 2?", n=3)
    print(f"avg: {stats['avg_latency_ms']:.0f}ms | min: {stats['min_ms']:.0f}ms | max: {stats['max_ms']:.0f}ms")
