# Agents

## 1. Principle

Agents execute specific tasks. They should never receive the whole problem without a concrete task.

## 2. Research Agent

Researches a question, consults sources, extracts findings and returns evidence with its citations.

It distinguishes two operations (see [notebooklm-integration.md](notebooklm-integration.md) §2):

- **corpus-query** — ask an existing corpus. It can hold follow-ups by reusing a conversation id provided by the tool.
- **web-research** — find new sources. It returns references, not a narrative answer.

The agent picks the operation based on the task; it never combines both in one call.

```json
{
  "type": "research",
  "objective": "Check whether X is compatible with Y",
  "operation": "corpus-query",
  "expectedOutput": "Findings and sources"
}
```

## 3. Analysis Agent

Analyzes existing results, compares information, detects relationships and draws conclusions from the data it was given. It must not invent evidence.

## 4. Verification Agent

Verifies claims, cross-checks sources, detects inconsistencies and flags unconfirmed information.

## 5. Capabilities

Agents declare themselves by capability:

```json
{
  "id": "research-agent",
  "capabilities": ["corpus-query", "web-research", "source-analysis"]
}
```

The orchestrator selects agents by the capabilities a task requires.

## 6. Isolation

Each agent receives only the context it needs for its task. This reduces noise, context consumption and ambiguity, and keeps agents from changing decisions outside their responsibility.
