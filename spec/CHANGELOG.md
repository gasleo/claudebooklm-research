# Changelog

Notable changes to the spec. Informal semantic versioning: major when a contract changes, minor when rules or components are added, patch for wording.

## 0.2 — 2026-09-21

- `notebooklm-integration.md` rewritten. It separates `chat` (existing corpus) from `research` (new sources), describes the asynchronous polling cycle and `conversation_id`, and maps citations.
- `agents.md`: the Research Agent declares separate capabilities `corpus-query`, `web-research` and `source-analysis`. New `operation` field in its input.
- `tasks.md`: `sources[]` gains optional `citedText` and `citationNumber`.
- `architecture.md`: new rule R8 — changing the corpus (for example, importing sources) requires explicit user confirmation.
- `orchestration.md`: the Agent Manager must support asynchronous tasks with polling.
- Diagrams `architecture.mmd`, `full-architecture.mmd`, `sequence.mmd`: new `ResearchTool` layer between agents and NotebookLM MCP; the sequence diagram shows the polling.
- New `glossary.md`.

## 0.1 — initial version

First version: architecture, decision-context, orchestration, agents, tasks, notebooklm-integration and five Mermaid diagrams.
