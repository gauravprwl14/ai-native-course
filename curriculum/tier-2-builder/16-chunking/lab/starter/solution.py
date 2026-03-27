"""Lab 16: Chunking Strategies"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared"))

import re
import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(ENCODING.encode(text))


def fixed_size_chunk(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """
    Split text into fixed-size character chunks with overlap.

    # TODO:
    # chunks = []
    # i = 0
    # while i < len(text):
    #   chunk = text[i:i+chunk_size]
    #   chunks.append(chunk)
    #   i += chunk_size - overlap
    # return chunks
    """
    raise NotImplementedError("Implement fixed_size_chunk")


def sentence_chunk(text: str, max_tokens: int = 256) -> list[str]:
    """
    Split text into chunks at sentence boundaries, respecting max_tokens.

    # TODO:
    # 1. Split text into sentences using regex: re.split(r'(?<=[.!?])\s+', text)
    # 2. Accumulate sentences into a chunk until adding the next sentence would exceed max_tokens
    # 3. When limit reached, save current chunk, start new one
    # 4. Return list of chunks
    """
    raise NotImplementedError("Implement sentence_chunk")


def chunk_with_metadata(text: str, source: str, chunk_size: int = 512, overlap: int = 50) -> list[dict]:
    """
    Chunk text and attach metadata.
    Returns list of {"text": str, "source": str, "chunk_index": int, "token_count": int}

    # TODO: use fixed_size_chunk, then build metadata dicts
    """
    raise NotImplementedError("Implement chunk_with_metadata")
