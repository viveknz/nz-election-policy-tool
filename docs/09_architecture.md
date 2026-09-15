# Architecture — Agents, Modules, and the Orchestrator

Decided 15 Sep 2026, after the extraction schema debugging in
`08_extraction_schema.md` surfaced repeated evidence that this model contradicts
itself and hallucinates in subtle ways even under careful constraints. That
evidence directly shaped the choices below.

---

## Module breakdown

Each module has one job and sees only the minimal context it needs — this is
both a context/memory-saving design and a safety design, since a module that
never sees a voter's raw question can't be talked into producing a verdict.

| Module | Job | LLM? | Model |
|---|---|---|---|
| **Fetch** | Given a URL, retrieve raw page text. Retry logic, robots.txt/bot-block detection lives here | No | — |
| **Extraction** | Given one page's raw text + party name, return the structured policy schema (`08_extraction_schema.md`) | Yes | Nemotron-3-Nano |
| **Topic-Match** | Given a voter's query + the pre-built corpus of already-extracted policies, return relevant matches across parties | Yes | Nemotron-3-Super |
| **Fiscal Compare** | Given one costed claim + its matching Treasury/RBNZ baseline figure, produce a stated comparison — never a verdict | Yes | Nemotron-3-Ultra |
| **Seat Calculator** | Pure MMP arithmetic from party vote percentages, including overhang | No | — |
| **Orchestrator** | Routes a user's question to the right module(s), assembles the final answer | See below | — |

Fetch and Extraction run **offline/in batch** to build the policy corpus ahead of
time — they are not live, per-question agents. Topic-Match, Fiscal Compare, and
Seat Calculator are **live sub-agents**, called by the Orchestrator per user
question, each receiving only the specific payload it needs (Fiscal Compare
never sees the whole corpus, only the one claim + its baseline row; Topic-Match
never sees raw HTML, only pre-extracted structured policies).

## The Orchestrator: deterministic router, not an LLM call

**Decision: the Orchestrator is a deterministic router, not an LLM making
judgment calls about which sub-agent to invoke.**

### Why, given the evidence from this session

`08_extraction_schema.md` documents, in order: a nullable-type bug producing
empty fields, a repetition loop burying a real answer inside garbage text, a
fabricated multi-paragraph fiscal analysis citing entities that don't exist, an
internal contradiction where the model extracted a correct dollar figure and
then separately claimed no dollar figure existed, and a fully invented ISO
timestamp with no basis in the source text — this last one appearing even at
`temperature=0`, which is supposed to be the most conservative setting
available.

The project's one non-negotiable rule is "no verdicts, no scores, no ranking
parties." Routing logic decides which capabilities get invoked for a given
question — that is itself a kind of judgment call, and this session gave
repeated, concrete evidence that this model's judgment calls are not reliable
enough to trust with a rule that has zero tolerance for failure. A
misrouted question is recoverable (worst case: the user doesn't get the
fiscal-comparison layer they wanted). A routing LLM that decides, on its own
initiative, that a question "deserves" an opinion is exactly the failure mode
the whole project is built to prevent — and asking an LLM to route is one more
surface where that could happen, for no real gain, since routing a factual
question ("does this look like it needs a cost check") is pattern-matchable
without judgment at all.

### What the router actually does

Simple, testable, rule-based logic — no LLM call:
- Every question goes to **Topic-Match** first (the baseline feature — every
  question needs to find the relevant policies)
- If the matched policy is costed (`amount` is non-empty in the corpus) **and**
  the question contains cost/afford/realistic-type language, also call
  **Fiscal Compare**
- If the question mentions specific vote percentages or "what if X gets Y%",
  route to **Seat Calculator** instead of/alongside Topic-Match
- Otherwise, Topic-Match's result alone is the answer

This is deliberately simple to start. It can be tested with exact input/output
pairs the same way the extraction schema was — a router test suite is a
natural next step once this exists in code, not before.

### Revisit condition

This is a starting decision, not a permanent one. If real testing shows the
deterministic router is too rigid to handle genuinely ambiguous real voter
questions well, an LLM-based router becomes worth reconsidering — but only
with the same kind of adversarial testing this session just did on extraction,
not adopted on the assumption that "more agentic" is automatically better.
