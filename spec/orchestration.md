# Orchestration

## 1. Responsibility

The orchestrator drives the execution cycle from a `DecisionContext` to a final answer.

## 2. Pipeline

```text
DecisionContext
    ↓
Context Handler
    ↓
Task Planner
    ↓
Task Dispatcher
    ↓
Agent Manager
    ↓
Agents
    ↓
Result Aggregator
    ↓
Response Synthesizer
    ↓
Answer
```

## 3. Context Handler

Validates the context, normalizes data, detects missing information and prepares the context for the model. It does not produce the plan.

## 4. Task Planner

Uses the main model to produce a plan. For example:

```text
1. Check compatibility.
2. Find the official documentation.
3. Identify constraints.
4. Compare alternatives.
5. Verify results.
6. Synthesize an answer.
```

## 5. Task Dispatcher

Turns the plan into executable tasks. It resolves dependencies, priority, parallelism and the choice of agent type.

## 6. Agent Manager

- selects agents;
- creates executions;
- assigns tasks;
- controls concurrency;
- handles errors and retries;
- enforces timeouts;
- supports asynchronous tasks whose execution consists of waiting on an external tool by polling (for example, NotebookLM MCP operations).

## 7. Result Aggregator

Combines results from several agents without losing their provenance. It keeps `taskId`, agent, sources, findings, errors and confidence.

## 8. Response Synthesizer

Hands the results back to the main model to produce the final answer. The synthesis considers the `DecisionContext`, the user's decisions, the results, the sources, the uncertainties and any conflicts between results.

## 9. Parallel execution

Independent tasks can run in parallel; dependent tasks wait for their predecessors.

```text
Task A ──→ Agent A ──┐
Task B ──→ Agent B ──┼──→ Aggregator
Task C ──→ Agent C ──┘
```

## 10. Errors

One failing agent should not necessarily fail the whole run. Each result reports:

```text
status = success | partial | failed
```

The orchestrator then decides whether to retry, delegate to another agent, continue, or ask the user for information.
