# NotebookLM MCP integration

## 1. Role

NotebookLM MCP is an external research tool, not a subagent. Agents use it through a `ResearchTool` layer; the orchestration logic does not depend on MCP details beyond that contract.

## 2. Two modes of operation

NotebookLM exposes two distinct capabilities, and they correspond to two distinct agent decisions.

### 2.1 Query the existing corpus (`chat`)

The agent asks the notebook using the sources already loaded. Use it when the knowledge is already in the corpus.

```text
chat_start(notebook, question)
   → task_id
chat_status(task_id)              # poll
   → status: pending | completed
   → answer + references[] + conversation_id
```

- It is asynchronous: `chat_start` returns a `task_id` immediately and does not block.
- Every answer carries `references[]` with `source_id`, `cited_text` and `citation_number`. This is the primary traceability mechanism (R7).
- `conversation_id` chains follow-up questions in the same thread. An agent that needs to dig deeper should reuse it before opening a new conversation.
- A synchronous variant exists (`chat_ask`), but it can exceed timeouts on large notebooks. Treat it as a fallback, not the main path.

### 2.2 Find new sources (`research`)

The agent asks the MCP to search the web or Drive. Use it when the corpus does not cover the topic.

```text
research_start(notebook, query, mode, source)
   → poll_task_id
research_status(notebook, poll_task_id)
   → sources[] + summary + report
research_import(notebook, poll_task_id)   # optional
```

- `mode` = `fast` | `deep`. `source` = `web` | `drive`.
- The initial result is a set of URLs with a title and a hint, not a narrative answer.
- `research_import` adds those sources to the notebook and changes external state. See §5.

## 3. What the agent decides

- whether the topic calls for `chat` (existing corpus) or `research` (new sources);
- which question to ask;
- whether a follow-up reuses `conversation_id` or opens a new one;
- how to interpret and structure the results;
- whether the findings justify proposing an import to the orchestrator.

## 4. What the MCP does

It provides the interface to operate on the notebook. It does not decide what to ask or when to import.

## 5. Enriching the corpus

`research_import` is not a research operation: it modifies the user's corpus. The integration treats it as a decision that requires explicit user confirmation, never as an automatic step after a `research`. Rule: R8.

## 6. Recommended abstraction

```text
ResearchAgent
      ↓
ResearchTool          # stable layer, two operations: query / discover
      ↓
NotebookLM MCP        # swappable implementation
```

- `query(question, notebook, conversationId?)` — maps to `chat_*`.
- `discover(query, mode, source)` — maps to `research_*`.

Any future source (another MCP, a private index, a search engine) should be able to implement the same contract.

## 7. Results

Results returned to the orchestrator are structured and keep the MCP's citations. `TaskResult.sources[]` maps directly onto NotebookLM's fields:

| TaskResult.sources[] | NotebookLM |
|---|---|
| `reference` | `source_id` |
| `title` | source title |
| `citedText` | `cited_text` |
| `citationNumber` | `citation_number` |

If the MCP does not expose a field, the agent omits it; it never invents it.

## 8. Asynchronous tasks

Both cycles (`chat_*`, `research_*`) are asynchronous with polling, so the orchestrator must support tasks whose execution consists of waiting. See [orchestration.md](orchestration.md) §6 (Agent Manager) and §10 (errors and timeouts).
