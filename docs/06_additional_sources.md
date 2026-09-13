# Additional Source Profiles — Roy Morgan, RNZ, and Others Found Along the Way

Same discipline as `04_source_profiles.md`: these sources were fetched and checked
directly, not assumed from `02_data_sources.md`'s original notes. One-time proper
investigation, done now, so extraction code isn't built against a guess.

**Checked: 13 Sep 2026**

---

## Roy Morgan (roymorgan.com/findings)

**URL tested:** `roymorgan.com/findings/10321-nz-national-voting-intention-august-2026`
— fetches cleanly, no blocking.

### Structure

Each monthly finding is a single static HTML page (press release format) containing:

- **Headline party vote %** for the two blocs (National-led Government vs.
  Labour-led Opposition) and named minor parties, each with a month-over-month
  delta (e.g. "up 1.5%", "down 1%")
- **Seat projection table**, per party, computed from that month's party vote,
  including a note on which party would hold the balance of power
- **Government Confidence Rating** (a Roy Morgan-specific index), with a
  breakdown by gender and age band
- **Methodology block**: sample size, date range of interviews, exact survey
  question wording, non-response rate
- **Margin of error table**: a fixed reference table (sample size vs. confidence
  interval width), identical in structure across findings — this table itself is
  boilerplate, not something to re-extract each month
- **Direct PDF download link** for the same release
- **"Related Findings" list** at the bottom, linking to the 2-3 prior months —
  useful for discovering adjacent findings without needing to guess URLs

### What this means for extraction

- Party vote %, seat projections, and confidence rating are all **plain numbers in
  prose**, not in a table/JSON structure — extraction needs to parse sentences like
  "support for National dropped 1% to 31%", not scrape a data table.
- **Te Pāti Māori appears as its own named line** in the opposition bloc (not
  merged into "Greens" or "Other"), currently at 1.5% — confirms it should be
  tracked as a distinct party in our own scope, consistent with the decision to
  add it.
- **Finding-number URLs are chronological but not evenly spaced.** May–August 2026
  finding numbers were 10241, 10271, 10281, 10321 — gaps of 30, 10, 40. **Do not
  compute next month's URL by adding a fixed offset.** The reliable way to find the
  latest finding is to fetch `roymorgan.com/findings` (the index) or follow the
  "Related Findings" links from the most recent known finding.
- The PDF link is available if a cleaner extraction target is preferred over prose
  parsing — worth testing whether the PDF has the same numbers in a more
  structured layout, as a follow-up.

---

## RNZ Election Policy Guide (rnz.co.nz)

**URLs tested:**
- `rnz.co.nz/news/politics_election-2026/feature/rnz-election-policy-guide-2026`
- `rnz.co.nz/news/politics_election-2026/feature/maori-issues-policy-guide`

**Result: both blocked.** Anthropic's fetch tool gets bot detection on every RNZ URL
tried — this is not a one-off failure on a single page, it's site-wide behaviour, based
on testing two different pages under the same domain.

### What's known from search-result snippets (not a live fetch)

- The guide is organised as a **reverse-chronological log of policy announcements**
  across all parties — one line per announcement, e.g. "Labour talks fuel taxes",
  "ACT talks about 'one law for all'" — each presumably linking to a fuller writeup.
- There's a **dedicated sub-guide for Māori issues policy** specifically, separate
  from the main chronological guide, which already contains at least one NZ First
  policy (disestablishing Auckland's Houkura / IMSB, plus a Māori-seats referendum
  push) with linked source statements.
- Explicit statement on the page: "Minor parties are limited to those with a decent
  prospect of entering Parliament through party vote or a specific electorate" —
  RNZ's own inclusion threshold, worth noting since it's a different (looser) bar
  than "sitting in Parliament," and would include TOP/Opportunity by their own
  stated logic.

### What this means for the build

- **RNZ cannot be a live, runtime data source** for this project as currently
  architected — the app can't fetch it on demand the way it fetches party pages
  directly. Anything from RNZ would have to be a one-time manual read, copied in
  by a human, not an automated ingestion step.
- Given that constraint, RNZ is best used as a **completeness cross-check done once
  by hand** during Phase 1 — confirming the six-to-seven-party scope hasn't missed
  an announced policy — rather than as a pipeline input.

---

## Other sources surfaced incidentally (not yet decided on, noted for the record)

Found while checking the above, not requested, not yet added to scope:

- **NZ Herald's own policy grid** — explicitly scopes itself to "all parties
  currently represented in Parliament plus the Opportunity Party." This is an
  independent confirmation that a credible outlet draws its own party-scope line
  in the same place we just decided to draw ours (sitting parties + TOP), which
  supports the Te Pāti Māori addition.
- **PartyMap.co.nz** — claims to cover all 17 registered parties, organised by
  topic categories (Economy and tax, Health, Education, Housing and transport,
  Climate and environment, Law/justice/rights, Te Tiriti and democracy, Foreign
  affairs, Immigration, Family and social policy, Animals and drug law reform).
  This topic taxonomy is worth revisiting once our own topic-tagging schema is
  built — it may be a useful cross-check for category completeness, since it's
  broader than the "childcare" or "parental leave" single-topic tests done so far.
- **Parliament Pulse (parliamentpulse.co.nz)** — an independent, non-partisan
  comparison tool already doing something adjacent to this project's primary
  feature (comparing party positions across issues) plus a 29-question policy
  quiz. Not a data source to ingest, but worth being aware it exists as a
  reference point for what "done" can look like from a UX perspective.

Neither of these is in scope by decision — just recorded so they aren't
rediscovered and re-evaluated from scratch later.
