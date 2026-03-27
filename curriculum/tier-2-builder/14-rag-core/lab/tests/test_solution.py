"""
Tests for Lab 14 — RAG: Core Concept
These tests verify the function signatures and logic WITHOUT making real API calls.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, call

# Add starter (or solution for CI) to path so we test the learner's code.
# Set LAB_TARGET=solution to run tests against the reference solution.
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_embedding_response(vector: list[float]):
    """Create a mock OpenAI embeddings API response."""
    mock = MagicMock()
    mock.data = [MagicMock(embedding=vector)]
    return mock


def make_claude_response(text: str):
    """Create a mock Anthropic messages API response."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock


SAMPLE_DOCS = [
    {"id": "1", "text": "Enterprise customers get a 60-day refund window.", "source": "refund-policy.txt"},
    {"id": "2", "text": "Standard accounts have a 30-day refund window.", "source": "refund-policy.txt"},
    {"id": "3", "text": "Python SDK v2.0 was released on March 1, 2024.", "source": "changelog.txt"},
]

# Simple unit vectors for deterministic similarity testing
VEC_A = [1.0, 0.0, 0.0]
VEC_B = [0.0, 1.0, 0.0]
VEC_C = [0.0, 0.0, 1.0]
VEC_D = [1.0, 0.0, 0.0]  # identical to VEC_A

SAMPLE_INDEX = [
    {"id": "1", "text": "Enterprise refund", "source": "a.txt", "embedding": VEC_A},
    {"id": "2", "text": "Standard refund", "source": "b.txt", "embedding": VEC_B},
    {"id": "3", "text": "SDK changelog", "source": "c.txt", "embedding": VEC_C},
]


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors_return_one(self):
        """cosine_similarity returns 1.0 for two identical vectors."""
        from solution import cosine_similarity
        assert cosine_similarity(VEC_A, VEC_D) == pytest.approx(1.0)

    def test_orthogonal_vectors_return_zero(self):
        """cosine_similarity returns ~0.0 for orthogonal (perpendicular) vectors."""
        from solution import cosine_similarity
        result = cosine_similarity(VEC_A, VEC_B)
        assert result == pytest.approx(0.0, abs=1e-9)

    def test_zero_vector_returns_zero(self):
        """cosine_similarity returns 0.0 if either vector is all zeros."""
        from solution import cosine_similarity
        assert cosine_similarity([0.0, 0.0, 0.0], VEC_A) == 0.0


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

class TestBuildIndex:
    def test_returns_list_of_dicts_with_embedding_key(self):
        """build_index returns a list where each dict contains an 'embedding' key."""
        from solution import build_index

        mock_vector = [0.1, 0.2, 0.3]

        with patch('solution.get_openai_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.embeddings.create.return_value = make_embedding_response(mock_vector)

            result = build_index(SAMPLE_DOCS)

        assert isinstance(result, list)
        assert len(result) == len(SAMPLE_DOCS)
        for doc in result:
            assert "embedding" in doc, "Each document dict must contain an 'embedding' key"

    def test_calls_embeddings_api_once_per_document(self):
        """build_index calls the OpenAI embeddings API exactly once per document."""
        from solution import build_index

        mock_vector = [0.1, 0.2, 0.3]

        with patch('solution.get_openai_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.embeddings.create.return_value = make_embedding_response(mock_vector)

            build_index(SAMPLE_DOCS)

        assert mock_client.embeddings.create.call_count == len(SAMPLE_DOCS)

    def test_preserves_original_fields(self):
        """build_index preserves all original document fields."""
        from solution import build_index

        mock_vector = [0.5, 0.5]

        with patch('solution.get_openai_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.embeddings.create.return_value = make_embedding_response(mock_vector)

            result = build_index(SAMPLE_DOCS)

        for original, enriched in zip(SAMPLE_DOCS, result):
            assert enriched["id"] == original["id"]
            assert enriched["text"] == original["text"]
            assert enriched["source"] == original["source"]


# ---------------------------------------------------------------------------
# retrieve_chunks
# ---------------------------------------------------------------------------

class TestRetrieveChunks:
    def test_returns_list_sorted_by_similarity_descending(self):
        """retrieve_chunks returns results sorted by similarity, highest first."""
        from solution import retrieve_chunks

        # Query vector is identical to VEC_A — should rank chunk 1 highest
        with patch('solution.get_openai_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.embeddings.create.return_value = make_embedding_response(VEC_A)

            results = retrieve_chunks("enterprise refund", SAMPLE_INDEX, top_k=3)

        assert len(results) == 3
        similarities = [r["similarity"] for r in results]
        assert similarities == sorted(similarities, reverse=True), (
            "Results must be sorted by similarity descending"
        )

    def test_returns_top_k_results(self):
        """retrieve_chunks returns exactly top_k results."""
        from solution import retrieve_chunks

        with patch('solution.get_openai_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.embeddings.create.return_value = make_embedding_response(VEC_A)

            results = retrieve_chunks("test query", SAMPLE_INDEX, top_k=2)

        assert len(results) == 2

    def test_each_result_contains_similarity_key(self):
        """retrieve_chunks adds a 'similarity' key to each returned chunk."""
        from solution import retrieve_chunks

        with patch('solution.get_openai_client') as mock_client_fn:
            mock_client = MagicMock()
            mock_client_fn.return_value = mock_client
            mock_client.embeddings.create.return_value = make_embedding_response(VEC_B)

            results = retrieve_chunks("test", SAMPLE_INDEX, top_k=3)

        for result in results:
            assert "similarity" in result, "Each result must have a 'similarity' key"
            assert isinstance(result["similarity"], float)


# ---------------------------------------------------------------------------
# answer_question
# ---------------------------------------------------------------------------

class TestAnswerQuestion:
    def test_returns_dict_with_required_keys(self):
        """answer_question returns a dict with 'answer', 'sources', and 'chunks_used' keys."""
        from solution import answer_question

        with patch('solution.get_openai_client') as mock_openai_fn, \
             patch('solution.get_anthropic_client') as mock_anthropic_fn:

            mock_openai = MagicMock()
            mock_openai_fn.return_value = mock_openai
            mock_openai.embeddings.create.return_value = make_embedding_response(VEC_A)

            mock_anthropic = MagicMock()
            mock_anthropic_fn.return_value = mock_anthropic
            mock_anthropic.messages.create.return_value = make_claude_response(
                "Enterprise customers have a 60-day refund window."
            )

            result = answer_question("How long is the enterprise refund window?", SAMPLE_INDEX)

        assert "answer" in result
        assert "sources" in result
        assert "chunks_used" in result

    def test_answer_is_string(self):
        """answer_question result 'answer' value is a string."""
        from solution import answer_question

        with patch('solution.get_openai_client') as mock_openai_fn, \
             patch('solution.get_anthropic_client') as mock_anthropic_fn:

            mock_openai = MagicMock()
            mock_openai_fn.return_value = mock_openai
            mock_openai.embeddings.create.return_value = make_embedding_response(VEC_A)

            mock_anthropic = MagicMock()
            mock_anthropic_fn.return_value = mock_anthropic
            mock_anthropic.messages.create.return_value = make_claude_response("The answer is 60 days.")

            result = answer_question("test question", SAMPLE_INDEX)

        assert isinstance(result["answer"], str)
        assert result["answer"] == "The answer is 60 days."

    def test_sources_are_unique(self):
        """answer_question returns deduplicated sources — no duplicates."""
        from solution import answer_question

        # Index where all chunks have the same source
        same_source_index = [
            {"id": "1", "text": "Chunk A", "source": "policy.txt", "embedding": VEC_A},
            {"id": "2", "text": "Chunk B", "source": "policy.txt", "embedding": VEC_B},
            {"id": "3", "text": "Chunk C", "source": "policy.txt", "embedding": VEC_C},
        ]

        with patch('solution.get_openai_client') as mock_openai_fn, \
             patch('solution.get_anthropic_client') as mock_anthropic_fn:

            mock_openai = MagicMock()
            mock_openai_fn.return_value = mock_openai
            mock_openai.embeddings.create.return_value = make_embedding_response(VEC_A)

            mock_anthropic = MagicMock()
            mock_anthropic_fn.return_value = mock_anthropic
            mock_anthropic.messages.create.return_value = make_claude_response("Answer.")

            result = answer_question("question", same_source_index, top_k=3)

        # "policy.txt" appears 3 times in retrieved chunks but sources must be unique
        assert len(result["sources"]) == len(set(result["sources"])), (
            "sources must not contain duplicates"
        )
        assert result["sources"] == ["policy.txt"]

    def test_calls_retrieve_then_claude(self):
        """answer_question calls the embeddings API (for retrieval) then calls Claude."""
        from solution import answer_question

        with patch('solution.get_openai_client') as mock_openai_fn, \
             patch('solution.get_anthropic_client') as mock_anthropic_fn:

            mock_openai = MagicMock()
            mock_openai_fn.return_value = mock_openai
            mock_openai.embeddings.create.return_value = make_embedding_response(VEC_A)

            mock_anthropic = MagicMock()
            mock_anthropic_fn.return_value = mock_anthropic
            mock_anthropic.messages.create.return_value = make_claude_response("Answer.")

            answer_question("test question", SAMPLE_INDEX)

        # Both APIs must have been called
        assert mock_openai.embeddings.create.call_count >= 1
        assert mock_anthropic.messages.create.call_count == 1

    def test_chunks_used_matches_top_k(self):
        """answer_question 'chunks_used' value equals the top_k argument."""
        from solution import answer_question

        with patch('solution.get_openai_client') as mock_openai_fn, \
             patch('solution.get_anthropic_client') as mock_anthropic_fn:

            mock_openai = MagicMock()
            mock_openai_fn.return_value = mock_openai
            mock_openai.embeddings.create.return_value = make_embedding_response(VEC_A)

            mock_anthropic = MagicMock()
            mock_anthropic_fn.return_value = mock_anthropic
            mock_anthropic.messages.create.return_value = make_claude_response("Answer.")

            result = answer_question("question", SAMPLE_INDEX, top_k=2)

        assert result["chunks_used"] == 2
