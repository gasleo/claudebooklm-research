"""The nlm-research command, with the MCP server replaced by a scripted backend."""

import io
import json
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest

from notebooklm_research import cli, mcp_backend

from .fakes import STARTED, ScriptedBackend, completed_chat


def use_backend(monkeypatch: pytest.MonkeyPatch, backend: ScriptedBackend) -> None:
    @asynccontextmanager
    async def fake_connect(command: str = "", args: object = ()) -> AsyncIterator[ScriptedBackend]:
        yield backend

    monkeypatch.setattr(mcp_backend, "connect", fake_connect)


DISCOVERY: list[tuple[str, dict[str, Any]]] = [
    ("research_start", {"poll_task_id": "r-1"}),
    (
        "research_status",
        {"status": "completed", "sources": [{"title": "Paper", "url": "https://x/1"}]},
    ),
]


def discovery_backend() -> ScriptedBackend:
    backend = ScriptedBackend()
    for tool, response in DISCOVERY:
        backend.on(tool, response)
    return backend


def test_query_prints_the_task_result(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    use_backend(
        monkeypatch, ScriptedBackend().on("chat_start", STARTED).on("chat_status", completed_chat())
    )

    code = cli.main(["query", "Galpon", "Why 260 °C?"])

    assert code == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == "completed"
    assert printed["sources"][0]["reference"] == "src-a"


def test_failed_query_exits_non_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    use_backend(
        monkeypatch,
        ScriptedBackend()
        .on("chat_start", STARTED)
        .on("chat_status", {"status": "failed", "error": {"code": "AUTH", "message": "login"}}),
    )

    assert cli.main(["query", "nb", "q"]) == 1


def test_discover_without_import_never_asks(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    backend = discovery_backend()
    use_backend(monkeypatch, backend)
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("must not ask"))

    assert cli.main(["discover", "nb", "pasta"]) == 0
    assert json.loads(capsys.readouterr().out)["sources"] == [
        {"title": "Paper", "url": "https://x/1"}
    ]
    assert backend.calls_to("research_import") == []


@pytest.mark.parametrize(("answer", "imports"), [("y", 1), ("", 0), ("no", 0)])
def test_discover_with_import_follows_the_answer(
    monkeypatch: pytest.MonkeyPatch, answer: str, imports: int
) -> None:
    backend = discovery_backend().on(
        "research_import", {"status": "imported", "newly_imported_count": 1}
    )
    use_backend(monkeypatch, backend)
    monkeypatch.setattr("builtins.input", lambda _: answer)

    assert cli.main(["discover", "nb", "pasta", "--import"]) == 0
    assert len(backend.calls_to("research_import")) == imports


def test_failed_discovery_exits_non_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    use_backend(
        monkeypatch,
        ScriptedBackend()
        .on("research_start", {"poll_task_id": "r-1"})
        .on("research_status", {"status": "failed", "termination_reason": "no_results"}),
    )

    assert cli.main(["discover", "nb", "q"]) == 1


def test_prints_symbols_on_a_cp1252_console(monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = io.BytesIO()
    console = io.TextIOWrapper(buffer, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", console)
    chat = completed_chat("T = (ṁ·cp·T_in + UA·T_j)/(ṁ·cp + UA), with ρ = 1300 kg/m³ [1].")
    use_backend(monkeypatch, ScriptedBackend().on("chat_start", STARTED).on("chat_status", chat))

    assert cli.main(["query", "nb", "q"]) == 0
    console.flush()
    assert "ρ = 1300" in json.loads(buffer.getvalue().decode("utf-8"))["findings"][0]
