"""ResearchBackend implementation over an MCP client (notebooklm-mcp by default)."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any, Protocol

from mcp import Client, StdioServerParameters
from mcp.types import CallToolResult, TextContent

from .backend import BackendError, parse_backend_error


class ToolCaller(Protocol):
    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult: ...


class McpBackend:
    def __init__(self, client: ToolCaller) -> None:
        self._client = client

    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = await self._client.call_tool(tool, arguments)
        text = "".join(c.text for c in result.content if isinstance(c, TextContent))
        if result.is_error:
            raise parse_backend_error(text)

        data: Any = result.structured_content
        if data is None:
            try:
                data = json.loads(text)
            except json.JSONDecodeError as error:
                raise BackendError("PROTOCOL", f"{tool} returned non-JSON text", False) from error
        # FastMCP wraps non-object return values as {"result": ...}.
        if isinstance(data, dict) and set(data) == {"result"} and isinstance(data["result"], dict):
            data = data["result"]
        if not isinstance(data, dict):
            raise BackendError("PROTOCOL", f"{tool} returned {type(data).__name__}", False)
        return data


@asynccontextmanager
async def connect(
    command: str = "notebooklm-mcp", args: Sequence[str] = ()
) -> AsyncIterator[McpBackend]:
    """Start the MCP server as a subprocess and yield a backend bound to it."""
    async with Client(StdioServerParameters(command=command, args=list(args))) as client:
        yield McpBackend(client)
