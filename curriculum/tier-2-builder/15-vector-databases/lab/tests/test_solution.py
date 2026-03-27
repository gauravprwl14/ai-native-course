"""Tests for Lab 15: Vector Databases with Chroma"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "starter"))

import unittest
from unittest.mock import MagicMock, patch, call


class TestCreateCollection(unittest.TestCase):
    """Tests for create_collection()"""

    @patch("solution.chromadb")
    def test_uses_ephemeral_client_when_no_persist_dir(self, mock_chromadb):
        """create_collection with no persist_dir uses EphemeralClient."""
        from solution import create_collection

        mock_client = MagicMock()
        mock_chromadb.EphemeralClient.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        result = create_collection("test-collection")

        mock_chromadb.EphemeralClient.assert_called_once()
        mock_chromadb.PersistentClient.assert_not_called()
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test-collection",
            metadata={"hnsw:space": "cosine"}
        )
        self.assertEqual(result, mock_collection)

    @patch("solution.chromadb")
    def test_uses_persistent_client_when_persist_dir_provided(self, mock_chromadb):
        """create_collection with persist_dir uses PersistentClient with that path."""
        from solution import create_collection

        mock_client = MagicMock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection

        result = create_collection("my-collection", persist_dir="./test_db")

        mock_chromadb.PersistentClient.assert_called_once_with(path="./test_db")
        mock_chromadb.EphemeralClient.assert_not_called()
        mock_client.get_or_create_collection.assert_called_once_with(
            name="my-collection",
            metadata={"hnsw:space": "cosine"}
        )
        self.assertEqual(result, mock_collection)

    @patch("solution.chromadb")
    def test_collection_configured_with_cosine_space(self, mock_chromadb):
        """create_collection always uses hnsw:space=cosine."""
        from solution import create_collection

        mock_client = MagicMock()
        mock_chromadb.EphemeralClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = MagicMock()

        create_collection("cosine-test")

        _, kwargs = mock_client.get_or_create_collection.call_args
        self.assertEqual(kwargs.get("metadata", {}).get("hnsw:space"), "cosine")


class TestAddDocuments(unittest.TestCase):
    """Tests for add_documents()"""

    def _make_collection(self):
        collection = MagicMock()
        return collection

    @patch("solution.get_embeddings")
    def test_returns_correct_document_count(self, mock_get_embeddings):
        """add_documents returns the number of documents added."""
        from solution import add_documents

        mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        collection = self._make_collection()

        documents = [
            {"id": "d1", "text": "First doc", "source": "a.pdf"},
            {"id": "d2", "text": "Second doc", "source": "b.pdf"},
            {"id": "d3", "text": "Third doc", "source": "c.pdf"},
        ]
        result = add_documents(collection, documents)

        self.assertEqual(result, 3)

    @patch("solution.get_embeddings")
    def test_calls_collection_add_with_correct_params(self, mock_get_embeddings):
        """add_documents calls collection.add with correct ids, embeddings, documents, metadatas."""
        from solution import add_documents

        fake_embeddings = [[0.1, 0.2], [0.3, 0.4]]
        mock_get_embeddings.return_value = fake_embeddings
        collection = self._make_collection()

        documents = [
            {"id": "doc-1", "text": "Hello world", "source": "test.pdf"},
            {"id": "doc-2", "text": "Goodbye world", "source": "test.pdf"},
        ]
        add_documents(collection, documents)

        collection.add.assert_called_once_with(
            ids=["doc-1", "doc-2"],
            embeddings=fake_embeddings,
            documents=["Hello world", "Goodbye world"],
            metadatas=[{"source": "test.pdf"}, {"source": "test.pdf"}],
        )

    @patch("solution.get_embeddings")
    def test_gets_embeddings_in_single_batch(self, mock_get_embeddings):
        """add_documents calls get_embeddings once for all texts — not once per document."""
        from solution import add_documents

        mock_get_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        collection = self._make_collection()

        documents = [
            {"id": "d1", "text": "Doc one", "source": "x.pdf"},
            {"id": "d2", "text": "Doc two", "source": "x.pdf"},
            {"id": "d3", "text": "Doc three", "source": "x.pdf"},
        ]
        add_documents(collection, documents)

        # get_embeddings should be called exactly once, with all texts
        self.assertEqual(mock_get_embeddings.call_count, 1)
        called_texts = mock_get_embeddings.call_args[0][0]
        self.assertEqual(called_texts, ["Doc one", "Doc two", "Doc three"])

    @patch("solution.get_embeddings")
    def test_metadata_excludes_id_and_text(self, mock_get_embeddings):
        """add_documents metadata dicts contain all fields except 'id' and 'text'."""
        from solution import add_documents

        mock_get_embeddings.return_value = [[0.1, 0.2]]
        collection = self._make_collection()

        documents = [
            {
                "id": "doc-1",
                "text": "Some content",
                "source": "policy.pdf",
                "page": 3,
                "category": "hr",
            }
        ]
        add_documents(collection, documents)

        _, kwargs = collection.add.call_args
        meta = kwargs["metadatas"][0]
        self.assertNotIn("id", meta)
        self.assertNotIn("text", meta)
        self.assertEqual(meta["source"], "policy.pdf")
        self.assertEqual(meta["page"], 3)
        self.assertEqual(meta["category"], "hr")


class TestSearch(unittest.TestCase):
    """Tests for search()"""

    def _make_chroma_results(self, n=2):
        """Build a mock Chroma query result structure."""
        return {
            "ids": [["id-1", "id-2"][:n]],
            "documents": [["Text one", "Text two"][:n]],
            "distances": [[0.12, 0.34][:n]],
            "metadatas": [[{"source": "a.pdf"}, {"source": "b.pdf"}][:n]],
        }

    @patch("solution.get_embeddings")
    def test_search_calls_query_with_correct_n_results(self, mock_get_embeddings):
        """search passes top_k as n_results to collection.query."""
        from solution import search

        mock_get_embeddings.return_value = [[0.5, 0.6, 0.7]]
        collection = MagicMock()
        collection.query.return_value = self._make_chroma_results(n=2)

        search(collection, "test query", top_k=2)

        _, kwargs = collection.query.call_args
        self.assertEqual(kwargs.get("n_results"), 2)

    @patch("solution.get_embeddings")
    def test_search_returns_list_of_dicts_with_correct_keys(self, mock_get_embeddings):
        """search returns list of dicts each containing id, text, distance, metadata."""
        from solution import search

        mock_get_embeddings.return_value = [[0.1, 0.2]]
        collection = MagicMock()
        collection.query.return_value = self._make_chroma_results(n=2)

        results = search(collection, "a query", top_k=2)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIn("id", r)
            self.assertIn("text", r)
            self.assertIn("distance", r)
            self.assertIn("metadata", r)

    @patch("solution.get_embeddings")
    def test_search_passes_filter_as_where(self, mock_get_embeddings):
        """search passes filter dict as 'where' to collection.query."""
        from solution import search

        mock_get_embeddings.return_value = [[0.1, 0.2]]
        collection = MagicMock()
        collection.query.return_value = self._make_chroma_results(n=1)

        my_filter = {"source": {"$eq": "policy.pdf"}}
        search(collection, "query", top_k=1, filter=my_filter)

        _, kwargs = collection.query.call_args
        self.assertEqual(kwargs.get("where"), my_filter)

    @patch("solution.get_embeddings")
    def test_search_result_values_match_chroma_output(self, mock_get_embeddings):
        """search correctly maps Chroma result fields to output dict fields."""
        from solution import search

        mock_get_embeddings.return_value = [[0.9, 0.8]]
        collection = MagicMock()
        collection.query.return_value = {
            "ids": [["abc"]],
            "documents": [["The quick brown fox"]],
            "distances": [[0.07]],
            "metadatas": [[{"source": "fox.pdf", "page": 1}]],
        }

        results = search(collection, "foxes", top_k=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "abc")
        self.assertEqual(results[0]["text"], "The quick brown fox")
        self.assertAlmostEqual(results[0]["distance"], 0.07)
        self.assertEqual(results[0]["metadata"], {"source": "fox.pdf", "page": 1})


class TestDeleteDocument(unittest.TestCase):
    """Tests for delete_document()"""

    def test_calls_collection_delete_with_correct_id(self):
        """delete_document calls collection.delete with the doc_id wrapped in a list."""
        from solution import delete_document

        collection = MagicMock()
        delete_document(collection, "doc-42")

        collection.delete.assert_called_once_with(ids=["doc-42"])

    def test_returns_none(self):
        """delete_document returns None."""
        from solution import delete_document

        collection = MagicMock()
        result = delete_document(collection, "doc-1")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
