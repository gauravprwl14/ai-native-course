"""
Lab 47 — Mini GraphRAG Pipeline
---------------------------------
Build a knowledge graph pipeline: entity extraction, relationship extraction,
graph construction, BFS traversal, and graph querying.

Fill in every TODO to complete this lab.
No external libraries required — only Python standard library.

Run: python solution.py
Test: cd .. && pytest tests/ -v
"""

import re
from dataclasses import dataclass, field
from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    name: str
    type: str  # PERSON, ORG, PRODUCT, LOCATION, ENTITY, etc.


@dataclass
class Relationship:
    subject: str   # entity name
    predicate: str # relationship type e.g. WORKS_AT, MAKES, RELATED_TO
    obj: str       # entity name (object)


@dataclass
class KnowledgeGraph:
    entities: dict[str, Entity] = field(default_factory=dict)
    # adjacency: entity_name -> list of (predicate, target_entity_name)
    adjacency: dict[str, list[tuple[str, str]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    relationships: list[Relationship] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def extract_entities_simple(text: str) -> list[Entity]:
    """
    Simple rule-based entity extraction using regex.

    Args:
        text: Input text to extract entities from

    Returns:
        List of unique Entity objects (no duplicate names)
    """
    # TODO: Use re.findall with pattern r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    #       to find all capitalized noun phrases in text
    # TODO: Deduplicate by name (use a set to track seen names)
    # TODO: Create Entity(name=match, type="ENTITY") for each unique match
    # TODO: Return the list of Entity objects
    pass


# ---------------------------------------------------------------------------
# Relationship extraction
# ---------------------------------------------------------------------------

def extract_relationships_from_pairs(
    text: str, entities: list[Entity]
) -> list[Relationship]:
    """
    Extract relationships when two entity names appear in the same sentence.

    Args:
        text: Input text
        entities: List of entities to look for

    Returns:
        List of Relationship objects (predicate="RELATED_TO")
    """
    # TODO: Split text by '. ' to get sentences
    # TODO: For each sentence, find which entity names appear in it
    # TODO: If 2 or more entity names appear, create a Relationship:
    #       subject=first_entity, predicate="RELATED_TO", obj=second_entity
    # TODO: Return all relationships found
    pass


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(
    entities: list[Entity], relationships: list[Relationship]
) -> KnowledgeGraph:
    """
    Build a KnowledgeGraph from a list of entities and relationships.

    Args:
        entities: List of Entity objects
        relationships: List of Relationship objects

    Returns:
        A KnowledgeGraph with adjacency lists populated
    """
    # TODO: Create a KnowledgeGraph()
    # TODO: Add all entities to graph.entities (keyed by entity.name)
    # TODO: For each relationship:
    #   - Add (predicate, obj) to graph.adjacency[subject]
    #   - Add (predicate + "_REVERSE", subject) to graph.adjacency[obj]
    #   - Append relationship to graph.relationships
    # TODO: Return the graph
    pass


# ---------------------------------------------------------------------------
# Graph traversal
# ---------------------------------------------------------------------------

def find_connected(
    graph: KnowledgeGraph, start_entity: str, max_hops: int = 2
) -> list[str]:
    """
    BFS from start_entity to find all reachable entities within max_hops.

    Args:
        graph: The KnowledgeGraph
        start_entity: Name of the starting entity
        max_hops: Maximum traversal depth

    Returns:
        List of reachable entity names (excluding start_entity)
    """
    # TODO: Check if start_entity is in graph.adjacency; return [] if not
    # TODO: BFS:
    #   - Use deque, initialize with (start_entity, 0)
    #   - Track visited set (start with {start_entity})
    #   - For each node at depth < max_hops, expand its neighbors
    #   - Add newly visited neighbors to visited and result list
    # TODO: Return list of connected entity names (excluding start_entity)
    pass


# ---------------------------------------------------------------------------
# Graph query
# ---------------------------------------------------------------------------

def query_graph(graph: KnowledgeGraph, query: str) -> str:
    """
    Answer a query by finding mentioned entities and their graph connections.

    Args:
        graph: The KnowledgeGraph
        query: Natural language query string

    Returns:
        String describing entities related to the query entities
    """
    # TODO: Find entity names from graph.entities that appear in query (case-insensitive)
    # TODO: If no entities found, return "No relevant entities found"
    # TODO: For each found entity, call find_connected(graph, entity, max_hops=2)
    # TODO: Format result as: "Entities related to {entity}: {comma_separated_connected}"
    # TODO: Join multiple entity results with newline and return
    pass


# ---------------------------------------------------------------------------
# Manual smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    passages = [
        "Apple is a technology company founded by Steve Jobs.",
        "Tim Cook is the CEO of Apple.",
        "Apple makes the iPhone and the MacBook.",
        "Steve Jobs also co-founded Pixar.",
        "The iPhone uses chips manufactured by Samsung.",
    ]

    text = " ".join(passages)

    print("=== Entity Extraction ===")
    entities = extract_entities_simple(text)
    for e in entities:
        print(f"  {e.name} ({e.type})")

    print("\n=== Relationship Extraction ===")
    relationships = extract_relationships_from_pairs(text, entities)
    for r in relationships:
        print(f"  {r.subject} --{r.predicate}--> {r.obj}")

    print("\n=== Build Graph ===")
    graph = build_graph(entities, relationships)
    print(f"  Entities: {len(graph.entities)}")
    print(f"  Relationships: {len(graph.relationships)}")

    print("\n=== Graph Traversal (Apple, 2 hops) ===")
    connected = find_connected(graph, "Apple", max_hops=2)
    print(f"  {connected}")

    print("\n=== Graph Query ===")
    result = query_graph(graph, "What is related to Apple?")
    print(f"  {result}")

    print("\n=== Flat Keyword Search (for comparison) ===")
    keyword = "Apple"
    flat_results = [p for p in passages if keyword in p]
    print(f"  Sentences containing '{keyword}':")
    for s in flat_results:
        print(f"    - {s}")
