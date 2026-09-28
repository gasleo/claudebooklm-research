"""corpus-query: cited answers from the existing notebook (spec R7, orchestration §6 and §10)."""

from typing import Any

import pytest

from notebooklm_research import ResearchTool, Source, Status
from notebooklm_research.backend import BackendError

from .fakes import (
    PENDING,
    STARTED,
    Approver,
    ScriptedBackend,
    VirtualClock,
    completed_chat,
    make_tool,
)

pytestmark = pytest.mark.anyio


async def test_polls_until_completed_and_maps_citations() -> None:
    clock = VirtualClock()
    backend = (
        ScriptedBackend()
        .on("chat_start", STARTED)
        .on("chat_status", PENDING, PENDING, completed_chat())
    )

    result = await make_tool(backend, clock).query("At what temperature does water boil?", "Galpon")

    assert result.status is Status.COMPLETED
    assert result.findings == ("Water boils at 100 °C at sea level [1].",)
    assert result.sources == (
        Source(reference="src-a", cited_text="boils at 100 °C", citation_number=1),
    )
    assert result.conversation_id == "conv-1"
    assert clock.sleeps == [20.0, 20.0]
    assert backend.calls_to("chat_start") == [
        {"notebook": "Galpon", "question": "At what temperature does water boil?"}
    ]


async def test_follow_up_reuses_the_conversation() -> None:
    backend = ScriptedBackend().on("chat_start", STARTED).on("chat_status", completed_chat())

    await make_tool(backend).query("And at altitude?", "Galpon", conversation_id="conv-1")

    assert backend.calls_to("chat_start")[0]["conversation_id"] == "conv-1"


async def test_missing_citation_fields_are_omitted_not_invented() -> None:
    backend = (
        ScriptedBackend()
        .on("chat_start", STARTED)
        .on("chat_status", completed_chat(references=[{"source_id": "src-b"}]))
    )

    result = await make_tool(backend).query("q", "nb")

    assert result.sources == (Source(reference="src-b"),)
    assert result.to_dict()["sources"] == [{"reference": "src-b"}]


async def test_reference_without_source_id_is_dropped_and_reported() -> None:
    references: list[dict[str, Any]] = [
        {"citation_number": 1, "cited_text": "orphan"},
        {"source_id": "src-a"},
    ]
    backend = (
        ScriptedBackend()
        .on("chat_start", STARTED)
        .on("chat_status", completed_chat(references=references))
    )

    result = await make_tool(backend).query("q", "nb")

    assert [s.reference for s in result.sources] == ["src-a"]
    assert result.errors == ("dropped a reference without source_id",)


async def test_uncited_answer_is_partial() -> None:
    backend = (
        ScriptedBackend()
        .on("chat_start", STARTED)
        .on("chat_status", completed_chat("The sources don't cover stoves.", references=[]))
    )

    result = await make_tool(backend).query("Stove efficiency?", "nb")

    assert result.status is Status.PARTIAL
    assert result.findings == ("The sources don't cover stoves.",)
    assert "cannot be traced" in result.errors[0]


async def test_empty_answer_fails() -> None:
    backend = ScriptedBackend().on("chat_start", STARTED).on("chat_status", completed_chat("  "))

    result = await make_tool(backend).query("q", "nb")

    assert result.status is Status.FAILED
    assert result.findings == ()


async def test_retriable_generation_failure_is_retried_once() -> None:
    failed = {
        "status": "failed",
        "task_id": "t-1",
        "error": {"code": "RATE_LIMITED", "message": "slow down", "retriable": True},
    }
    backend = (
        ScriptedBackend()
        .on("chat_start", STARTED, STARTED)
        .on("chat_status", failed, completed_chat())
    )

    result = await make_tool(backend).query("q", "nb")

    assert result.status is Status.COMPLETED
    assert len(backend.calls_to("chat_start")) == 2


async def test_second_retriable_failure_gives_up() -> None:
    failed = {
        "status": "failed",
        "task_id": "t-1",
        "error": {"code": "SERVER", "message": "boom", "retriable": True},
    }
    backend = ScriptedBackend().on("chat_start", STARTED, STARTED).on("chat_status", failed, failed)

    result = await make_tool(backend).query("q", "nb")

    assert result.status is Status.FAILED
    assert result.errors == ("SERVER: boom",)


async def test_unconfirmed_failure_is_not_retried() -> None:
    failed = {
        "status": "failed",
        "task_id": "t-1",
        "error": {"code": "TIMEOUT", "message": "?", "retriable": True, "unconfirmed": True},
    }
    backend = ScriptedBackend().on("chat_start", STARTED).on("chat_status", failed)

    result = await make_tool(backend).query("q", "nb")

    assert result.status is Status.FAILED
    assert len(backend.calls_to("chat_start")) == 1


async def test_expired_task_is_started_again() -> None:
    backend = (
        ScriptedBackend()
        .on("chat_start", STARTED, STARTED)
        .on("chat_status", {"status": "unknown", "task_id": "t-1"}, completed_chat())
    )

    result = await make_tool(backend).query("q", "nb")

    assert result.status is Status.COMPLETED


async def test_non_retriable_backend_error_fails_without_retry() -> None:
    backend = ScriptedBackend().on(
        "chat_start", BackendError("NOT_FOUND", "no notebook 'x'", retriable=False)
    )

    result = await make_tool(backend).query("q", "x")

    assert result.status is Status.FAILED
    assert result.errors == ("NOT_FOUND: no notebook 'x'",)
    assert len(backend.calls) == 1


async def test_retriable_backend_error_on_start_is_retried() -> None:
    backend = (
        ScriptedBackend()
        .on("chat_start", BackendError("NETWORK", "reset", retriable=True), STARTED)
        .on("chat_status", completed_chat())
    )

    result = await make_tool(backend).query("q", "nb")

    assert result.status is Status.COMPLETED


async def test_times_out_instead_of_polling_forever() -> None:
    clock = VirtualClock()
    backend = ScriptedBackend().on("chat_start", STARTED).on("chat_status", *[PENDING] * 10)

    result = await make_tool(backend, clock, timeout=60.0).query("q", "nb")

    assert result.status is Status.FAILED
    assert result.errors[0].startswith("TIMEOUT")
    assert clock.now <= 60.0


@pytest.mark.parametrize(("interval", "timeout"), [(0, 10), (10, 0), (-1, 10)])
def test_rejects_non_positive_timing(interval: float, timeout: float) -> None:
    with pytest.raises(ValueError, match="positive"):
        ResearchTool(
            ScriptedBackend(),
            confirm_import=Approver(True),
            poll_interval=interval,
            timeout=timeout,
        )


async def test_to_dict_matches_the_spec_shape() -> None:
    backend = ScriptedBackend().on("chat_start", STARTED).on("chat_status", completed_chat())

    result = await make_tool(backend).query("q", "nb")

    assert result.to_dict() == {
        "taskId": "t-1",
        "status": "completed",
        "findings": ["Water boils at 100 °C at sea level [1]."],
        "sources": [{"reference": "src-a", "citedText": "boils at 100 °C", "citationNumber": 1}],
        "errors": [],
        "conversationId": "conv-1",
    }
