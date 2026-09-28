"""Grounded research over NotebookLM: cited answers, candidate sources, confirmed imports."""

from .backend import BackendError, ResearchBackend
from .mcp_backend import McpBackend, connect
from .models import (
    Discovery,
    FoundSource,
    ImportOutcome,
    ImportStatus,
    Source,
    Status,
    TaskResult,
)
from .tool import ResearchTool

__all__ = [
    "BackendError",
    "Discovery",
    "FoundSource",
    "ImportOutcome",
    "ImportStatus",
    "McpBackend",
    "ResearchBackend",
    "ResearchTool",
    "Source",
    "Status",
    "TaskResult",
    "connect",
]
