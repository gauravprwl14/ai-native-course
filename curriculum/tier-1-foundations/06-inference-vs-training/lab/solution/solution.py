"""Lab 06: Inference via API — Reference Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import time
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def run_inference(prompt: str, system_prompt: str = None) -> str:
    """
    Run a single inference call.

    Args:
        prompt: The user message to send to the model
        system_prompt: Optional system prompt to set model behaviour

    Returns:
        The model's text response as a string
    """
    client = get_anthropic_client()

    kwargs = {
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }

    if system_prompt is not None:
        kwargs["system"] = system_prompt

    response = client.messages.create(**kwargs)
    return response.content[0].text


def batch_inference(prompts: list[str]) -> list[str]:
    """
    Run inference on multiple prompts.

    Args:
        prompts: List of user messages to process

    Returns:
        List of model responses in the same order as the input
    """
    return [run_inference(prompt) for prompt in prompts]


def measure_inference_latency(prompt: str, n: int = 3) -> dict:
    """
    Measure average inference latency over n runs.

    Args:
        prompt: The prompt to send for each run
        n: Number of inference runs to perform

    Returns:
        Dict with avg_latency_ms, min_ms, max_ms, and n
    """
    latencies = []

    for _ in range(n):
        start = time.time()
        run_inference(prompt)
        end = time.time()
        latencies.append((end - start) * 1000)

    return {
        "avg_latency_ms": sum(latencies) / len(latencies),
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "n": n,
    }


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
