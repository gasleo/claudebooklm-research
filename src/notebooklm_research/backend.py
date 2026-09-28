"""The port between ResearchTool and whatever serves the research operations."""

from __future__ import annotations

import re
from typing import Any, Protocol


class ResearchBackend(Protocol):
    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run one backend tool and return its JSON payload.

        Raises BackendError when the tool itself reports a failure.
        """
        ...


class BackendError(Exception):
    def __init__(self, code: str, message: str, retriable: bool) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.retriable = retriable


_ERROR_PATTERN = re.compile(
    r"\b(?P<code>[A-Z][A-Z_]{2,}): (?P<message>.*?)(?: \(retriable=(?P<retriable>\w+)\))?$",
    re.DOTALL,
)


def parse_backend_error(text: str) -> BackendError:
    """Parse notebooklm-mcp's error text, `CODE: message (retriable=true|false)`.

    The code may come after a prefix the MCP layer adds, such as
    `Error executing tool chat_start: `. Text in any other shape becomes a
    non-retriable UNKNOWN error that keeps the text.
    """
    match = _ERROR_PATTERN.search(text.strip())
    if match is None:
        return BackendError("UNKNOWN", text.strip(), retriable=False)
    retriable = (match["retriable"] or "").lower() == "true"
    return BackendError(match["code"], match["message"], retriable)
