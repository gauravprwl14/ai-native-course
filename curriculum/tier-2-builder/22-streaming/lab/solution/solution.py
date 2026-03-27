"""Lab 22: Streaming (SSE) — Solution"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import time
from typing import Generator
from utils import get_anthropic_client

MODEL = "claude-3-haiku-20240307"


def stream_response(prompt: str, system_prompt: str = None) -> Generator[str, None, None]:
    """Stream response tokens as a generator. Yields each text chunk as it arrives."""
    client = get_anthropic_client()
    kwargs = {
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    with client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
            yield text


def stream_and_collect(prompt: str) -> dict:
    """
    Stream response and collect the full text + chunk count.
    Returns {"full_text": str, "chunk_count": int}
    """
    chunks = []
    for text in stream_response(prompt):
        chunks.append(text)
    return {
        "full_text": "".join(chunks),
        "chunk_count": len(chunks),
    }


def measure_ttft(prompt: str) -> float:
    """
    Measure time-to-first-token in milliseconds.
    Returns float (ms), or -1.0 if no response received.
    """
    start = time.time()
    for chunk in stream_response(prompt):
        ttft = (time.time() - start) * 1000
        return ttft  # return on FIRST chunk only
    return -1.0  # no response received


# ---------------------------------------------------------------------------
# Quick manual test (run: python solution.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== stream_response ===")
    for chunk in stream_response("Say hello in one word."):
        print(chunk, end="", flush=True)
    print()

    print("\n=== stream_and_collect ===")
    result = stream_and_collect("List 3 colors.")
    print(f"Full text: {result['full_text']}")
    print(f"Chunks: {result['chunk_count']}")

    print("\n=== measure_ttft ===")
    ttft = measure_ttft("Say hi.")
    print(f"TTFT: {ttft:.1f}ms")
