"""Tests for Lab 16 — Chunking Strategies"""

import sys
import os
import pytest

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))


# ---------------------------------------------------------------------------
# fixed_size_chunk
# ---------------------------------------------------------------------------

class TestFixedSizeChunk:
    def test_returns_multiple_chunks_for_long_text(self):
        """A text longer than chunk_size produces more than one chunk."""
        from solution import fixed_size_chunk

        text = "A" * 1000
        chunks = fixed_size_chunk(text, chunk_size=200, overlap=20)
        assert len(chunks) > 1

    def test_respects_chunk_size(self):
        """No chunk is longer than chunk_size characters."""
        from solution import fixed_size_chunk

        text = "Hello world! " * 100
        chunk_size = 100
        chunks = fixed_size_chunk(text, chunk_size=chunk_size, overlap=10)
        for chunk in chunks:
            assert len(chunk) <= chunk_size, (
                f"Chunk exceeds chunk_size={chunk_size}: {len(chunk)} chars"
            )

    def test_chunks_have_overlap(self):
        """The first word of chunk N+1 also appears at the end of chunk N."""
        from solution import fixed_size_chunk

        # Use a text where overlap content is identifiable
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 10  # 260 chars
        overlap = 10
        chunks = fixed_size_chunk(text, chunk_size=50, overlap=overlap)

        assert len(chunks) >= 2, "Need at least 2 chunks to test overlap"

        # The last `overlap` chars of chunk 0 should equal the first `overlap` chars of chunk 1
        assert chunks[0][-overlap:] == chunks[1][:overlap], (
            f"Expected overlap of {overlap} chars between chunk 0 and chunk 1. "
            f"End of chunk 0: {chunks[0][-overlap:]!r}, "
            f"Start of chunk 1: {chunks[1][:overlap]!r}"
        )

    def test_single_chunk_when_text_shorter_than_chunk_size(self):
        """Short text produces exactly one chunk containing all text."""
        from solution import fixed_size_chunk

        text = "Short text."
        chunks = fixed_size_chunk(text, chunk_size=512, overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == text


# ---------------------------------------------------------------------------
# sentence_chunk
# ---------------------------------------------------------------------------

class TestSentenceChunk:
    def test_splits_at_sentence_boundaries(self):
        """Each chunk contains only complete sentences."""
        from solution import sentence_chunk

        text = (
            "The contract was signed on January 1st. "
            "The termination clause requires 30 days notice. "
            "Payment terms are net-30. "
            "Disputes shall be resolved in New York State."
        )
        chunks = sentence_chunk(text, max_tokens=50)
        # Verify every chunk ends with sentence-ending punctuation
        for chunk in chunks:
            assert chunk.strip()[-1] in ".!?", (
                f"Chunk does not end with sentence punctuation: {chunk!r}"
            )

    def test_respects_max_tokens(self):
        """No chunk significantly exceeds max_tokens (allow a single oversized sentence)."""
        from solution import sentence_chunk
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        text = " ".join([
            "This is sentence number one.",
            "This is sentence number two.",
            "This is sentence number three.",
            "This is sentence number four.",
            "This is sentence number five.",
        ])
        max_tokens = 15
        chunks = sentence_chunk(text, max_tokens=max_tokens)

        for chunk in chunks:
            token_count = len(enc.encode(chunk))
            # Allow a single sentence that is itself > max_tokens to pass through
            sentences_in_chunk = len([s for s in chunk.split(". ") if s])
            if sentences_in_chunk > 1:
                assert token_count <= max_tokens * 2, (
                    f"Multi-sentence chunk exceeds reasonable token limit: "
                    f"{token_count} tokens in {chunk!r}"
                )

    def test_returns_empty_for_empty_input(self):
        """Empty or whitespace-only input returns an empty list."""
        from solution import sentence_chunk

        assert sentence_chunk("") == []
        assert sentence_chunk("   ") == []


# ---------------------------------------------------------------------------
# chunk_with_metadata
# ---------------------------------------------------------------------------

class TestChunkWithMetadata:
    def test_returns_list_of_dicts(self):
        """chunk_with_metadata returns a list of dicts."""
        from solution import chunk_with_metadata

        result = chunk_with_metadata("Hello world! " * 50, source="test.txt")
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)

    def test_dicts_have_correct_keys(self):
        """Every dict has the required keys: text, source, chunk_index, token_count."""
        from solution import chunk_with_metadata

        result = chunk_with_metadata("Sample text. " * 50, source="sample.pdf")
        required_keys = {"text", "source", "chunk_index", "token_count"}
        for item in result:
            assert required_keys.issubset(item.keys()), (
                f"Dict missing required keys. Got: {set(item.keys())}"
            )

    def test_includes_source_in_metadata(self):
        """Every chunk carries the source identifier passed in."""
        from solution import chunk_with_metadata

        source = "annual_report_2024.pdf"
        result = chunk_with_metadata("Content. " * 50, source=source)
        for item in result:
            assert item["source"] == source, (
                f"Expected source={source!r}, got {item['source']!r}"
            )

    def test_chunk_index_is_sequential(self):
        """chunk_index values are 0, 1, 2, ... in order."""
        from solution import chunk_with_metadata

        result = chunk_with_metadata("Word " * 200, source="doc.txt", chunk_size=100, overlap=10)
        indices = [item["chunk_index"] for item in result]
        expected = list(range(len(result)))
        assert indices == expected, (
            f"chunk_index values not sequential: {indices}"
        )
