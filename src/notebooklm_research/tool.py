"""ResearchTool: the layer between agents and NotebookLM (spec/notebooklm-integration.md §6)."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any, Literal

import anyio

from .backend import BackendError, ResearchBackend
from .models import (
    Discovery,
    FoundSource,
    ImportOutcome,
    ImportStatus,
    Source,
    Status,
    TaskResult,
)

ConfirmImport = Callable[[Discovery], Awaitable[bool]]
Sleep = Callable[[float], Awaitable[None]]
Clock = Callable[[], float]

_RESEARCH_RUNNING = {"in_progress", "no_research"}


class ResearchTool:
    """Two research operations and one guarded corpus change.

    - `query` asks the existing corpus (`chat_*`) and returns cited findings.
    - `discover` searches for new sources (`research_*`) and returns candidates only.
    - `import_sources` adds candidates to the notebook, and only after `confirm_import`
      returns True (rule R8). There is no way to build a ResearchTool without it.

    Backend failures come back as FAILED results, not exceptions, so one failed task
    does not bring down the caller's whole run (spec/orchestration.md §10).
    """

    def __init__(
        self,
        backend: ResearchBackend,
        *,
        confirm_import: ConfirmImport,
        poll_interval: float = 20.0,
        timeout: float = 300.0,
        sleep: Sleep = anyio.sleep,
        clock: Clock = time.monotonic,
    ) -> None:
        if poll_interval <= 0 or timeout <= 0:
            raise ValueError("poll_interval and timeout must be positive")
        self._backend = backend
        self._confirm_import = confirm_import
        self._poll_interval = poll_interval
        self._timeout = timeout
        self._sleep = sleep
        self._clock = clock

    async def query(
        self, question: str, notebook: str, conversation_id: str | None = None
    ) -> TaskResult:
        """Ask the notebook's existing sources.

        Reusing `conversation_id` keeps a follow-up in the same thread. A failure the
        backend marks as retriable is retried once, as notebooklm-mcp recommends.
        """
        arguments: dict[str, Any] = {"notebook": notebook, "question": question}
        if conversation_id is not None:
            arguments["conversation_id"] = conversation_id

        task_id = ""
        for attempt in range(2):
            try:
                started = await self._backend.call("chat_start", arguments)
                task_id = str(started["task_id"])
                payload = await self._poll_chat(task_id)
            except BackendError as error:
                if error.retriable and attempt == 0:
                    continue
                return _failed(task_id, f"{error.code}: {error.message}")
            except TimeoutError:
                return _failed(task_id, f"TIMEOUT: no answer after {self._timeout:g} s")

            if payload["status"] == "completed":
                return _task_result_from_chat(task_id, payload)
            failure = _error_of(payload)
            if failure.retriable and attempt == 0:
                continue
            return _failed(task_id, f"{failure.code}: {failure.message}")
        raise AssertionError("unreachable: the loop always returns")  # pragma: no cover

    async def discover(
        self,
        query: str,
        notebook: str,
        mode: Literal["fast", "deep"] = "fast",
        source: Literal["web", "drive"] = "web",
    ) -> Discovery:
        """Search for new sources. The result is a list of candidates; nothing is imported."""
        if mode == "deep" and source != "web":
            raise ValueError("deep research only searches the web")
        try:
            started = await self._backend.call(
                "research_start",
                {"notebook": notebook, "query": query, "mode": mode, "source": source},
            )
            poll_task_id = str(started["poll_task_id"])
            payload = await self._poll_research(notebook, poll_task_id)
        except BackendError as error:
            return Discovery(notebook, query, Status.FAILED, errors=(str(error),))
        except TimeoutError:
            return Discovery(
                notebook,
                query,
                Status.FAILED,
                errors=(f"TIMEOUT: research not finished after {self._timeout:g} s",),
            )

        if payload.get("status") != "completed":
            reason = payload.get("termination_reason") or payload.get("status")
            return Discovery(
                notebook, query, Status.FAILED, poll_task_id, errors=(f"research {reason}",)
            )
        found = tuple(
            FoundSource(str(s["title"]), str(s["url"]), s.get("hint") or None)
            for s in payload.get("sources") or []
            if s.get("url")
        )
        return Discovery(notebook, query, Status.COMPLETED, poll_task_id, found)

    async def import_sources(
        self,
        discovery: Discovery,
        *,
        cited_only: bool = False,
        max_sources: int | None = None,
    ) -> ImportOutcome:
        """Add a discovery's sources to the notebook, if and only if the user confirms."""
        if discovery.status is not Status.COMPLETED or discovery.poll_task_id is None:
            raise ValueError("only a completed discovery can be imported")
        if max_sources is not None and max_sources < 1:
            raise ValueError("max_sources must be at least 1")
        if not await self._confirm_import(discovery):
            return ImportOutcome(ImportStatus.DECLINED)

        arguments: dict[str, Any] = {
            "notebook": discovery.notebook,
            "poll_task_id": discovery.poll_task_id,
            "cited_only": cited_only,
        }
        if max_sources is not None:
            arguments["max_sources"] = max_sources
        try:
            payload = await self._backend.call("research_import", arguments)
        except BackendError as error:
            return ImportOutcome(ImportStatus.FAILED, errors=(str(error),))
        return ImportOutcome(
            ImportStatus(payload["status"]),
            imported_count=int(payload.get("newly_imported_count", 0)),
            already_present_count=int(payload.get("already_present_count", 0)),
        )

    async def _poll_chat(self, task_id: str) -> dict[str, Any]:
        deadline = self._clock() + self._timeout
        while True:
            payload = await self._backend.call("chat_status", {"task_id": task_id})
            if payload.get("status") != "pending":
                return payload
            await self._wait_or_timeout(deadline)

    async def _poll_research(self, notebook: str, poll_task_id: str) -> dict[str, Any]:
        deadline = self._clock() + self._timeout
        while True:
            payload = await self._backend.call(
                "research_status", {"notebook": notebook, "poll_task_id": poll_task_id}
            )
            if payload.get("status") not in _RESEARCH_RUNNING:
                return payload
            await self._wait_or_timeout(deadline)

    async def _wait_or_timeout(self, deadline: float) -> None:
        if self._clock() + self._poll_interval > deadline:
            raise TimeoutError
        await self._sleep(self._poll_interval)


def _task_result_from_chat(task_id: str, payload: dict[str, Any]) -> TaskResult:
    sources: list[Source] = []
    errors: list[str] = []
    for ref in payload.get("references") or []:
        source_id = ref.get("source_id")
        if not source_id:
            errors.append("dropped a reference without source_id")
            continue
        number = ref.get("citation_number")
        sources.append(
            Source(
                reference=str(source_id),
                cited_text=ref.get("cited_text") or None,
                citation_number=int(number) if number is not None else None,
            )
        )

    answer = str(payload.get("answer") or "").strip()
    if not answer:
        return TaskResult(task_id, Status.FAILED, errors=("empty answer", *errors))
    status = Status.COMPLETED
    if not sources:
        status = Status.PARTIAL
        errors.append("answer has no citations: it cannot be traced to the corpus")
    return TaskResult(
        task_id,
        status,
        findings=(answer,),
        sources=tuple(sources),
        errors=tuple(errors),
        conversation_id=payload.get("conversation_id"),
    )


def _error_of(payload: dict[str, Any]) -> BackendError:
    error = payload.get("error") or {}
    status = str(payload.get("status", "unknown"))
    # An expired task comes back as "unknown"; the server says to start it again.
    retriable = status == "unknown" or (
        bool(error.get("retriable", False)) and not error.get("unconfirmed", False)
    )
    return BackendError(
        str(error.get("code") or status.upper()),
        str(error.get("message") or f"chat task ended as {status}"),
        retriable,
    )


def _failed(task_id: str, message: str) -> TaskResult:
    return TaskResult(task_id, Status.FAILED, errors=(message,))
