"""web-research and the corpus change it may lead to (spec R8: import only with confirmation)."""

import pytest

from notebooklm_research import Discovery, FoundSource, ImportStatus, Status
from notebooklm_research.backend import BackendError

from .fakes import Approver, ScriptedBackend, VirtualClock, make_tool

pytestmark = pytest.mark.anyio

RUNNING = {"status": "in_progress", "sources": []}
DONE = {
    "status": "completed",
    "termination_reason": "completed",
    "sources": [
        {"title": "Rehydration kinetics of spaghetti", "url": "https://pmc/1", "hint": "Fick"},
        {"title": "Cooking quality of spaghetti", "url": "https://journal/2", "hint": ""},
        {"title": "Report row without url", "url": ""},
    ],
}
IMPORTED = {
    "status": "imported",
    "newly_imported_count": 2,
    "already_present_count": 0,
}


def discovery_backend() -> ScriptedBackend:
    return (
        ScriptedBackend()
        .on("research_start", {"poll_task_id": "r-1"})
        .on("research_status", RUNNING, DONE)
    )


async def test_discover_returns_candidates_and_imports_nothing() -> None:
    backend = discovery_backend()

    discovery = await make_tool(backend).discover("pasta water uptake", "Galpon")

    assert discovery.status is Status.COMPLETED
    assert discovery.poll_task_id == "r-1"
    assert discovery.sources == (
        FoundSource("Rehydration kinetics of spaghetti", "https://pmc/1", "Fick"),
        FoundSource("Cooking quality of spaghetti", "https://journal/2"),
    )
    assert backend.calls_to("research_import") == []
    assert backend.calls_to("research_start") == [
        {"notebook": "Galpon", "query": "pasta water uptake", "mode": "fast", "source": "web"}
    ]


async def test_deep_research_is_web_only() -> None:
    with pytest.raises(ValueError, match="web"):
        await make_tool(ScriptedBackend()).discover("q", "nb", mode="deep", source="drive")


async def test_failed_research_reports_the_termination_reason() -> None:
    backend = (
        ScriptedBackend()
        .on("research_start", {"poll_task_id": "r-1"})
        .on("research_status", {"status": "failed", "termination_reason": "no_results"})
    )

    discovery = await make_tool(backend).discover("q", "nb")

    assert discovery.status is Status.FAILED
    assert discovery.errors == ("research no_results",)


async def test_backend_error_during_discovery_fails_the_discovery() -> None:
    backend = ScriptedBackend().on("research_start", BackendError("AUTH", "log in", False))

    discovery = await make_tool(backend).discover("q", "nb")

    assert discovery.status is Status.FAILED
    assert discovery.errors == ("AUTH: log in",)


async def test_discovery_times_out() -> None:
    clock = VirtualClock()
    backend = (
        ScriptedBackend()
        .on("research_start", {"poll_task_id": "r-1"})
        .on("research_status", *[RUNNING] * 10)
    )

    discovery = await make_tool(backend, clock, timeout=60.0).discover("q", "nb")

    assert discovery.status is Status.FAILED
    assert discovery.errors[0].startswith("TIMEOUT")


async def test_import_asks_the_user_first_and_stops_when_declined() -> None:
    backend = discovery_backend()
    approver = Approver(False)
    tool = make_tool(backend, approver=approver)
    discovery = await tool.discover("q", "Galpon")

    outcome = await tool.import_sources(discovery)

    assert outcome.status is ImportStatus.DECLINED
    assert approver.asked == [discovery]
    assert backend.calls_to("research_import") == []


async def test_import_runs_after_approval() -> None:
    backend = discovery_backend().on("research_import", IMPORTED)
    approver = Approver(True)
    tool = make_tool(backend, approver=approver)
    discovery = await tool.discover("q", "Galpon")

    outcome = await tool.import_sources(discovery, cited_only=True, max_sources=5)

    assert outcome.status is ImportStatus.IMPORTED
    assert outcome.imported_count == 2
    assert backend.calls_to("research_import") == [
        {"notebook": "Galpon", "poll_task_id": "r-1", "cited_only": True, "max_sources": 5}
    ]


async def test_repeat_import_reports_already_imported() -> None:
    again = {"status": "already_imported", "newly_imported_count": 0, "already_present_count": 2}
    backend = discovery_backend().on("research_import", again)
    tool = make_tool(backend, approver=Approver(True))

    outcome = await tool.import_sources(await tool.discover("q", "nb"))

    assert outcome.status is ImportStatus.ALREADY_IMPORTED
    assert outcome.already_present_count == 2


async def test_import_failure_is_reported() -> None:
    backend = discovery_backend().on("research_import", BackendError("SERVER", "down", True))
    tool = make_tool(backend, approver=Approver(True))

    outcome = await tool.import_sources(await tool.discover("q", "nb"))

    assert outcome.status is ImportStatus.FAILED
    assert outcome.errors == ("SERVER: down",)


async def test_a_failed_discovery_cannot_be_imported() -> None:
    approver = Approver(True)
    failed = Discovery("nb", "q", Status.FAILED, errors=("x",))

    with pytest.raises(ValueError, match="completed"):
        await make_tool(ScriptedBackend(), approver=approver).import_sources(failed)
    assert approver.asked == []


async def test_max_sources_must_be_positive() -> None:
    tool = make_tool(discovery_backend(), approver=Approver(True))
    discovery = await tool.discover("q", "nb")

    with pytest.raises(ValueError, match="max_sources"):
        await tool.import_sources(discovery, max_sources=0)
