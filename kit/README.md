# Kit: NotebookLM research for Claude Code

Two pieces that make Claude Code use a NotebookLM notebook the way the [spec](../spec/architecture.md) describes: a `CLAUDE.md` block with the always-on rules, and a `/research` skill with the full procedure.

## 1. Install the MCP server

The server is [notebooklm-py](https://github.com/teng-lin/notebooklm-py) (MIT, by Teng Lin). This repository does not include or modify it.

```bash
uv tool install "notebooklm-py[mcp,browser,cookies]"
```

```bash
notebooklm login
```

```bash
claude mcp add --scope user notebooklm -- notebooklm-mcp
```

Check it from Claude Code by asking it to call `server_info`: `auth.authenticated` must be `true`.

> notebooklm-py drives NotebookLM through its web session, not an official API. Expect breakage when Google changes the product, and read its README for the current auth options.

## 2. Add the rules

Copy [CLAUDE.md](CLAUDE.md) into your project's `CLAUDE.md` and replace `<NOTEBOOK NAME>`. For every project, put it in `~/.claude/CLAUDE.md` instead and name the notebook per project.

## 3. Add the skill

From your project's root, with this repository cloned next to it:

```bash
mkdir -p .claude/skills && cp -r ../claude-notebooklm-research/kit/skills/research .claude/skills/
```

Use `~/.claude/skills/` instead to make it available in every project. Then, inside Claude Code:

```text
/research why does the reactor settle at 260 °C instead of the setpoint?
```

## What the pieces enforce

| Rule | Where | Spec |
|---|---|---|
| Pick `chat` or `research`, never both in one step | skill §1 | agents.md §2 |
| Async start + poll instead of blocking calls | CLAUDE.md, skill §2–3 | orchestration.md §6 |
| Every finding carries its `citation_number` | skill §4 | R7 |
| Separate "the sources say" from "I add" | skill §4 | tasks.md §5 |
| Ask before `research_import` | CLAUDE.md, skill §3.4 | R8 |
| Provenance written into code docstrings | skill §5 | R7 |
