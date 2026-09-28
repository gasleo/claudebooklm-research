# DecisionContext

## 1. Purpose

`DecisionContext` is the contract between the decision chat and the orchestration system. It represents the problem as defined by the user, before any execution plan exists.

## 2. Responsibility

It answers:

- What does the user want to achieve?
- What is the context?
- What requirements exist?
- What constraints exist?
- What has already been decided?
- What assumptions are in use?
- What information is still missing?

## 3. Conceptual contract

```json
{
  "id": "context-001",
  "objective": "Decide how to implement X",
  "context": ["Relevant context for the problem"],
  "requirements": [],
  "constraints": [],
  "decisions": [],
  "assumptions": [],
  "unknowns": [],
  "createdAt": "2026-09-21T00:00:00Z",
  "updatedAt": "2026-09-21T00:00:00Z"
}
```

## 4. Entities

### Decision

```json
{
  "id": "decision-001",
  "description": "Use MCP",
  "reason": "It integrates the existing tool",
  "status": "confirmed"
}
```

Recommended states: `proposed`, `confirmed`, `rejected`, `superseded`.

### Requirement

```json
{
  "id": "req-001",
  "description": "Must work offline",
  "priority": "high",
  "status": "active"
}
```

### Constraint

```json
{
  "id": "constraint-001",
  "description": "Do not modify the existing system",
  "type": "technical"
}
```

### Assumption

```json
{
  "id": "assumption-001",
  "description": "API X is available",
  "confidence": 0.7
}
```

## 5. Unknowns

Unknowns must not be hidden.

```json
{
  "id": "unknown-001",
  "description": "The exact version of X is unknown"
}
```

The orchestrator can turn an unknown into a research task.

## 6. Completion criterion

The decision chat ends when:

- there is a clear objective;
- the relevant constraints are identified;
- the decisions that belong to the user are resolved;
- the remaining unknowns can be researched or do not block planning.

Not every unknown has to be eliminated before research starts.
