"""Result types of the ResearchTool, shaped after spec/tasks.md."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Status(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class Source:
    """A citation returned by the research backend.

    Only `reference` is guaranteed. The other fields are None when the backend did not
    return them, and are left out of `to_dict()` rather than filled with guesses.
    """

    reference: str
    title: str | None = None
    cited_text: str | None = None
    citation_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        fields = {
            "reference": self.reference,
            "title": self.title,
            "citedText": self.cited_text,
            "citationNumber": self.citation_number,
        }
        return {k: v for k, v in fields.items() if v is not None}


@dataclass(frozen=True)
class TaskResult:
    """Outcome of a corpus query.

    `PARTIAL` means an answer came back without any citation, so it cannot be traced
    to the corpus. Confidence is left to the calling agent: the tool has no basis for it.
    """

    task_id: str
    status: Status
    findings: tuple[str, ...] = ()
    sources: tuple[Source, ...] = ()
    errors: tuple[str, ...] = ()
    conversation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "taskId": self.task_id,
            "status": self.status.value,
            "findings": list(self.findings),
            "sources": [s.to_dict() for s in self.sources],
            "errors": list(self.errors),
        }
        if self.conversation_id is not None:
            data["conversationId"] = self.conversation_id
        return data


@dataclass(frozen=True)
class FoundSource:
    """A candidate source from web or Drive research. Not yet part of the corpus."""

    title: str
    url: str
    hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {"title": self.title, "url": self.url}
        if self.hint:
            data["hint"] = self.hint
        return data


@dataclass(frozen=True)
class Discovery:
    """Outcome of a search for new sources. Importing it is a separate, confirmed step."""

    notebook: str
    query: str
    status: Status
    poll_task_id: str | None = None
    sources: tuple[FoundSource, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "notebook": self.notebook,
            "query": self.query,
            "status": self.status.value,
            "pollTaskId": self.poll_task_id,
            "sources": [s.to_dict() for s in self.sources],
            "errors": list(self.errors),
        }


class ImportStatus(StrEnum):
    IMPORTED = "imported"
    ALREADY_IMPORTED = "already_imported"
    DECLINED = "declined"
    FAILED = "failed"


@dataclass(frozen=True)
class ImportOutcome:
    status: ImportStatus
    imported_count: int = 0
    already_present_count: int = 0
    errors: tuple[str, ...] = ()
