# Glossary

Every term used in the spec, in one place. If a term is not here, it is not part of the architecture's formal vocabulary.

## Actors and components

**User** — Originates the problem and makes decisions. See [architecture.md](architecture.md) §3.

**Decision chat** — Conversational interface that turns free-form conversation into a `DecisionContext`. It does not solve the problem.

**DecisionContext** — Structured contract representing the defined problem. See [decision-context.md](decision-context.md).

**Main model** — The reasoning component. It plans and synthesizes; it does not call tools.

**Orchestrator** — Coordinates the cycle from `DecisionContext` to final answer. See [orchestration.md](orchestration.md).

**Subagent** — Executes one concrete task, with only the context that task needs.

**ResearchTool** — Stable layer between agents and external research tools. Two operations: `query` (ask an existing corpus) and `discover` (find new sources). See [notebooklm-integration.md](notebooklm-integration.md) §6.

**NotebookLM MCP** — Concrete implementation behind `ResearchTool`. External and swappable.

## Entities

**Task** — Executable unit delegated to an agent. See [tasks.md](tasks.md).

**TaskResult** — Structured output of a task: findings, sources, confidence and errors.

**Decision / Requirement / Constraint / Assumption / Unknown** — Elements of the `DecisionContext`. See [decision-context.md](decision-context.md) §4–5.

**Reference / Source** — Citation returned by a research tool, stored in `TaskResult.sources[]`.

## Operations and states

**corpus-query** — Ask an existing corpus. Maps to `chat_*` in NotebookLM.

**web-research** — Find new sources. Maps to `research_*` in NotebookLM.

**conversation** — Thread of follow-up questions on the same corpus, identified by a tool-provided conversation id.

**status** — `Task` states: `pending`, `running`, `completed`, `partial`, `failed`, `cancelled`. See [tasks.md](tasks.md) §3.

## Rules

R1–R8 — Architectural rules. See [architecture.md](architecture.md) §5.
