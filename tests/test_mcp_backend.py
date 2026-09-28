"""McpBackend over the real MCP protocol, against an in-memory server shaped like notebooklm-mcp."""

from typing import Any

import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, TextContent

from notebooklm_research import McpBackend, ResearchTool, Status
from notebooklm_research.backend import BackendError, parse_backend_error

from .fakes import Approver, VirtualClock

pytestmark = pytest.mark.anyio


def notebooklm_like_server() -> MCPServer:
    server = MCPServer("fake-notebooklm")
    polls = {"t-1": 0}

    @server.tool()
    def chat_start(
        notebook: str, question: str, conversation_id: str | None = None
    ) -> dict[str, Any]:
        if notebook == "missing":
            raise ToolError("NOT_FOUND: no notebook named 'missing' (retriable=false)")
        return {"status": "started", "task_id": "t-1"}

    @server.tool()
    def chat_status(task_id: str) -> dict[str, Any]:
        polls[task_id] += 1
        if polls[task_id] < 2:
            return {"status": "pending", "task_id": task_id, "state": "generating"}
        return {
            "status": "completed",
            "task_id": task_id,
            "answer": "The latent heat is 31 % of the energy to remove [1].",
            "conversation_id": "conv-9",
            "references": [{"source_id": "src-pet", "citation_number": 1, "cited_text": "31 %"}],
        }

    return server


async def test_query_round_trip_over_mcp() -> None:
    clock = VirtualClock()
    async with Client(notebooklm_like_server()) as client:
        tool = ResearchTool(
            McpBackend(client),
            confirm_import=Approver(False),
            sleep=clock.sleep,
            clock=clock,
        )
        result = await tool.query("How much energy goes into the phase change?", "Galpon")

    assert result.status is Status.COMPLETED
    assert result.sources[0].reference == "src-pet"
    assert result.sources[0].citation_number == 1
    assert result.conversation_id == "conv-9"


async def test_tool_error_becomes_a_failed_result() -> None:
    async with Client(notebooklm_like_server()) as client:
        tool = ResearchTool(McpBackend(client), confirm_import=Approver(False))
        result = await tool.query("q", "missing")

    assert result.status is Status.FAILED
    assert result.errors[0].startswith("NOT_FOUND")


class CannedCaller:
    def __init__(self, result: CallToolResult) -> None:
        self.result = result

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> CallToolResult:
        return self.result


def text_result(text: str, is_error: bool = False) -> CallToolResult:
    return CallToolResult(content=[TextContent(type="text", text=text)], is_error=is_error)


async def test_falls_back_to_json_text_without_structured_content() -> None:
    backend = McpBackend(CannedCaller(text_result('{"status": "started", "task_id": "t-7"}')))

    assert await backend.call("chat_start", {}) == {"status": "started", "task_id": "t-7"}


async def test_unwraps_result_envelope() -> None:
    wrapped = CallToolResult(content=[], structured_content={"result": {"status": "idle"}})

    assert await McpBackend(CannedCaller(wrapped)).call("chat_status", {}) == {"status": "idle"}


async def test_rejects_non_json_text() -> None:
    with pytest.raises(BackendError, match="PROTOCOL"):
        await McpBackend(CannedCaller(text_result("not json"))).call("chat_start", {})


async def test_rejects_non_object_payload() -> None:
    with pytest.raises(BackendError, match="list"):
        await McpBackend(CannedCaller(text_result("[1, 2]"))).call("chat_start", {})


async def test_error_result_raises_backend_error() -> None:
    caller = CannedCaller(text_result("RATE_LIMITED: slow down (retriable=true)", is_error=True))

    with pytest.raises(BackendError) as raised:
        await McpBackend(caller).call("chat_start", {})
    assert (raised.value.code, raised.value.retriable) == ("RATE_LIMITED", True)


@pytest.mark.parametrize(
    ("text", "code", "message", "retriable"),
    [
        ("AUTH: session expired (retriable=false)", "AUTH", "session expired", False),
        ("NETWORK: reset by peer (retriable=True)", "NETWORK", "reset by peer", True),
        ("VALIDATION: bad mode", "VALIDATION", "bad mode", False),
        (
            "Error executing tool chat_start: NOT_FOUND: no notebook (retriable=false)",
            "NOT_FOUND",
            "no notebook",
            False,
        ),
        ("something unexpected", "UNKNOWN", "something unexpected", False),
    ],
)
def test_parse_backend_error(text: str, code: str, message: str, retriable: bool) -> None:
    error = parse_backend_error(text)

    assert (error.code, error.message, error.retriable) == (code, message, retriable)
