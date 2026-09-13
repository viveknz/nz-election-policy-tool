# Data Sources

Every source below was checked live. Record the check date next to each when you
re-verify, since party sites update through the campaign and a stale fetch is a wrong
answer with a confident tone.

**Checked: [today's date when you run Phase 0]**

---

## Party policy sources

| Party | URL | Shape | Notes |
|---|---|---|---|
| National | national.org.nz/policies | ~12 individual pages, categorised (Economy, Tax, Law & Order, Education, Health) | No visible costings on the listing page; check individual pages |
| Labour | labour.org.nz/our-policies | 16 individual pages | Explicit costings and start dates stated inline (e.g. Graduate Nurse Guarantee "$525 million") — best-structured source |
| Greens | greens.org.nz/manifesto_2026 | 34-topic manifesto + full PDF + Māori Manifesto PDF | Long-form prose per topic, not itemised costings |
| TOP | opportunity.org.nz/policy | 5 priority + 7 secondary pages | Thematic, not itemised |
| NZ First | nzfirst.nz/policy | 15+ individual announcement pages | Weakest on stated mechanism/cost — mostly headline commitments |
| ACT | act.org.nz/policies | 8 category pages (Economy & Cost of Living, Law & Order, Health, Equal Rights & Democracy, Housing & Infrastructure, Backing Rural NZ, Education, Hunting/Conservation/Firearms) | Correction from initial search: an indexed policy page exists at `/policies` (not `/policy`, which doesn't exist). Same shape as National/TOP — categorised index. The `/news` feed found earlier is separate and not needed as a policy source. |

## Sector source

| Source | URL | Shape |
|---|---|---|
| Retail NZ | retail.kiwi (2026 Election Manifesto PDF) | PDF, sector asks independent of any party |

## Public opinion

| Source | URL | Shape |
|---|---|---|
| Roy Morgan | roymorgan.com/findings (monthly) | Press-release HTML + downloadable PDF. August 2026 finding: National-led 49%, Labour-led 41%, TOP 9.5% and holding balance of power. Methodology and margin-of-error table included every release. History runs back through at least May 2026 at predictable URLs (finding numbers increment). |

## Economic baseline — the anchor for every check

| Source | URL | What it gives |
|---|---|---|
| Treasury BEFU 2026 | treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2026 | Net core Crown debt peaks 46.1% of GDP in 2027/28. OBEGALx deficit 2.4% of GDP in 2026/27, improving to 0.5% surplus 2028/29, 1.1% surplus 2029/30. Consolidation of 3.5% of GDP over three years, decomposed into expense reduction (2.3pp), cyclical revenue/fiscal drag (0.8pp), SOE/Crown entity performance (0.4pp). |
| RBNZ OCR | tradingeconomics.com/new-zealand/interest-rate (or RBNZ direct) | 2.25% as of April 2026 meeting, held since. Raised 25bp in July on an oil-price shock lifting near-term inflation while growth softens. |

**Note the measure mismatch risk already visible:** Labour's own fiscal strategy states
a target using "the original OBEGAL measure rather than OBEGALx." Treasury's BEFU
figures above are OBEGALx. Any check comparing Labour's target against Treasury's
forecast must either convert between the two measures or say plainly that they're
different and shouldn't be compared as if identical. This is exactly the kind of
mismatch that produced wrong answers in the bushfire build — flag it now rather than
discover it after ingestion.

---

## Fetch method by source type

| Type | Method | Fragility |
|---|---|---|
| Individual policy pages (National, Labour, NZ First) | Fetch each URL, extract main content | Low — static HTML, one page per policy |
| Manifesto listing (Greens) | Fetch listing page for links, then each linked page, or the single PDF | PDF is more stable for one-shot ingestion; per-page is more current if updated mid-campaign |
| TOP | Same as National/Labour | Low |
| Retail NZ | Direct PDF download | Low — static document |
| Roy Morgan | Fetch the monthly finding page; PDF also available | Medium — URL pattern must be confirmed to hold for earlier/later months |
| Treasury BEFU | Fetch publication page, likely links to PDF chapters | Low, but large document — extract only the fiscal summary numbers needed |
| RBNZ OCR | Prefer RBNZ's own site over aggregators (tradingeconomics, CEIC) for the authoritative figure | Aggregators drift out of sync during the ingestion window |

## Historical validation data (for the MMP seat calculator)

The seat calculator is deterministic — pure arithmetic against New Zealand's documented
MMP formula, no LLM involved in the calculation itself. It needs a ground truth to
prove it's correct before it's trusted with a hypothetical scenario.

| Source | URL | What it gives |
|---|---|---|
| Data.govt.nz Election Catalogue | catalogue.data.govt.nz (search "Electoral Commission") | Official party vote %, seat counts, and electorate-level results for past elections, as downloadable CSV |

**How this gets used:** feed a past election's actual party vote percentages into the
calculator and confirm it reproduces the actual seat allocation, including any
overhang seats. 2023 is the obvious test case — Wikipedia's own 2023 election page
already states 122 seats were filled against the normal 120, which is an overhang
scenario. If the calculator reproduces that from raw vote shares, it's trustworthy for
a hypothetical 2026 scenario. If it doesn't, the arithmetic is wrong and nothing built
on top of it can be trusted regardless of how good the interface is.

## Optional polish (not core to either feature)

| Source | URL | What it gives |
|---|---|---|
| Stats NZ Geographic Data Finder | datafinder.stats.govt.nz | Electorate boundary shapefiles/GeoJSON, for a map view if time allows |
| Electoral Commission Media Resources | elections.nz/media-and-news/media-resources | Finalised candidate lists and polling place locations, closer to election day |

Both are genuinely optional. Neither feeds the two core features (policy-vs-baseline,
seat arithmetic) — they'd only matter if a visual map became part of the demo, which
is not currently planned.

## Explicitly excluded, and why

Two categories of data surfaced during research and were deliberately left out. Recorded
here so the reasoning isn't lost and doesn't get silently reconsidered later in the
build.

**NZES survey data and census-by-electorate demographics, used to model "why an
electorate leans a certain way."** This asks a model to infer voter motivation from
demographic proxies — age, income — and state it as if it were a finding. That's
characterisation of a group of people from statistics, the same category of problem as
sentiment-scoring a party leader, just moved from a person to an electorate. Excluded.

**Parliamentary transcripts and speech data intended to give an AI persona "the
authentic negotiation logic" or speaking style of a real MP.** Any output modelled this
way generates things a real, currently-serving politician did not say and presents them
in their voice, days before they're on a ballot. This is true regardless of how
accurate or well-sourced the training material is — the problem is the output, not the
input. Excluded entirely, along with the "Kingmaker negotiator chatbot" feature it would
have powered.

Donation-data-driven "polling variance" modelling was also excluded: it invents a
causal mechanism (money → hypothetical future polling movement) that isn't grounded in
anything the tool can check or source. If donation disclosures are used at all, they
should be presented as a plain fact ("Party X disclosed $Y in donations this quarter,
source: Electoral Commission") with no inferred effect attached.


- [x] ACT's policy page URL — found at act.org.nz/policies (note: plural, `/policy`
      singular does not exist). Eight category pages, same indexed shape as
      National/TOP. The earlier `/news`-feed finding was superseded once the correct
      URL was found — worth remembering that a missing page can look like "no source
      exists" when it is actually "wrong URL guessed."
- [ ] Whether Treasury or RBNZ expose the underlying figures in a table/API rather than
      prose, which would save real extraction effort
- [ ] Whether party pages are likely to change during the build window (all five sites
      are actively campaigning, so re-check dates matter)
- [ ] Whether RNZ's election policy guide (rnz.co.nz, chronological, all parties) is
      worth fetching as a completeness cross-check — not a primary source, but useful
      for confirming the ingestion hasn't silently missed a party's policy

## Source-shape note (revised)

All six parties (National, Labour, Greens, TOP, NZ First, ACT) now confirmed to expose
policy through some form of categorised index or listing page. NZ First's is a flat
chronological list rather than a topic index, and is thinner on stated mechanism/cost
than the others, but it is still clearly policy-framed content rather than mixed
commentary. No source currently requires the commentary-vs-policy classification step
described in the earlier draft of this section — that concern turned out to be based on
a wrong URL for ACT, not a real property of their site. Worth remembering: a 404 or a
guessed wrong path is not evidence a data shape problem exists — confirm the correct
URL before designing around an assumption.
