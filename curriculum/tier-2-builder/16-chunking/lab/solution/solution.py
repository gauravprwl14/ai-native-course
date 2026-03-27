"""Lab 16: Chunking Strategies — Reference Solution"""
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

    Each chunk is at most chunk_size characters. Consecutive chunks overlap
    by `overlap` characters — the last `overlap` chars of chunk N are the
    first `overlap` chars of chunk N+1.
    """
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def sentence_chunk(text: str, max_tokens: int = 256) -> list[str]:
    """
    Split text into chunks at sentence boundaries, respecting max_tokens.

    Splits on sentence-ending punctuation (. ! ?) followed by whitespace.
    Accumulates sentences until adding the next would exceed max_tokens,
    then saves the current chunk and starts a new one.
    """
    stripped = text.strip()
    if not stripped:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', stripped)

    chunks = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        if current_tokens + sentence_tokens > max_tokens and current_sentences:
            # Save the current chunk and start fresh
            chunks.append(" ".join(current_sentences))
            current_sentences = []
            current_tokens = 0

        current_sentences.append(sentence)
        current_tokens += sentence_tokens

    # Flush the last chunk
    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def chunk_with_metadata(text: str, source: str, chunk_size: int = 512, overlap: int = 50) -> list[dict]:
    """
    Chunk text and attach metadata to each chunk.

    Returns a list of dicts:
        {
            "text": str,          — chunk content
            "source": str,        — passed-in source identifier
            "chunk_index": int,   — 0-indexed position
            "token_count": int    — tiktoken token count for this chunk
        }
    """
    raw_chunks = fixed_size_chunk(text, chunk_size=chunk_size, overlap=overlap)
    return [
        {
            "text": chunk,
            "source": source,
            "chunk_index": i,
            "token_count": count_tokens(chunk),
        }
        for i, chunk in enumerate(raw_chunks)
    ]
