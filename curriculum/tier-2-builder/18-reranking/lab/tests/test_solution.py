"""Tests for Lab 18 — Re-ranking"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'shared'))


def _make_mock_response(text: str):
    """Build a mock Anthropic API response with the given text."""
    content_block = MagicMock()
    content_block.text = text
    response = MagicMock()
    response.content = [content_block]
    return response


class TestScoreChunkRelevance:
    def test_returns_integer(self):
        """score_chunk_relevance returns an int."""
        from solution import score_chunk_relevance

        mock_response = _make_mock_response("7")
        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = score_chunk_relevance("What is the vacation policy?", "Employees get 20 days vacation.")

        assert isinstance(result, int)

    def test_returns_value_between_1_and_10(self):
        """score_chunk_relevance returns a value in [1, 10]."""
        from solution import score_chunk_relevance

        mock_response = _make_mock_response("8")
        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = score_chunk_relevance("What is the vacation policy?", "Employees get 20 days vacation.")

        assert 1 <= result <= 10

    def test_clamps_out_of_range_score(self):
        """score_chunk_relevance clamps scores outside [1, 10]."""
        from solution import score_chunk_relevance

        mock_response = _make_mock_response("15")  # out of range
        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            result = score_chunk_relevance("Any query", "Any chunk")

        assert result == 10  # clamped to max

    def test_uses_temperature_zero(self):
        """score_chunk_relevance calls the API with temperature=0."""
        from solution import score_chunk_relevance

        mock_response = _make_mock_response("5")
        with patch("solution.get_anthropic_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_fn.return_value = mock_client

            score_chunk_relevance("query", "chunk")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs.get("temperature") == 0 or (
            "temperature" in str(call_kwargs) and "0" in str(call_kwargs)
        )


class TestLlmRerank:
    def test_returns_list_of_top_k_tuples(self):
        """llm_rerank returns a list of exactly top_k tuples."""
        from solution import llm_rerank

        chunks = ["chunk a", "chunk b", "chunk c", "chunk d", "chunk e", "chunk f"]
        scores = [3, 7, 5, 9, 2, 6]

        with patch("solution.score_chunk_relevance", side_effect=scores):
            result = llm_rerank("query", chunks, top_k=3)

        assert isinstance(result, list)
        assert len(result) == 3

    def test_sorts_by_score_descending(self):
        """llm_rerank returns results sorted by score highest first."""
        from solution import llm_rerank

        chunks = ["low", "high", "mid"]
        scores = [2, 9, 5]

        with patch("solution.score_chunk_relevance", side_effect=scores):
            result = llm_rerank("query", chunks, top_k=3)

        returned_scores = [score for _, score in result]
        assert returned_scores == sorted(returned_scores, reverse=True)

    def test_returns_chunk_score_tuples(self):
        """llm_rerank returns (str, int) tuples."""
        from solution import llm_rerank

        chunks = ["alpha", "beta", "gamma"]
        scores = [4, 8, 6]

        with patch("solution.score_chunk_relevance", side_effect=scores):
            result = llm_rerank("query", chunks, top_k=2)

        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            chunk_text, score = item
            assert isinstance(chunk_text, str)
            assert isinstance(score, int)


class TestTwoStageRetrieve:
    def test_returns_list_of_strings(self):
        """two_stage_retrieve returns a list of strings."""
        from solution import two_stage_retrieve

        chunks = [f"chunk {i}" for i in range(10)]
        embeddings = [[float(i), float(i), float(i)] for i in range(1, 11)]
        query_embedding = [5.0, 5.0, 5.0]

        with patch("solution.llm_rerank") as mock_rerank:
            mock_rerank.return_value = [("chunk 5", 9), ("chunk 4", 7), ("chunk 6", 6)]
            result = two_stage_retrieve(
                query="test query",
                chunks=chunks,
                chunk_embeddings=embeddings,
                query_embedding=query_embedding,
                initial_k=5,
                final_k=3,
            )

        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    def test_returns_at_most_final_k_items(self):
        """two_stage_retrieve returns at most final_k items."""
        from solution import two_stage_retrieve

        chunks = [f"chunk {i}" for i in range(10)]
        embeddings = [[float(i), float(i), float(i)] for i in range(1, 11)]
        query_embedding = [5.0, 5.0, 5.0]

        with patch("solution.llm_rerank") as mock_rerank:
            mock_rerank.return_value = [("chunk 5", 9), ("chunk 4", 7)]
            result = two_stage_retrieve(
                query="test query",
                chunks=chunks,
                chunk_embeddings=embeddings,
                query_embedding=query_embedding,
                initial_k=5,
                final_k=2,
            )

        assert len(result) <= 2
