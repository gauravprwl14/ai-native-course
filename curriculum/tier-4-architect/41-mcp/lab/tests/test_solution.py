"""Tests for Lab 41 — MCP Server"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# LAB_TARGET=solution runs tests against the reference solution
_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, str(Path(__file__).parent.parent / _lab_target))


class TestMCPTool(unittest.TestCase):
    def _make_tool(self, name="my_tool", description="A test tool", handler=None):
        from solution import MCPTool
        return MCPTool(
            name=name,
            description=description,
            input_schema={"type": "object", "properties": {}},
            handler=handler or (lambda args: "result"),
        )

    def test_tool_stores_name(self):
        from solution import MCPTool
        tool = self._make_tool(name="list_files")
        self.assertEqual(tool.name, "list_files")

    def test_tool_stores_description(self):
        from solution import MCPTool
        tool = self._make_tool(description="Lists directory contents")
        self.assertEqual(tool.description, "Lists directory contents")

    def test_tool_stores_input_schema(self):
        from solution import MCPTool
        schema = {"type": "object", "properties": {"path": {"type": "string"}}}
        tool = MCPTool(name="t", description="d", input_schema=schema)
        self.assertEqual(tool.input_schema, schema)

    def test_tool_handler_is_callable(self):
        tool = self._make_tool(handler=lambda args: "ok")
        self.assertTrue(callable(tool.handler))


class TestMCPResource(unittest.TestCase):
    def test_resource_stores_uri(self):
        from solution import MCPResource
        r = MCPResource(uri="file:///tmp/test.txt", name="test", description="a file")
        self.assertEqual(r.uri, "file:///tmp/test.txt")

    def test_resource_default_mime_type(self):
        from solution import MCPResource
        r = MCPResource(uri="file:///tmp/test.txt", name="test", description="a file")
        self.assertEqual(r.mime_type, "text/plain")

    def test_resource_custom_mime_type(self):
        from solution import MCPResource
        r = MCPResource(uri="file:///tmp/test.json", name="cfg", description="config",
                        mime_type="application/json")
        self.assertEqual(r.mime_type, "application/json")


class TestMCPServerRegistration(unittest.TestCase):
    def _make_server(self):
        from solution import MCPServer
        return MCPServer("test-server")

    def _make_tool(self, name="tool1"):
        from solution import MCPTool
        return MCPTool(name=name, description="desc", input_schema={},
                       handler=lambda args: "ok")

    def _make_resource(self, uri="file:///tmp/test.txt"):
        from solution import MCPResource
        return MCPResource(uri=uri, name="file", description="a file")

    def test_server_name(self):
        server = self._make_server()
        self.assertEqual(server.name, "test-server")

    def test_register_tool_adds_to_tools(self):
        server = self._make_server()
        tool = self._make_tool("my_tool")
        server.register_tool(tool)
        tools = server.list_tools()
        self.assertTrue(any(t["name"] == "my_tool" for t in tools))

    def test_register_multiple_tools(self):
        server = self._make_server()
        server.register_tool(self._make_tool("tool_a"))
        server.register_tool(self._make_tool("tool_b"))
        tools = server.list_tools()
        names = [t["name"] for t in tools]
        self.assertIn("tool_a", names)
        self.assertIn("tool_b", names)

    def test_register_resource_adds_to_resources(self):
        server = self._make_server()
        resource = self._make_resource("file:///tmp/readme.md")
        server.register_resource(resource)
        resources = server.list_resources()
        self.assertTrue(any(r["uri"] == "file:///tmp/readme.md" for r in resources))

    def test_list_tools_returns_list(self):
        server = self._make_server()
        self.assertIsInstance(server.list_tools(), list)

    def test_list_resources_returns_list(self):
        server = self._make_server()
        self.assertIsInstance(server.list_resources(), list)

    def test_list_tools_empty_when_no_tools(self):
        server = self._make_server()
        self.assertEqual(server.list_tools(), [])

    def test_list_resources_empty_when_no_resources(self):
        server = self._make_server()
        self.assertEqual(server.list_resources(), [])


class TestMCPServerListFormat(unittest.TestCase):
    def _make_server_with_tool(self):
        from solution import MCPServer, MCPTool
        server = MCPServer("test")
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        server.register_tool(MCPTool(
            name="my_tool",
            description="My description",
            input_schema=schema,
            handler=lambda args: "result",
        ))
        return server

    def _make_server_with_resource(self):
        from solution import MCPServer, MCPResource
        server = MCPServer("test")
        server.register_resource(MCPResource(
            uri="file:///tmp/notes.txt",
            name="Notes",
            description="My notes file",
            mime_type="text/plain",
        ))
        return server

    def test_list_tools_has_name_key(self):
        server = self._make_server_with_tool()
        tool = server.list_tools()[0]
        self.assertIn("name", tool)
        self.assertEqual(tool["name"], "my_tool")

    def test_list_tools_has_description_key(self):
        server = self._make_server_with_tool()
        tool = server.list_tools()[0]
        self.assertIn("description", tool)
        self.assertEqual(tool["description"], "My description")

    def test_list_tools_has_inputSchema_key(self):
        server = self._make_server_with_tool()
        tool = server.list_tools()[0]
        self.assertIn("inputSchema", tool)
        self.assertIsInstance(tool["inputSchema"], dict)

    def test_list_resources_has_uri_key(self):
        server = self._make_server_with_resource()
        resource = server.list_resources()[0]
        self.assertIn("uri", resource)
        self.assertEqual(resource["uri"], "file:///tmp/notes.txt")

    def test_list_resources_has_name_key(self):
        server = self._make_server_with_resource()
        resource = server.list_resources()[0]
        self.assertIn("name", resource)

    def test_list_resources_has_mimeType_key(self):
        server = self._make_server_with_resource()
        resource = server.list_resources()[0]
        self.assertIn("mimeType", resource)
        self.assertEqual(resource["mimeType"], "text/plain")


class TestMCPServerCallTool(unittest.TestCase):
    def _make_server(self):
        from solution import MCPServer, MCPTool
        server = MCPServer("test")
        server.register_tool(MCPTool(
            name="echo",
            description="Echoes the input",
            input_schema={},
            handler=lambda args: f"echo: {args.get('text', '')}",
        ))
        server.register_tool(MCPTool(
            name="fail_tool",
            description="Always raises",
            input_schema={},
            handler=lambda args: (_ for _ in ()).throw(RuntimeError("intentional error")),
        ))
        return server

    def test_call_tool_returns_dict(self):
        server = self._make_server()
        result = server.call_tool("echo", {"text": "hello"})
        self.assertIsInstance(result, dict)

    def test_call_tool_has_content_key(self):
        server = self._make_server()
        result = server.call_tool("echo", {"text": "hello"})
        self.assertIn("content", result)

    def test_call_tool_has_isError_key(self):
        server = self._make_server()
        result = server.call_tool("echo", {"text": "hello"})
        self.assertIn("isError", result)

    def test_call_tool_success_is_not_error(self):
        server = self._make_server()
        result = server.call_tool("echo", {"text": "hello"})
        self.assertFalse(result["isError"])

    def test_call_tool_content_matches_handler_return(self):
        server = self._make_server()
        result = server.call_tool("echo", {"text": "world"})
        self.assertIn("world", str(result["content"]))

    def test_call_tool_unknown_raises_value_error(self):
        server = self._make_server()
        with self.assertRaises(ValueError):
            server.call_tool("nonexistent", {})

    def test_call_tool_handler_exception_returns_error(self):
        from solution import MCPServer, MCPTool
        server = MCPServer("test")
        server.register_tool(MCPTool(
            name="bad",
            description="fails",
            input_schema={},
            handler=lambda args: (_ for _ in ()).throw(ValueError("bad input")),
        ))
        result = server.call_tool("bad", {})
        self.assertTrue(result["isError"])
        self.assertIn("bad input", result["content"])


class TestCreateFilesystemServer(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory with some test files
        self.tmp_dir = tempfile.mkdtemp()
        self.file1 = os.path.join(self.tmp_dir, "hello.txt")
        self.file2 = os.path.join(self.tmp_dir, "world.txt")
        with open(self.file1, "w") as f:
            f.write("Hello, world!")
        with open(self.file2, "w") as f:
            f.write("Second file content")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _make_server(self):
        from solution import create_filesystem_server
        return create_filesystem_server(self.tmp_dir)

    def test_returns_mcp_server(self):
        from solution import MCPServer
        server = self._make_server()
        self.assertIsInstance(server, MCPServer)

    def test_server_name_is_filesystem(self):
        server = self._make_server()
        self.assertEqual(server.name, "filesystem")

    def test_has_list_files_tool(self):
        server = self._make_server()
        names = [t["name"] for t in server.list_tools()]
        self.assertIn("list_files", names)

    def test_has_read_file_tool(self):
        server = self._make_server()
        names = [t["name"] for t in server.list_tools()]
        self.assertIn("read_file", names)

    def test_list_files_returns_sorted_list(self):
        server = self._make_server()
        result = server.call_tool("list_files", {})
        self.assertFalse(result["isError"])
        files = result["content"]
        self.assertIsInstance(files, list)
        self.assertIn("hello.txt", files)
        self.assertIn("world.txt", files)
        self.assertEqual(files, sorted(files))

    def test_read_file_returns_content(self):
        server = self._make_server()
        result = server.call_tool("read_file", {"filename": "hello.txt"})
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"], "Hello, world!")

    def test_read_file_path_traversal_blocked(self):
        server = self._make_server()
        result = server.call_tool("read_file", {"filename": "../../../etc/passwd"})
        self.assertTrue(result["isError"])
        self.assertIn("Access denied", result["content"])

    def test_read_file_nonexistent_returns_error(self):
        server = self._make_server()
        result = server.call_tool("read_file", {"filename": "does_not_exist.txt"})
        self.assertTrue(result["isError"])

    def test_list_files_two_files(self):
        server = self._make_server()
        result = server.call_tool("list_files", {})
        self.assertFalse(result["isError"])
        self.assertEqual(len(result["content"]), 2)


if __name__ == "__main__":
    unittest.main()
