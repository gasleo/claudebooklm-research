"""Contract checks against the real notebooklm-mcp server. They change nothing in NotebookLM:
one lists tools, the other asks a notebook that does not exist, which fails on lookup.

Run with `uv run pytest -m live`. Needs `notebooklm-mcp` on PATH and a logged-in session;
skipped when the command is missing.
"""

import shutil

import pytest
from mcp import Client, StdioServerParameters

from notebooklm_research import McpBackend
from notebooklm_research.backend import BackendError

pytestmark = [pytest.mark.live, pytest.mark.anyio]

# Every argument ResearchTool sends, per tool. If notebooklm-py renames one, this fails first.
ARGUMENTS_SENT = {
    "chat_start": {"notebook", "question", "conversation_id"},
    "chat_status": {"task_id"},
    "research_start": {"notebook", "query", "mode", "source"},
    "research_status": {"notebook", "poll_task_id"},
    "research_import": {"notebook", "poll_task_id", "cited_only", "max_sources"},
}


@pytest.fixture
def server_command() -> str:
    command = shutil.which("notebooklm-mcp")
    if command is None:
        pytest.skip("notebooklm-mcp is not installed")
    return command


async def test_server_accepts_every_argument_we_send(server_command: str) -> None:
    async with Client(StdioServerParameters(command=server_command)) as client:
        listed = await client.list_tools()

    schemas = {tool.name: tool.input_schema for tool in listed.tools}
    for name, sent in ARGUMENTS_SENT.items():
        assert name in schemas, f"notebooklm-mcp no longer exposes {name}"
        accepted = set(schemas[name].get("properties", {}))
        assert sent <= accepted, f"{name} does not accept {sorted(sent - accepted)}"


async def test_real_errors_parse_into_code_and_retriable(server_command: str) -> None:
    async with Client(StdioServerParameters(command=server_command)) as client:
        with pytest.raises(BackendError) as raised:
            await McpBackend(client).call(
                "chat_start",
                {"notebook": "zz-no-such-notebook-7f3a", "question": "ping"},
            )

    assert raised.value.code == "NOT_FOUND"
    assert raised.value.retriable is False
