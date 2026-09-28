"""Command line: `nlm-research query|discover` against the local notebooklm-mcp server."""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections.abc import Sequence

import anyio

from . import mcp_backend
from .models import Discovery, Status
from .tool import ResearchTool


async def _ask_on_terminal(discovery: Discovery) -> bool:
    print(f"\n{len(discovery.sources)} sources found for: {discovery.query}", file=sys.stderr)
    for source in discovery.sources:
        print(f"  - {source.title}\n    {source.url}", file=sys.stderr)
    answer = input(f"Import them into '{discovery.notebook}'? [y/N] ")
    return answer.strip().lower() in {"y", "yes", "s", "si", "sí"}


async def _run(args: argparse.Namespace) -> int:
    async with mcp_backend.connect(args.server) as backend:
        tool = ResearchTool(
            backend, confirm_import=_ask_on_terminal, poll_interval=args.poll_interval
        )
        if args.command == "query":
            result = await tool.query(args.question, args.notebook, args.conversation)
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 1 if result.status is Status.FAILED else 0

        discovery = await tool.discover(args.query, args.notebook, args.mode, args.source)
        print(json.dumps(discovery.to_dict(), ensure_ascii=False, indent=2))
        if args.import_sources and discovery.sources:
            outcome = await tool.import_sources(discovery)
            print(f"import: {outcome.status.value} ({outcome.imported_count} new)", file=sys.stderr)
        return 1 if discovery.status is Status.FAILED else 0


def main(argv: Sequence[str] | None = None) -> int:
    # Answers carry symbols such as ρ or °, which a cp1252 Windows console cannot encode.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="nlm-research", description=__doc__)
    parser.add_argument("--server", default="notebooklm-mcp", help="MCP server command")
    parser.add_argument("--poll-interval", type=float, default=10.0)
    commands = parser.add_subparsers(dest="command", required=True)

    query = commands.add_parser("query", help="ask the notebook's existing sources")
    query.add_argument("notebook")
    query.add_argument("question")
    query.add_argument("--conversation", help="conversation id of a previous answer")

    discover = commands.add_parser("discover", help="search the web or Drive for new sources")
    discover.add_argument("notebook")
    discover.add_argument("query")
    discover.add_argument("--mode", choices=["fast", "deep"], default="fast")
    discover.add_argument("--source", choices=["web", "drive"], default="web")
    discover.add_argument(
        "--import",
        dest="import_sources",
        action="store_true",
        help="offer to import the sources found (asks for confirmation)",
    )

    return anyio.run(_run, parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
