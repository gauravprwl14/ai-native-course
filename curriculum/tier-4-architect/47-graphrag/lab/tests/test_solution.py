"""Tests for Lab 47 — Mini GraphRAG Pipeline"""

import sys
import os
import unittest
from pathlib import Path

# Set LAB_TARGET=solution to run tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


class TestExtractEntitiesSimple(unittest.TestCase):

    def test_returns_list(self):
        from solution import extract_entities_simple
        result = extract_entities_simple("Apple is a company.")
        assert isinstance(result, list)

    def test_extracts_single_word_entities(self):
        from solution import extract_entities_simple
        entities = extract_entities_simple("Apple is based in Cupertino.")
        names = [e.name for e in entities]
        assert "Apple" in names
        assert "Cupertino" in names

    def test_extracts_multi_word_entities(self):
        from solution import extract_entities_simple
        entities = extract_entities_simple("Tim Cook leads Apple Inc.")
        names = [e.name for e in entities]
        assert "Tim Cook" in names

    def test_deduplicates_entities(self):
        from solution import extract_entities_simple
        entities = extract_entities_simple("Apple is a company. Apple makes products.")
        names = [e.name for e in entities]
        assert names.count("Apple") == 1

    def test_entity_type_is_entity(self):
        from solution import extract_entities_simple
        entities = extract_entities_simple("Apple is a company.")
        for e in entities:
            assert e.type == "ENTITY"

    def test_empty_text_returns_empty_list(self):
        from solution import extract_entities_simple
        assert extract_entities_simple("") == []

    def test_no_capitalized_words_returns_empty(self):
        from solution import extract_entities_simple
        entities = extract_entities_simple("hello world foo bar")
        assert len(entities) == 0


class TestExtractRelationshipsFromPairs(unittest.TestCase):

    def _make_entities(self, names):
        from solution import Entity
        return [Entity(name=n, type="ENTITY") for n in names]

    def test_co_occurring_entities_create_relationship(self):
        from solution import extract_relationships_from_pairs
        entities = self._make_entities(["Apple", "Tim Cook"])
        text = "Apple CEO Tim Cook announced the product."
        rels = extract_relationships_from_pairs(text, entities)
        assert len(rels) >= 1
        subjects = [r.subject for r in rels]
        assert "Apple" in subjects or "Tim Cook" in subjects

    def test_predicate_is_related_to(self):
        from solution import extract_relationships_from_pairs
        entities = self._make_entities(["Apple", "Tim Cook"])
        text = "Apple CEO Tim Cook announced the product."
        rels = extract_relationships_from_pairs(text, entities)
        for r in rels:
            assert r.predicate == "RELATED_TO"

    def test_no_relationship_when_entities_in_different_sentences(self):
        from solution import extract_relationships_from_pairs
        entities = self._make_entities(["Apple", "Samsung"])
        text = "Apple makes the iPhone. Samsung makes the Galaxy."
        rels = extract_relationships_from_pairs(text, entities)
        # Each sentence has only one entity — no co-occurrence
        assert len(rels) == 0

    def test_returns_list(self):
        from solution import extract_relationships_from_pairs
        result = extract_relationships_from_pairs("text", [])
        assert isinstance(result, list)


class TestBuildGraph(unittest.TestCase):

    def _setup(self):
        from solution import Entity, Relationship, build_graph
        entities = [
            Entity("Apple", "ENTITY"),
            Entity("iPhone", "ENTITY"),
        ]
        relationships = [
            Relationship("Apple", "MAKES", "iPhone"),
        ]
        graph = build_graph(entities, relationships)
        return graph

    def test_entities_added(self):
        graph = self._setup()
        assert "Apple" in graph.entities
        assert "iPhone" in graph.entities

    def test_forward_edge_added(self):
        graph = self._setup()
        edges = graph.adjacency["Apple"]
        assert ("MAKES", "iPhone") in edges

    def test_reverse_edge_added(self):
        graph = self._setup()
        edges = graph.adjacency["iPhone"]
        predicates = [pred for pred, _ in edges]
        assert any("REVERSE" in p for p in predicates)

    def test_relationships_list_populated(self):
        graph = self._setup()
        assert len(graph.relationships) == 1

    def test_empty_inputs_return_empty_graph(self):
        from solution import build_graph
        graph = build_graph([], [])
        assert len(graph.entities) == 0
        assert len(graph.relationships) == 0


class TestFindConnected(unittest.TestCase):

    def _make_chain_graph(self):
        """Build A → B → C → D"""
        from solution import Entity, Relationship, build_graph
        entities = [Entity(n, "ENTITY") for n in ["A", "B", "C", "D"]]
        rels = [
            Relationship("A", "NEXT", "B"),
            Relationship("B", "NEXT", "C"),
            Relationship("C", "NEXT", "D"),
        ]
        return build_graph(entities, rels)

    def test_finds_direct_neighbors(self):
        from solution import find_connected
        graph = self._make_chain_graph()
        connected = find_connected(graph, "A", max_hops=1)
        assert "B" in connected

    def test_max_hops_respected(self):
        from solution import find_connected
        graph = self._make_chain_graph()
        connected = find_connected(graph, "A", max_hops=1)
        # D is 3 hops away, should not appear with max_hops=1
        assert "D" not in connected

    def test_two_hops_reaches_two_levels(self):
        from solution import find_connected
        graph = self._make_chain_graph()
        connected = find_connected(graph, "A", max_hops=2)
        assert "B" in connected
        assert "C" in connected

    def test_unknown_entity_returns_empty(self):
        from solution import find_connected
        graph = self._make_chain_graph()
        assert find_connected(graph, "NONEXISTENT") == []

    def test_start_entity_not_in_result(self):
        from solution import find_connected
        graph = self._make_chain_graph()
        connected = find_connected(graph, "A", max_hops=3)
        assert "A" not in connected


class TestQueryGraph(unittest.TestCase):

    def _make_apple_graph(self):
        from solution import Entity, Relationship, build_graph
        entities = [
            Entity("Apple", "ENTITY"),
            Entity("iPhone", "ENTITY"),
            Entity("Tim Cook", "ENTITY"),
        ]
        rels = [
            Relationship("Apple", "MAKES", "iPhone"),
            Relationship("Tim Cook", "LEADS", "Apple"),
        ]
        return build_graph(entities, rels)

    def test_known_entity_returns_result(self):
        from solution import query_graph
        graph = self._make_apple_graph()
        result = query_graph(graph, "What is related to Apple?")
        assert "Apple" in result
        assert result != "No relevant entities found"

    def test_unknown_entity_returns_no_entities(self):
        from solution import query_graph
        graph = self._make_apple_graph()
        result = query_graph(graph, "What about Google?")
        assert result == "No relevant entities found"

    def test_result_is_string(self):
        from solution import query_graph
        graph = self._make_apple_graph()
        result = query_graph(graph, "Apple")
        assert isinstance(result, str)

    def test_case_insensitive_matching(self):
        from solution import query_graph
        graph = self._make_apple_graph()
        # Query uses lowercase "apple"
        result = query_graph(graph, "tell me about apple")
        assert result != "No relevant entities found"
