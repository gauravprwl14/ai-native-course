"""
Lab 47 — Mini GraphRAG Pipeline (Reference Solution)
------------------------------------------------------
Fully working implementation of the GraphRAG pipeline lab.
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
    predicate: str # relationship type
    obj: str       # entity name (object)


@dataclass
class KnowledgeGraph:
    entities: dict[str, Entity] = field(default_factory=dict)
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

    Matches capitalized noun phrases: 'Apple', 'Tim Cook', 'New York'.
    """
    pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    matches = re.findall(pattern, text)
    seen = set()
    entities = []
    for name in matches:
        if name not in seen:
            seen.add(name)
            entities.append(Entity(name=name, type="ENTITY"))
    return entities


# ---------------------------------------------------------------------------
# Relationship extraction
# ---------------------------------------------------------------------------

def extract_relationships_from_pairs(
    text: str, entities: list[Entity]
) -> list[Relationship]:
    """
    Extract relationships from entity co-occurrence within sentences.
    """
    relationships = []
    sentences = text.split(". ")
    entity_names = [e.name for e in entities]

    for sentence in sentences:
        # Find which entities appear in this sentence
        found = [name for name in entity_names if name in sentence]
        if len(found) >= 2:
            # Create relationship between the first two entities found
            relationships.append(Relationship(
                subject=found[0],
                predicate="RELATED_TO",
                obj=found[1],
            ))

    return relationships


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(
    entities: list[Entity], relationships: list[Relationship]
) -> KnowledgeGraph:
    """
    Build a KnowledgeGraph with forward and reverse adjacency edges.
    """
    graph = KnowledgeGraph()

    # Add entities
    for entity in entities:
        graph.entities[entity.name] = entity

    # Add relationships and reverse edges
    for rel in relationships:
        graph.adjacency[rel.subject].append((rel.predicate, rel.obj))
        graph.adjacency[rel.obj].append((rel.predicate + "_REVERSE", rel.subject))
        graph.relationships.append(rel)

    return graph


# ---------------------------------------------------------------------------
# Graph traversal
# ---------------------------------------------------------------------------

def find_connected(
    graph: KnowledgeGraph, start_entity: str, max_hops: int = 2
) -> list[str]:
    """
    BFS traversal from start_entity, up to max_hops depth.
    """
    if start_entity not in graph.adjacency:
        return []

    visited = {start_entity}
    queue: deque[tuple[str, int]] = deque([(start_entity, 0)])
    connected = []

    while queue:
        node, depth = queue.popleft()
        if depth >= max_hops:
            continue
        for _predicate, neighbor in graph.adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                connected.append(neighbor)
                queue.append((neighbor, depth + 1))

    return connected


# ---------------------------------------------------------------------------
# Graph query
# ---------------------------------------------------------------------------

def query_graph(graph: KnowledgeGraph, query: str) -> str:
    """
    Answer a query by matching entity names and traversing the graph.
    """
    query_lower = query.lower()
    found_entities = [
        name for name in graph.entities
        if name.lower() in query_lower
    ]

    if not found_entities:
        return "No relevant entities found"

    results = []
    for entity in found_entities:
        connected = find_connected(graph, entity, max_hops=2)
        results.append(f"Entities related to {entity}: {', '.join(connected)}")

    return "\n".join(results)


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
