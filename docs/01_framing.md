# Framing: Problem, Solution, Approach

This is the document that goes into the submission's project description, and it's
what the demo video script gets written from. Get this right before writing code —
everything else follows from it.

> **Flagged during Phase 1, not yet fully reconciled below:** this document was
> written before any real party page was fetched. Two things it assumed have since
> been checked and found wrong — see `04_source_profiles.md` and
> `05_voter_topics.md` for the full findings:
> 1. **Party count is seven, not six** — Te Pāti Māori was missing entirely.
> 2. **The "childcare" example throughout this document is unverified and likely
>    wrong.** Labour's page has no childcare-framed policy at all (checked
>    directly), and current NZ voter polling doesn't show childcare as a live
>    top-of-mind issue — "parental leave" and "cost of living" are the better-
>    evidenced real examples. The specific claim below that "National's related
>    material sits under Paid Parental Leave" has not yet been checked against
>    National's actual page. The narrative below is left as-is rather than
>    silently rewritten — treat every "childcare" mention past this point as an
>    illustrative placeholder needing a real replacement, not a confirmed fact.

---

## The problem

New Zealand's 2026 general election is 7 November. Seven parties have published
policy positions — some costed and dated, some not. Treasury has published its own
fiscal forecast. RBNZ has published its current rate and reasoning for it. Nobody has
put these next to each other.

A voter who wants to check a party's promise against reality has to read the party's
own page, then separately find and read a 100-page Treasury document, then work out
whether the two are talking about the same thing. Almost nobody does this. Most voters
form a view from a headline or a 30-second clip.

New Zealand also runs MMP, where a single party almost never wins outright and the
government is decided by which parties can combine to 61 of 120 seats. Polling moves
month to month, and small shifts change which coalitions are even mathematically
possible. Right now TOP is polling at 9.5% and positioned to hold the balance of power
— a fact that changes the practical meaning of every other party's policy, since none
of them govern alone.

So there are two related problems: policy claims that go unchecked against public
economic data, and seat arithmetic that most people can't do in their head.

## The solution

A tool where a voter asks about a topic in their own words — "what does each party say
about childcare" — and gets back every party's actual stated position, side by side,
each with a link to their own page. That's the primary feature. No opinions, no
rankings, no verdicts about which party is right — just each party's own words, found
and shown.

**This is harder than a keyword search.** None of the six parties use the word
"childcare" as a category. National's related material sits under Paid Parental Leave.
Labour's sits inside their Medicard family-health framing. The Greens have a dedicated
"Children" manifesto page that doesn't mention childcare by that name either. A voter
asking a plain question shouldn't need to know each party's internal taxonomy —
matching intent to differently-worded policy is the actual retrieval problem, and it's
where an LLM earns its place over a simple keyword search across the six sites.

**A second, optional layer sits on top of the same retrieval:** where a party has
attached a cost or start date to a policy, the tool can note whether that figure sits
near Treasury's BEFU 2026 forecast or RBNZ's current position — stated as "Party X's
figure, Treasury's figure, here's the difference," never as "credible" or "not
credible." This is depth for someone who wants it, not the entry point, and it inherits
the same rule as the primary feature: state what's checkable, cite both sides, stop
there.

**A third feature, supporting rather than central:** an MMP seat and overhang
calculator. New Zealand's Sainte-Laguë formula and overhang mechanic are exact and
well-documented (confirmed against Parliament's own record — the Māori Party's 2005
overhang, 4 electorates against a 2.1% party vote, producing a 121-seat Parliament, is
the first and best-verified test case). This calculator is pure arithmetic with no
LLM involved in the computation itself, and it's useful for showing what a given
polling scenario means for who could govern.

**Worth being direct about this feature's positioning:** a live public tool,
election2026.nz, already does seat-and-overhang calculation well, backtested against
four past elections. Building the same thing from scratch adds little on its own. It
stays in this project because it's a good way to validate the pipeline's arithmetic
against real historical data, and because "which parties could combine to govern"
is a natural follow-on question once someone has read the parties' actual policies —
but it is not the reason to build this tool, and the demo should not lead with it.

## Why we're building it

**Because a voter who wants a straight answer to "who supports X" today has to visit
six different websites, each organised by its own categories, and read enough to
translate their question into whatever language that party uses.** That's real friction
for an ordinary decision, and it's exactly the retrieval problem an LLM is suited to —
not generating an opinion, but finding the relevant real content regardless of how it's
labelled.

**Because the fiscal cross-check is tedious and nobody does it by hand**, and it's a
natural next question once someone has already found a party's stated position — "is
this actually paid for" follows naturally from "what did they promise."

**Because the alternative — sentiment or opinion tools about an election — is
indefensible days before a vote**, and we specifically want to demonstrate that a
technically ambitious project doesn't require manufacturing content to be interesting.
Retrieval-with-citation across inconsistent sources is itself the hard engineering
problem, and getting it right — never drifting into summarising into an opinion, never
inventing a position a party didn't state — is the actual demonstration of
understanding the problem space.

## The approach

Same discipline as a previous project of ours that placed 2nd in the Databricks Genie
App Challenge: profile every source before writing extraction code, document every
trap found, and never let a metric ship without checking what it actually counts.

1. **Ingest** seven parties' policy pages, Treasury's BEFU 2026, RBNZ's OCR history, and
   Roy Morgan's monthly polling — each already profiled for shape and quirks (see
   `02_data_sources.md`).
2. **Extract** per-party, per-topic positions with source links. Each extracted item
   needs a topic tag independent of the party's own category name, so a query about
   "childcare" can surface National's Paid Parental Leave page, Labour's Medicard
   family provisions, and the Greens' Children manifesto page together, even though
   none of the source pages use that word.
3. **Match** a plain-English query against those topic-tagged extractions — this is
   the primary feature and the one the demo leads with.
4. **Compare**, as a secondary layer, any costed or dated claim against Treasury's
   BEFU 2026 or RBNZ's baseline, producing claim-baseline pairs with an explicit "no
   baseline exists for this claim" path rather than silence or a guess. OBEGAL and
   OBEGALx are tracked as distinct metrics that are never silently treated as
   equivalent.
5. **Calculate** seats under MMP for any polling input, including overhang, as a
   separate, fully deterministic feature with no LLM involved — validated against the
   confirmed 2005 Māori Party overhang before it's trusted with a hypothetical
   scenario.
6. **Present** through a chat-style interface backed by an NVIDIA open model on Nebius
   Token Factory, so a user can ask "what does each party say about childcare" and get
   an answer built from step 3, with a natural path into steps 4 and 5 for anyone who
   wants to go further.

## What "done" looks like

- A plain-English topic query returns every party's actual stated position, correctly
  matched even when the party's own category name is completely different from the
  query.
- Every claim shown has a clickable source, both for the party position and, where
  shown, the baseline.
- The seat calculator reproduces the 2005 overhang correctly from raw historical vote
  shares before it's used on any hypothetical scenario.
- No output anywhere characterises a party, ranks them, or predicts an election
  outcome as fact rather than as a labelled scenario the user chose.
- A judge who knows nothing about NZ politics can ask about a topic and understand the
  point inside twenty seconds of the demo video.
