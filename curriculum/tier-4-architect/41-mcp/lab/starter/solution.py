"""Lab 41: MCP — Model Context Protocol (simplified, stdlib-only)"""
import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict
    handler: Any = field(default=None, repr=False)


@dataclass
class MCPResource:
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


class MCPServer:
    def __init__(self, name: str):
        self.name = name
        self._tools: dict[str, MCPTool] = {}
        self._resources: dict[str, MCPResource] = {}

    def register_tool(self, tool: MCPTool) -> None:
        # TODO: Add tool to self._tools dict keyed by tool.name
        pass

    def register_resource(self, resource: MCPResource) -> None:
        # TODO: Add resource to self._resources dict keyed by resource.uri
        pass

    def list_tools(self) -> list[dict]:
        # TODO: Return list of dicts with name, description, inputSchema for each tool
        # Format: [{"name": ..., "description": ..., "inputSchema": ...}, ...]
        pass

    def list_resources(self) -> list[dict]:
        # TODO: Return list of dicts with uri, name, description, mimeType for each resource
        # Format: [{"uri": ..., "name": ..., "description": ..., "mimeType": ...}, ...]
        pass

    def call_tool(self, name: str, arguments: dict) -> dict:
        # TODO: Find tool by name, raise ValueError if not found
        # TODO: Call tool.handler(arguments) and return {"content": result, "isError": False}
        # TODO: Catch exceptions, return {"content": str(e), "isError": True}
        pass


def create_filesystem_server(base_dir: str) -> MCPServer:
    """Create an MCP server that exposes filesystem operations."""
    # TODO: Create MCPServer("filesystem")

    # TODO: Create a list_files tool
    # - name: "list_files"
    # - description: "List files in the base directory"
    # - input_schema: {"type": "object", "properties": {}}
    # - handler: returns sorted(os.listdir(base_dir))

    # TODO: Create a read_file tool
    # - name: "read_file"
    # - description: "Read a file's contents"
    # - input_schema: {"type": "object", "properties": {"filename": {"type": "string"}}}
    # - handler:
    #     filename = args["filename"]
    #     full_path = os.path.realpath(os.path.join(base_dir, filename))
    #     if not full_path.startswith(os.path.realpath(base_dir)):
    #         raise ValueError("Access denied: path outside base directory")
    #     with open(full_path) as f:
    #         return f.read()

    # TODO: Register both tools on the server
    # TODO: Return the server
    pass
