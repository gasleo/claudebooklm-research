# Case study: Galpón, a process-plant simulator

Galpón is a university project (Supervised Professional Practice, UNGS, 2026): a process-plant simulator where you install equipment, connect it with pipes and watch mass and heat move through it. It started as a web prototype (TypeScript + three.js) and is being ported to Godot. The repository belongs to the team and is private; this page summarizes how the NotebookLM + Claude Code workflow was used in it, with short excerpts.

The constraint that made the workflow necessary: **the simulator has to be physically defensible before a panel**, and the team are software developers, not process engineers. A constant that looks precise but has no source is exactly what a panel asks about.

## How the pieces map onto the spec

| Spec component | In practice |
|---|---|
| Decision chat | Conversation with Claude Code before implementing, until the scope of the scenario is agreed |
| Main model + orchestrator | Claude Code itself |
| Research Agent | Claude Code following the rules in [kit/CLAUDE.md](../kit/CLAUDE.md) |
| ResearchTool → NotebookLM MCP | [notebooklm-py](https://github.com/teng-lin/notebooklm-py) over MCP |
| Corpus | One NotebookLM notebook: a self-contained project context document, fact sheets written for it, and a curated set of external sources (textbooks, papers, standards) |
| R8 (confirm before changing the corpus) | Every import was approved by a human in the conversation |

The spec describes a fuller system (separate decision chat, dispatcher, parallel agents); what runs today is the single-agent version of it. That is deliberate: the rules (R7 traceability, R8 confirmation) are what carry the value, and they work the same with one agent or five.

## 1. The corpus is built on purpose

The notebook was not filled with whatever search returned. The project keeps a `docs/notebooklm/` folder with:

- a **self-contained context document** describing the whole model, written so NotebookLM can answer questions about *this* project and not a generic one;
- **fact sheets** per physical topic (PET properties, line sizing, the building's real dimensions, lighting photometry), each listing its sources and how firm each number is;
- a **source list** ranked by priority, with the advice to start from 6–10 well-chosen sources rather than thirty;
- a **prompt sequence** that goes from understanding the model to explaining it, ending in a mock oral exam.

And one rule in `CONTRIBUTING.md` keeps it alive: *every time a physical interaction changes — a new equation, a new assumption, a recalculated number — its fact sheet is added or updated in the same commit.*

## 2. Research → confirm → import → implement

In September 2026 the client asked for a new scenario: a kitchen pot where water boils and pasta cooks. Boiling was already covered by the corpus (process modeling sources). Cooking pasta was not.

1. **Discover.** A fast web research run on the notebook with the query `pasta cooking kinetics water uptake starch gelatinization first-order model texture firmness vs cooking time in boiling water`.
2. **Confirm.** The sources found were shown to the user before anything touched the notebook (R8). Seven were imported; three that the research found could not be imported, and the source list says so.
3. **Query.** With the enriched corpus, the model questions went through `chat`: how water uptake evolves with time, what defines "al dente", at what temperature starch starts to gelatinize.
4. **Implement.** The answers became constants in the simulator's core, each one carrying its provenance.

## 3. Provenance lives in the data, not in someone's memory

This is the part that matters most. Every property in the ingredient catalog carries a **firmness label** and its source, stored in the saved file itself:

| Label | Meaning | Example from the pasta model |
|---|---|---|
| FIRM | Backed by a source | "Al dente" is the moment the white ungelatinized core disappears (AACC method, cited in a Chalmers thesis on pasta) |
| PARTIAL | Measured points, model choice for the shape | Two measured weight-gain points (Dziki and Laskowski, 2005) determine a first-order uptake curve: `k = 1.49e-3 1/s`, `a_eq = 2.715` |
| MODEL DECISION | A threshold the team chose, stated as such | "Overcooked" at five minutes past al dente, half of the measured range |
| NO SOURCE | The corpus was asked and does not have it | Uptake rate between 60 and 100 °C is interpolated linearly: no source in the notebook gives the activation energy |
| UNVERIFIED | An order of magnitude, not checked | Dry pasta heat capacity, 1.8 kJ/(kg·K) — with its impact estimated (≈3 °C on five liters) |

The two-point curve is worth a note: two measured points and two parameters mean the curve is **determined, not fitted**. There is no residual to show, and the test that covers it checks exactly that the curve passes through both points.

The same discipline appears where the notebook *didn't* help. The stove constant says in its docstring that its efficiency range is general technical reference and **does not come from the project notebook, which has no data on domestic stoves**. And the PET preform crystallinity fraction (0.15, labeled UNVERIFIED) records that the corpus was queried (September 2026) and confirmed no source reports a measured value for that process, so it is chosen mid-range as an order of magnitude, with the effect of changing it stated.

That is the whole point of rule R7: anyone reading the code can tell a sourced number from a chosen one.

## 4. Understanding, not just grounding

The notebook also served the team's own understanding. One example the project tells often: a reactor that settled at 260 °C and never reached its 320 °C jacket temperature looked like a bug. Asking the corpus for the steady-state energy balance of a continuously fed tank showed it was the correct answer — a weighted average between feed temperature and jacket temperature. The fix was not in the code but in the scenario: sizing the feed.

The same notebook generates the study guide, the FAQ and a two-voice audio overview (one voice from process engineering, one from software) configured through prompts kept in the repo.

## What it cost and what it bought

- **Cost:** keeping fact sheets current, and one more thing to install and authenticate (the MCP server drives NotebookLM through its web session, so it can break when Google changes the product).
- **Bought:** every physical number in the simulator can answer "where does this come from?", including the honest "nowhere, it's our choice". Unknowns are written down instead of hidden, which is what the spec asks of a `DecisionContext` too.
