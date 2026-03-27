"""Tests for Lab 17 — Hybrid Search"""

import sys
import os
import math
import pytest

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))


# ---------------------------------------------------------------------------
# bm25_search
# ---------------------------------------------------------------------------

class TestBM25Search:
    def test_returns_list_of_tuples(self):
        """bm25_search returns a list of (int, float) tuples."""
        from solution import bm25_search

        documents = ["hello world", "foo bar", "hello foo"]
        results = bm25_search("hello", documents, top_k=2)

        assert isinstance(results, list)
        assert len(results) > 0
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            idx, score = item
            assert isinstance(idx, (int, float))  # numpy int is acceptable
            assert isinstance(score, float)

    def test_finds_matching_document_at_top(self):
        """The document containing the query keywords ranks first."""
        from solution import bm25_search

        documents = [
            "The Toyota Camry XSE V6 has 301 horsepower.",
            "Electric vehicles are growing in market share.",
            "Sedans remain popular in the US market.",
        ]
        results = bm25_search("Toyota Camry", documents, top_k=3)
        top_idx = int(results[0][0])
        assert top_idx == 0, (
            f"Expected doc 0 (Toyota Camry) at top, got doc {top_idx}"
        )


# ---------------------------------------------------------------------------
# reciprocal_rank_fusion
# ---------------------------------------------------------------------------

class TestReciprocalRankFusion:
    def test_returns_sorted_by_score(self):
        """Results are sorted by RRF score descending."""
        from solution import reciprocal_rank_fusion

        rankings = [[0, 1, 2], [1, 0, 2]]
        results = reciprocal_rank_fusion(rankings)
        scores = [score for _, score in results]
        assert scores == sorted(scores, reverse=True), (
            "Results should be sorted by RRF score descending"
        )

    def test_boosts_documents_in_multiple_lists(self):
        """A document appearing in both lists scores higher than one in only one list."""
        from solution import reciprocal_rank_fusion

        # Doc 1 appears in both lists at decent ranks
        # Doc 3 appears in only one list at rank 1
        rankings = [
            [3, 1, 2],   # list 0: doc 3 first, doc 1 second
            [1, 2, 0],   # list 1: doc 1 first
        ]
        results = reciprocal_rank_fusion(rankings)
        score_map = dict(results)

        # Doc 1 should beat doc 3 because it appears in both lists
        assert score_map[1] > score_map[3], (
            f"Doc 1 (in both lists) should outscore doc 3 (only list 0). "
            f"Doc 1 score: {score_map[1]:.5f}, Doc 3 score: {score_map[3]:.5f}"
        )

    def test_handles_single_ranking(self):
        """RRF with a single ranking returns results ordered by that ranking's order."""
        from solution import reciprocal_rank_fusion

        ranking = [2, 0, 1]
        results = reciprocal_rank_fusion([ranking])
        # Doc 2 should be first (rank 0 in only list → highest score)
        assert int(results[0][0]) == 2, (
            f"Expected doc 2 first, got doc {results[0][0]}"
        )

    def test_rrf_score_formula(self):
        """Verifies the actual RRF score calculation for a simple case."""
        from solution import reciprocal_rank_fusion

        k = 60
        # Single ranking [0, 1]: doc 0 at rank 0, doc 1 at rank 1
        results = reciprocal_rank_fusion([[0, 1]], k=k)
        score_map = dict(results)

        expected_doc0 = 1.0 / (k + 0 + 1)  # 1/61
        expected_doc1 = 1.0 / (k + 1 + 1)  # 1/62

        assert math.isclose(score_map[0], expected_doc0, rel_tol=1e-9), (
            f"Doc 0 score: expected {expected_doc0}, got {score_map[0]}"
        )
        assert math.isclose(score_map[1], expected_doc1, rel_tol=1e-9), (
            f"Doc 1 score: expected {expected_doc1}, got {score_map[1]}"
        )


# ---------------------------------------------------------------------------
# hybrid_search
# ---------------------------------------------------------------------------

class TestHybridSearch:
    _documents = [
        "The Toyota Camry XSE V6 towing capacity is 1000 lbs.",
        "Electric vehicles are growing in popularity.",
        "The 2024 Camry has a new infotainment system.",
        "Sedans are popular in the US market.",
    ]
    _embeddings = [
        [0.9, 0.1, 0.0],
        [0.1, 0.9, 0.1],
        [0.8, 0.2, 0.1],
        [0.5, 0.5, 0.2],
    ]
    _query_embedding = [0.85, 0.15, 0.0]

    def test_returns_top_k_results(self):
        """hybrid_search returns exactly top_k results."""
        from solution import hybrid_search

        for top_k in [1, 2, 3]:
            results = hybrid_search(
                "Toyota Camry",
                self._documents,
                self._embeddings,
                self._query_embedding,
                top_k=top_k,
            )
            assert len(results) == top_k, (
                f"Expected {top_k} results, got {len(results)}"
            )

    def test_returns_list_of_tuples(self):
        """hybrid_search returns a list of (int, float) tuples."""
        from solution import hybrid_search

        results = hybrid_search(
            "Toyota Camry",
            self._documents,
            self._embeddings,
            self._query_embedding,
            top_k=2,
        )
        assert isinstance(results, list)
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 2
            idx, score = item
            assert isinstance(score, float)


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    def test_identical_vectors_return_one(self):
        """cosine_similarity of a vector with itself is 1.0."""
        from solution import cosine_similarity

        v = [1.0, 2.0, 3.0]
        result = cosine_similarity(v, v)
        assert math.isclose(result, 1.0, rel_tol=1e-9), (
            f"Expected 1.0 for identical vectors, got {result}"
        )

    def test_orthogonal_vectors_return_zero(self):
        """cosine_similarity of orthogonal vectors is 0.0."""
        from solution import cosine_similarity

        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        result = cosine_similarity(v1, v2)
        assert math.isclose(result, 0.0, abs_tol=1e-9), (
            f"Expected 0.0 for orthogonal vectors, got {result}"
        )
