# Lab 41 — Build an MCP Server

## Problem Statement

You will implement a simplified MCP (Model Context Protocol) server using only Python's standard library. The goal is to understand MCP mechanics — tool registration, resource registration, discovery, and tool invocation — without depending on the `mcp` package.

---

### Class 1: `MCPTool`

A dataclass representing a callable MCP tool.

**Fields:**
- `name: str` — unique tool identifier
- `description: str` — human-readable description for the model
- `input_schema: dict` — JSON Schema for the tool's input
- `handler: Any` — callable that accepts `arguments: dict` and returns a result (default `None`)

---

### Class 2: `MCPResource`

A dataclass representing a readable MCP resource.

**Fields:**
- `uri: str` — resource identifier (e.g., `"file:///path/to/file"`)
- `name: str` — human-readable name
- `description: str` — what this resource contains
- `mime_type: str` — content type (default `"text/plain"`)

---

### Class 3: `MCPServer`

The server that hosts tools and resources.

#### `__init__(self, name: str)`
Initialise with an empty `_tools` dict and an empty `_resources` dict.

#### `register_tool(self, tool: MCPTool) -> None`
Add `tool` to `self._tools`, keyed by `tool.name`.

#### `register_resource(self, resource: MCPResource) -> None`
Add `resource` to `self._resources`, keyed by `resource.uri`.

#### `list_tools(self) -> list[dict]`
Return a list of dicts in MCP wire format:
```python
[{"name": t.name, "description": t.description, "inputSchema": t.input_schema}
 for t in self._tools.values()]
```

#### `list_resources(self) -> list[dict]`
Return a list of dicts:
```python
[{"uri": r.uri, "name": r.name, "description": r.description, "mimeType": r.mime_type}
 for r in self._resources.values()]
```

#### `call_tool(self, name: str, arguments: dict) -> dict`
1. Look up `name` in `self._tools`; raise `ValueError(f"Unknown tool: {name}")` if not found
2. Call `tool.handler(arguments)` and return `{"content": result, "isError": False}`
3. If the handler raises any exception, catch it and return `{"content": str(e), "isError": True}`

---

### Function: `create_filesystem_server(base_dir: str) -> MCPServer`

Factory function that builds an MCP server exposing filesystem operations.

**Step 1: Create `MCPServer("filesystem")`**

**Step 2: Create a `list_files` tool**
- Name: `"list_files"`
- Description: `"List files in the base directory"`
- Input schema: `{"type": "object", "properties": {}}`
- Handler: returns `sorted(os.listdir(base_dir))`

**Step 3: Create a `read_file` tool**
- Name: `"read_file"`
- Description: `"Read a file's contents"`
- Input schema:
  ```python
  {"type": "object", "properties": {"filename": {"type": "string"}}}
  ```
- Handler logic:
  1. Get `filename` from `args`
  2. Build the full path: `os.path.join(base_dir, filename)`
  3. Resolve to canonical form: `os.path.realpath(full_path)`
  4. **Security check**: if the resolved path does not start with `os.path.realpath(base_dir)`, raise `ValueError("Access denied: path outside base directory")`
  5. Open and read the file; return its contents as a string

**Step 4: Register both tools on the server**

**Step 5: Return the server**

---

## Files

| File | Description |
|------|-------------|
| `starter/solution.py` | Fill in the `# TODO` comments |
| `solution/solution.py` | Reference implementation |
| `tests/test_solution.py` | Automated tests (no real filesystem required — uses `tmp_path`) |

## How to Run

```bash
# Run your implementation
cd curriculum/tier-4-architect/41-mcp/lab/starter
python solution.py

# Run tests
cd curriculum/tier-4-architect/41-mcp/lab
pytest tests/ -v
```
