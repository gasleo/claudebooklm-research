# NotebookLM — delegated research

<!-- Paste this block into your project's CLAUDE.md (or ~/.claude/CLAUDE.md for every project). Replace the notebook name. -->

The `notebooklm` MCP connects to the user's Google NotebookLM notebooks. This project's notebook is **"<NOTEBOOK NAME>"**.

## Two modes, two decisions

- **`chat`** asks the corpus that already exists. Use it when the question should be covered by the notebook's sources.
- **`research`** finds new sources on the web or in Drive. Use it when the corpus does not cover the topic. `research_import` then adds them to the notebook.

## Chat flow

`chat_start(notebook, question)` → `task_id` → poll `chat_status(task_id)` every ~20–30 s → `completed` with `answer`, `references[]` (`source_id`, `cited_text`, `citation_number`) and `conversation_id`.

Prefer `chat_start` + `chat_status` over the blocking `chat_ask`: large notebooks take 1–3 minutes. Reuse `conversation_id` for follow-ups.

## Research flow

`research_start(notebook, query, mode="fast"|"deep", source="web"|"drive")` → `poll_task_id` → poll `research_status` → `completed` with `sources[]`. Optionally `research_import(notebook, poll_task_id)`.

## Rules

- **Never import sources without asking.** `research_import` modifies the user's notebook.
- **Check the MCP is connected first.** If the tools are missing, say so and continue without them — do not present general knowledge as if it came from the notebook.
- **Cite.** When an answer comes from NotebookLM, say so and reference the relevant `citation_number`s.
- **Declare provenance in code.** A constant that came from the notebook names its source in the docstring; one that did not says so explicitly.
- **Don't send the user to NotebookLM by hand.** If the information is in a notebook, query it directly.
