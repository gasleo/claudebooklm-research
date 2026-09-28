# Tasks and results

## 1. Task

A `Task` is an executable unit of work.

```json
{
  "id": "task-001",
  "type": "research",
  "description": "Check whether X is compatible with Y",
  "priority": "high",
  "status": "pending",
  "dependencies": [],
  "input": {},
  "expectedOutput": "Sources and findings"
}
```

## 2. Task types

Initial types: `research`, `analysis`, `verification`, `synthesis`. The list can grow with the system.

## 3. Status

```text
pending
running
completed
partial
failed
cancelled
```

## 4. Dependencies

A task can depend on another (`Task A → Task B → Task C`). The dispatcher must respect dependencies.

## 5. TaskResult

```json
{
  "taskId": "task-001",
  "status": "completed",
  "findings": ["Finding 1", "Finding 2"],
  "sources": [
    {
      "reference": "source-id",
      "title": "Source",
      "citedText": "Passage cited by the tool",
      "citationNumber": 1
    }
  ],
  "confidence": 0.9,
  "errors": []
}
```

`sources[]` abstracts over whatever the research tool returns. Fields such as `citedText` and `citationNumber` may be absent when the source does not expose them; the agent omits them instead of fabricating them. The NotebookLM mapping is in [notebooklm-integration.md](notebooklm-integration.md) §7.

## 6. Traceability

Every result must be linkable along this chain, so that anyone can reconstruct how a conclusion was reached:

```text
Task → Agent → Tool → Source
```
