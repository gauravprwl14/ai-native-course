"""Lab 41: MCP — Model Context Protocol (simplified, stdlib-only) — Reference Solution"""
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
        self._tools[tool.name] = tool

    def register_resource(self, resource: MCPResource) -> None:
        self._resources[resource.uri] = resource

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]

    def list_resources(self) -> list[dict]:
        return [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mimeType": r.mime_type,
            }
            for r in self._resources.values()
        ]

    def call_tool(self, name: str, arguments: dict) -> dict:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = self._tools[name].handler(arguments)
            return {"content": result, "isError": False}
        except Exception as e:
            return {"content": str(e), "isError": True}


def create_filesystem_server(base_dir: str) -> MCPServer:
    """Create an MCP server that exposes filesystem operations."""
    server = MCPServer("filesystem")

    def list_files_handler(args: dict) -> list[str]:
        return sorted(os.listdir(base_dir))

    def read_file_handler(args: dict) -> str:
        filename = args["filename"]
        full_path = os.path.realpath(os.path.join(base_dir, filename))
        if not full_path.startswith(os.path.realpath(base_dir)):
            raise ValueError("Access denied: path outside base directory")
        with open(full_path) as f:
            return f.read()

    server.register_tool(MCPTool(
        name="list_files",
        description="List files in the base directory",
        input_schema={"type": "object", "properties": {}},
        handler=list_files_handler,
    ))

    server.register_tool(MCPTool(
        name="read_file",
        description="Read a file's contents",
        input_schema={
            "type": "object",
            "properties": {"filename": {"type": "string"}},
        },
        handler=read_file_handler,
    ))

    return server
