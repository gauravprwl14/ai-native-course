# Lab 47 — Build a Mini GraphRAG Pipeline

## Goal

Build a minimal knowledge graph pipeline in pure Python using only the standard library and regex. No spaCy, no graph database, no LLM API calls required. You will implement entity extraction, relationship extraction, graph construction, BFS traversal, and graph querying.

## Tasks

### Task 1: extract_entities_simple

Extract entities from text using a regex pattern that matches capitalized noun phrases.

- Use pattern `r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'` to find candidate entities
- Assign type `"ENTITY"` to all extracted entities (simplified)
- Deduplicate by name — no two `Entity` objects should have the same `name`
- Return a list of `Entity` objects

### Task 2: extract_relationships_from_pairs

Extract co-occurrence-based relationships from text.

- Split text by `'. '` to get sentences
- For each sentence, find which entities (by name) appear in it
- If 2 or more entities appear in the same sentence, create a `Relationship` with predicate `"RELATED_TO"` between the first two entities found
- Return all `Relationship` objects found across all sentences

### Task 3: build_graph

Build a `KnowledgeGraph` from entities and relationships.

- Add all entities to `graph.entities` (keyed by name)
- For each relationship, add `(predicate, obj)` to `graph.adjacency[subject]`
- Also add the reverse edge: `(predicate + "_REVERSE", subject)` to `graph.adjacency[obj]`
- Add each relationship to `graph.relationships`
- Return the completed `KnowledgeGraph`

### Task 4: find_connected

Traverse the graph using BFS to find all entities reachable from a starting entity.

- Use BFS with a `deque`
- Track visited nodes
- Stop expanding at `max_hops` depth
- Return list of reachable entity names (excluding the start entity itself)

### Task 5: query_graph

Answer natural language queries by entity matching and graph traversal.

- Find all entity names in `graph.entities` that appear in the query (case-insensitive)
- If no entities found, return `"No relevant entities found"`
- For each found entity, call `find_connected` with `max_hops=2`
- Format and return results as: `"Entities related to {entity_name}: {comma_separated_list}"`

## Running Tests

```bash
cd curriculum/tier-4-architect/47-graphrag/lab
pytest tests/ -v
```

## Files

- `starter/solution.py` — fill in the TODOs
- `solution/solution.py` — reference implementation
- `tests/test_solution.py` — test suite (no external dependencies)
