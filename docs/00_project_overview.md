# NZ Election Policy vs Economic Reality

**Nebius x NVIDIA Global AI Hackathon — Best Apps and Agents Track**
**Deadline: 30 October 2026**

## The question

New Zealand's 2026 general election is 7 November. Five parties (National, Labour,
Greens, TOP, NZ First) have published policy positions, some with explicit costings.
Treasury has published its own fiscal forecast (BEFU 2026). RBNZ has published its
current rate and reasoning. Nobody has put these next to each other.

The tool reads a party's stated position and asks: does the number, the timing, or the
funding mechanism sit near what Treasury or RBNZ themselves are forecasting? Not
whether the policy is good. Whether the arithmetic holds up against the government's
own numbers.

## Why this is defensible where sentiment analysis is not

Analysing news coverage of party leaders produces a number — a sentiment score — that
looks objective and isn't. It reflects which outlets got scraped and how the model
reads sarcasm. Publishing "Leader X scores higher than Leader Y" weeks before an
election is a claim about people that can't be defended.

This tool never scores a person or a party. It states three things and stops:

1. What the party said (with a link to their own page)
2. What Treasury or RBNZ's own baseline says
3. Whether the two are consistent, and by how much

That is fact-stating, not opinion. "Labour's fiscal strategy targets an OBEGAL surplus
by 2029/30 using the original measure; Treasury's BEFU 2026 forecasts an OBEGALx
surplus of 1.1% of GDP in 2029/30 on a different measure" is a sentence a Treasury
analyst would write. "This policy is unrealistic" is not, and the tool never writes it.

## The one rule that must never break

**No verdicts. No scores. No ranking parties against each other.**

Every output is: claim → baseline → the comparison, stated plainly, sourced both ways.
If a check can't be made — no matching baseline figure exists — the tool says so rather
than guessing or staying silent. Silence on an awkward policy looks like bias by
omission; a stated "no baseline exists for this claim" is honest.

This rule governs the semantic layer (Phase 2 equivalent), the interface copy, and the
video script. It gets tested explicitly before submission, the way the bushfire
question bank tested the season convention and the cause caveat.

## Coverage

Five parties confirmed with live sources: National, Labour, Greens, TOP, NZ First.

**ACT is missing and that's a problem.** They're part of the governing coalition and
excluding them makes the comparison look selective before a single line of code is
written. Find their policy page in Phase 0 before building anything else.

Retail NZ's manifesto is a sixth source of a different kind — a sector's asks,
independent of any party — useful for a "does any party answer this" cross-check.

## What "done" looks like for the hackathon

- Working app on Nebius Token Factory / AI Cloud, at least one NVIDIA open model
- 3-minute public demo video
- Public repo with an open-source licence and a README
- The neutrality rule visibly holding in every demo question

## Notebook / doc series

| File | Purpose |
|---|---|
| `00_project_overview.md` | This document |
| `01_phase0_recon.md` | Platform capability checks, before writing anything |
| `02_data_sources.md` | Every source, its shape, and how it's fetched |
| `03_extraction_schema.md` | What comes out of a policy page vs a baseline document |
