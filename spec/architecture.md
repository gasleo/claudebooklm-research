# Architecture

## 1. Goal

The system takes a problem stated by the user, structures it, plans a strategy to solve it, delegates tasks to specialized agents, uses research tools, and finally synthesizes the results.

## 2. Core principle

The architecture separates three questions:

| Layer | Question |
|---|---|
| Decision chat | What problem are we solving? |
| Main model | How should we solve it? |
| Orchestrator | Who runs each task, and when? |

Subagents execute the delegated tasks.

## 3. Components

### User

States goals, provides information, answers questions and makes decisions.

### Decision chat

Turns free-form conversation into a `DecisionContext`. It must not try to solve the whole problem. Its job ends when there is enough information to start planning.

### DecisionContext

A structured representation of the problem: objective, context, requirements, constraints, decisions, assumptions and unknowns. See [decision-context.md](decision-context.md).

### Orchestrator

Coordinates the full cycle:

1. receives the context;
2. asks the main model for a plan;
3. turns the plan into tasks;
4. delegates tasks;
5. supervises agents;
6. collects results;
7. asks for a synthesis;
8. delivers the answer.

### Main model

The reasoning component. It interprets the `DecisionContext`, produces the plan, decides what information it needs, analyzes results and synthesizes the answer. It does not call tools directly.

### Subagents

Execute concrete, bounded tasks. Examples: Research Agent, Analysis Agent, Verification Agent.

### NotebookLM MCP

External tool/infrastructure. Agents use it to reach notebooks and do research. **NotebookLM MCP is not a subagent: it provides capabilities to agents.**

## 4. Flow

```text
User
  ↓
Decision chat
  ↓
DecisionContext
  ↓
Orchestrator  ⇄  Main model
  ↓
Plan → Tasks
  ↓
Subagents
  ↓
ResearchTool → NotebookLM MCP
  ↓
Results → Result Aggregator
  ↓
Main model (synthesis)
  ↓
Answer
```

## 5. Architectural rules

**R1 — The decision chat does not solve.** Its job is to define the problem.

**R2 — The orchestrator does not research.** It coordinates agents and tools.

**R3 — The main model does not call tools.** It plans and analyzes; execution belongs to the orchestrator and the agents.

**R4 — Agents receive explicit tasks.** Every task defines an objective, a description, constraints and an expected output.

**R5 — Results are structured.** Every execution produces a `TaskResult`.

**R6 — User decisions are preserved.** An explicit user decision is never silently changed.

**R7 — Sources are traceable.** Research results must be linkable to the task and the source that produced them.

**R8 — Changing the corpus requires user confirmation.** Operations that alter the research corpus — for example, importing new sources into a notebook — never run automatically as the continuation of a search. The orchestrator must ask the user for explicit confirmation first.

## 6. Diagrams

- Overview: [diagrams/architecture.mmd](diagrams/architecture.mmd)
- Orchestrator components: [diagrams/orchestrator.mmd](diagrams/orchestrator.mmd)
- Timeline: [diagrams/sequence.mmd](diagrams/sequence.mmd)
- Domain model: [diagrams/domain-model.mmd](diagrams/domain-model.mmd)
- Full architecture: [diagrams/full-architecture.mmd](diagrams/full-architecture.mmd)
