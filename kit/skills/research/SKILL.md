---
name: research
description: Grounded research against a Google NotebookLM notebook through the notebooklm MCP. Use when a question should be answered from the project's curated sources (physics constants, domain rules, standards) or when the corpus lacks coverage and new sources must be found. Trigger: /research <question>.
---

# /research — grounded answers from a NotebookLM notebook

You are acting as the Research Agent of the architecture in `spec/`. The notebook is the corpus; you are the one who decides what to ask, how to read the answer, and what the user must approve.

## 0. Preconditions

1. Confirm the `mcp__notebooklm__*` tools are available. If not, say so and stop: do not answer from general knowledge as if it came from the corpus.
2. Call `server_info`. If `auth.authenticated` is false, tell the user to run `notebooklm login` on this machine and stop.
3. Resolve the notebook. Use the one named in the project's `CLAUDE.md`; otherwise `notebook_list` and ask the user which one applies.

## 1. Pick the operation (never both in one step)

- **corpus-query** — the question is about something the notebook's sources should already cover. Go to §2.
- **web-research** — the corpus clearly lacks the topic, or §2 answered "not in the sources". Go to §3.

## 2. corpus-query

1. `chat_start(notebook, question, references="full")` → `task_id`.
2. Wait ~20–30 s, then `chat_status(task_id)`. Repeat while `pending`. On `failed` with `retriable: true`, retry `chat_start` once.
3. On `completed`, keep `answer`, `references[]` and `conversation_id`.
4. Follow-ups on the same thread reuse `conversation_id`. Open a new conversation only for an unrelated question.

Prefer `chat_start` + `chat_status` over `chat_ask`: large notebooks take 1–3 minutes and a blocking call can time out mid-generation.

## 3. web-research

1. `research_start(notebook, query, mode="fast", source="web")` → `poll_task_id`. Use `mode="deep"` only if the user asks for depth.
2. Poll `research_status(notebook, poll_task_id)` until `completed` (or `failed`: report `termination_reason`).
3. Show the user the sources found: title, URL, and one line on why each is relevant.
4. **Stop and ask** whether to import them. `research_import` changes the user's notebook (rule R8). Offer `cited_only` or `max_sources` when the list is long. Never import as an automatic continuation.
5. After an approved import, go back to §2 and ask the question against the enriched corpus.

## 4. Report

Return a structured result, in prose for the user and in this shape when another agent consumes it:

```json
{
  "status": "completed | partial | failed",
  "findings": ["..."],
  "sources": [
    { "reference": "<source_id>", "title": "...", "citedText": "...", "citationNumber": 1 }
  ],
  "notInCorpus": ["claims the answer needed but the sources do not support"],
  "conversationId": "..."
}
```

Rules for the report:

- Every finding points to a `citation_number`. Omit fields the MCP did not return; never invent them.
- **Separate what the sources say from what you add.** Anything from general knowledge goes in `notInCorpus`, labeled as such.
- If the answer is "the sources don't say", that is a valid result. Say it plainly and offer §3.

## 5. Provenance in code

When a researched value ends up in code (a constant, a coefficient, a threshold), its docstring states where it came from:

- sourced: the source title and, if relevant, the passage — e.g. `Source: Rehydration Kinetics of Dried Spaghetti (PMC), notebook "<name>".`
- not sourced: say so explicitly — e.g. `Order-of-magnitude reference; NOT from the project notebook, which has no data on this.`

A value that looks precise but has no declared provenance is the failure this skill exists to prevent.
