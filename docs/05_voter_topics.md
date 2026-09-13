# Voter Topics — Grounding for Topic-Matching Design

`01_framing.md` used "childcare" as a worked example of the topic-matching problem
(a voter's plain-English query vs. each party's own category name). That example was
invented, not checked against what NZ voters are actually asking about in 2026. This
document replaces it with real, sourced data before the topic-tagging schema is built
around the wrong test case.

**Checked: 13 Sep 2026**

---

## Source

Ipsos Issues Monitor (quarterly since 2018), as reported by The Spinoff (26 May 2026
and 31 Jul 2026 editions) and corroborated by NZ Herald and a general-audience election
guide. Not a single source — cross-checked across three independent write-ups of the
same underlying poll series.

## Top voter concerns, most to least cited (2026 cycle)

1. **Cost of living / inflation** — dominant and consistent for 3+ years; ~6 in 10
   voters name it among their top three concerns.
2. **Fuel and petrol prices** — a distinct, sharply-rising sub-concern, separate from
   general cost of living in how it's tracked.
3. **Healthcare** — hospital capacity, GP access, treatment cost. Ipsos data shows
   this is significantly more important to women voters specifically than the
   overall average.
4. **Economy and employment** — unemployment at 5.6% as of the most recent data,
   the highest level in over a decade.
5. **Housing** — affordability, supply, rents.
6. **Crime and public safety.**
7. **Climate and energy.**

## Notable finding: parental leave, not childcare

One Spinoff piece (31 Jul 2026) noted rising voter enthusiasm for "extended parental
leave" this cycle, specifically tied to the contest for women's votes. This is the
closest real equivalent to the original "childcare" test case — but it's parental
leave, not childcare, and it's a live, real policy angle rather than an invented one.

This matters directly for Phase 1: when profiling National's policy page (which
`02_data_sources.md` already flags as filing related material under "Paid Parental
Leave"), that page should be checked against this specific finding rather than the
generic "childcare" guess.

## What this changes

- **Test queries for topic-matching should be drawn from this list**, not invented:
  "cost of living", "petrol prices", "healthcare", "unemployment", "housing", not
  "childcare".
- **"Childcare" is retired as the framing example.** It was never confirmed against
  real party pages (see `04_source_profiles.md` — Labour has no childcare-framed
  policy at all) and it isn't what voters are actually asking about, per this data.
- **Parental leave replaces it** as the specific test case for "party's own category
  name differs from a plain-English query" — to be confirmed once National's actual
  Paid Parental Leave page is fetched and profiled, the same way Labour's page was.

## Open question carried forward — resolved

~~Does any party frame a policy under "cost of living" as its own category name~~
**Resolved 13 Sep 2026**: yes. Te Pāti Māori has a policy literally titled "Cost of
living" (see `04_source_profiles.md`). Still worth checking whether National,
Greens, and NZ First use the same framing or something different once their pages
are profiled — this confirms at least one party matches voter-side language
directly, it doesn't confirm all of them do.
