"""Test doubles: a scripted backend and a virtual clock, so polling never really sleeps."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from notebooklm_research import Discovery, ResearchTool
from notebooklm_research.backend import BackendError

Response = dict[str, Any] | BackendError


class ScriptedBackend:
    """Answers each tool with the next scripted response and records every call."""

    def __init__(self) -> None:
        self._script: dict[str, deque[Response]] = defaultdict(deque)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def on(self, tool: str, *responses: Response) -> ScriptedBackend:
        self._script[tool].extend(responses)
        return self

    def calls_to(self, tool: str) -> list[dict[str, Any]]:
        return [args for name, args in self.calls if name == tool]

    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((tool, arguments))
        if not self._script[tool]:
            raise AssertionError(f"unexpected call to {tool} with {arguments}")
        response = self._script[tool].popleft()
        if isinstance(response, BackendError):
            raise response
        return response


class VirtualClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class Approver:
    """Stands in for the human who confirms or declines an import."""

    def __init__(self, answer: bool) -> None:
        self.answer = answer
        self.asked: list[Discovery] = []

    async def __call__(self, discovery: Discovery) -> bool:
        self.asked.append(discovery)
        return self.answer


def make_tool(
    backend: ScriptedBackend,
    clock: VirtualClock | None = None,
    approver: Approver | None = None,
    timeout: float = 120.0,
) -> ResearchTool:
    clock = clock or VirtualClock()
    return ResearchTool(
        backend,
        confirm_import=approver or Approver(False),
        poll_interval=20.0,
        timeout=timeout,
        sleep=clock.sleep,
        clock=clock,
    )


def completed_chat(
    answer: str = "Water boils at 100 °C at sea level [1].",
    references: list[dict[str, Any]] | None = None,
    conversation_id: str = "conv-1",
) -> dict[str, Any]:
    if references is None:
        references = [{"source_id": "src-a", "citation_number": 1, "cited_text": "boils at 100 °C"}]
    return {
        "status": "completed",
        "task_id": "t-1",
        "answer": answer,
        "references": references,
        "conversation_id": conversation_id,
    }


PENDING = {"status": "pending", "task_id": "t-1", "state": "generating"}
STARTED = {"status": "started", "task_id": "t-1"}
