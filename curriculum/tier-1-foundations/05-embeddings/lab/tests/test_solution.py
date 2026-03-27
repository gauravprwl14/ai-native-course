"""Tests for Lab 05 — Semantic Search with Embeddings"""

import sys
import math
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))


def _make_mock_embedding_response(vector: list[float]):
    """Helper: build a mock OpenAI embeddings response."""
    embedding_obj = MagicMock()
    embedding_obj.embedding = vector
    response = MagicMock()
    response.data = [embedding_obj]
    return response


class TestEmbedText:
    def test_calls_openai_with_correct_model(self):
        from solution import embed_text, EMBEDDING_MODEL

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [0.1] * 1536
        )

        with patch("solution.get_openai_client", return_value=mock_client):
            embed_text("hello world")

        mock_client.embeddings.create.assert_called_once()
        call_kwargs = mock_client.embeddings.create.call_args
        assert call_kwargs.kwargs.get("model") == EMBEDDING_MODEL or (
            len(call_kwargs.args) > 0 and EMBEDDING_MODEL in call_kwargs.args
        )

    def test_returns_list_of_floats(self):
        from solution import embed_text

        fake_vector = [0.23, -0.14, 0.87] + [0.0] * 1533  # 1536 floats total
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            fake_vector
        )

        with patch("solution.get_openai_client", return_value=mock_client):
            result = embed_text("test sentence")

        assert isinstance(result, list)
        assert all(isinstance(x, float) for x in result)

    def test_returns_correct_vector(self):
        from solution import embed_text

        fake_vector = [float(i) / 1536 for i in range(1536)]
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            fake_vector
        )

        with patch("solution.get_openai_client", return_value=mock_client):
            result = embed_text("any text")

        assert result == fake_vector

    def test_passes_input_text_to_api(self):
        from solution import embed_text

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = _make_mock_embedding_response(
            [0.0] * 1536
        )

        with patch("solution.get_openai_client", return_value=mock_client):
            embed_text("specific query text")

        call_kwargs = mock_client.embeddings.create.call_args
        # input could be positional or keyword
        all_args = str(call_kwargs)
        assert "specific query text" in all_args


class TestCosineSimilarity:
    def test_identical_vectors_return_one(self):
        from solution import cosine_similarity

        v = [1.0, 0.0, 0.0]
        result = cosine_similarity(v, v)
        assert abs(result - 1.0) < 1e-6

    def test_orthogonal_vectors_return_zero(self):
        from solution import cosine_similarity

        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        result = cosine_similarity(v1, v2)
        assert abs(result - 0.0) < 1e-6

    def test_opposite_vectors_return_minus_one(self):
        from solution import cosine_similarity

        v1 = [1.0, 0.0]
        v2 = [-1.0, 0.0]
        result = cosine_similarity(v1, v2)
        assert abs(result - (-1.0)) < 1e-6

    def test_returns_float(self):
        from solution import cosine_similarity

        result = cosine_similarity([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
        assert isinstance(result, float)

    def test_score_in_valid_range(self):
        from solution import cosine_similarity

        v1 = [0.5, 0.3, -0.2, 0.8]
        v2 = [0.1, -0.4, 0.9, 0.2]
        result = cosine_similarity(v1, v2)
        assert -1.0 <= result <= 1.0

    def test_known_similarity_value(self):
        from solution import cosine_similarity

        # [1, 1] vs [1, 0] → cos(45°) = 1/√2 ≈ 0.7071
        v1 = [1.0, 1.0]
        v2 = [1.0, 0.0]
        result = cosine_similarity(v1, v2)
        assert abs(result - (1.0 / math.sqrt(2))) < 1e-6


class TestFindMostSimilar:
    def _make_patcher(self, embedding_map: dict[str, list[float]]):
        """Return a side_effect function for embed_text that uses a fixed map."""

        def fake_embed(text):
            return embedding_map[text]

        return fake_embed

    def test_returns_tuple(self):
        from solution import find_most_similar

        # "a" is most similar to query
        embedding_map = {
            "query": [1.0, 0.0],
            "a": [0.9, 0.1],
            "b": [0.0, 1.0],
        }

        with patch("solution.embed_text", side_effect=self._make_patcher(embedding_map)):
            result = find_most_similar("query", ["a", "b"])

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_returns_most_similar_string(self):
        from solution import find_most_similar

        embedding_map = {
            "query": [1.0, 0.0],
            "close": [0.95, 0.05],
            "far": [0.0, 1.0],
            "opposite": [-1.0, 0.0],
        }

        with patch("solution.embed_text", side_effect=self._make_patcher(embedding_map)):
            best, score = find_most_similar("query", ["close", "far", "opposite"])

        assert best == "close"

    def test_returned_score_is_float(self):
        from solution import find_most_similar

        embedding_map = {
            "q": [1.0, 0.0],
            "c1": [0.8, 0.2],
            "c2": [0.2, 0.8],
        }

        with patch("solution.embed_text", side_effect=self._make_patcher(embedding_map)):
            _, score = find_most_similar("q", ["c1", "c2"])

        assert isinstance(score, float)

    def test_score_matches_expected_cosine(self):
        from solution import find_most_similar, cosine_similarity

        embedding_map = {
            "q": [1.0, 0.0],
            "best": [1.0, 0.0],
            "other": [0.0, 1.0],
        }

        with patch("solution.embed_text", side_effect=self._make_patcher(embedding_map)):
            _, score = find_most_similar("q", ["best", "other"])

        assert abs(score - 1.0) < 1e-6
