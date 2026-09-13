# Source Profiles — Phase 1

Real findings from fetching each party's actual page, checked against what
`02_data_sources.md` assumed before any page was fetched. Same discipline as the
bushfire build: document what's wrong or newly discovered rather than quietly
correcting the earlier doc.

---

## Labour (labour.org.nz/our-policies)

**Fetched:** 13 Sep 2026

### Confirmed correct

- 16 individual policy pages, exact match to the count in `02_data_sources.md`.
- Costings do appear inline as claimed — Graduate Nurse Job Guarantee is explicitly
  "costed at $525 million," confirming the doc's example was accurate.
- The OBEGAL vs OBEGALx measure mismatch flagged in `02_data_sources.md` is real and
  explicit on the page itself: "return an OBEGAL surplus by 2029/30, using the
  original OBEGAL measure rather than OBEGALx." Any fiscal comparison must preserve
  this distinction rather than treating the two measures as interchangeable.

### Found, not previously documented

1. **Costings live in a separate FAQ block, not on the policy tiles.** The listing
   page shows 16 tiles, each with a title, one-line summary, and a "Learn More" link
   — no dollar figures on the tiles themselves. Cost figures appear further down the
   page in a prose FAQ section, and have to be matched back to the correct policy by
   context. An extraction pass reading only the tile text will miss nearly every
   costing.

2. **Most policies carry no costing at all.** Of the 16 listed, only 2 have an
   explicit dollar figure anywhere on this page (Graduate Nurse Job Guarantee: $525m;
   Backing Māori into Skilled Work: $21m/year). The rest state a start date or
   mechanism but no cost. `is_costed: false` must be treated as a normal, expected
   result in the extraction schema — not a sign extraction failed.

3. **No childcare or Paid Parental Leave policy appears anywhere on this page.**
   `01_framing.md` specifically claimed "Labour's [childcare-related content] sits
   inside their Medicard family-health framing." That's not supported by what's
   actually here — Medicard covers GP visits, prescriptions, maternity scans, and
   cervical screening; nothing is framed as childcare or parental leave support.
   This framing claim was made before any page was fetched and needs re-checking
   against National's and Greens' actual pages before the topic-tagging design
   relies on it.

4. **Individual policy pages sit at flat, unpredictable root-level URLs**
   (`/farecap`, `/medicard`, `/capitalgainstax`), not nested under `/our-policies/`.
   A crawler cannot guess these from a pattern — it must extract the actual
   `Learn More` href from each tile on the listing page.

5. **Category filter tabs exist on the page itself**: All Policies, Cost of Living,
   Health, Economy, Jobs and Skills. Worth noting for later — these are Labour's own
   categories, and (per finding 3) they don't include anything childcare-shaped,
   which supports the framing doc's broader point that a plain-English query has to
   match content regardless of the party's own taxonomy — it just means the
   specific childcare example needs to be swapped for something that's actually
   there, once we find it.

### Open question carried forward

Where does a childcare-equivalent policy actually live for each party, if anywhere?
This can't be assumed — it needs the same check-the-real-page treatment as everything
else above.

---

## Te Pāti Māori (maoriparty.org.nz)

**Fetched:** 13 Sep 2026. Added to project scope this session — previously absent
from `02_data_sources.md`'s six-party list despite holding sitting seats in
Parliament (4-6, per Wikipedia and Roy Morgan's August 2026 finding), a gap flagged
and corrected the same way ACT's wrong URL was, per the project's stated "excluding
them looks selective" principle.

### URL and structure findings

- **Domain is `maoriparty.org.nz`**, not any variation of "tepatimaori" — not
  guessable from the party's own name, had to be found via search, not assumed.
- **Two URLs return the same 17-item policy list**: `/policy` (singular, indexed,
  linked from the main nav) and `/policies` (plural, `noindex`, linked from the
  homepage's "See all policies" button). Checked both directly — genuinely
  identical content, not a repeat of the ACT trap. Use `/policy` as the reference
  URL since it's the indexed/canonical one.
- The **homepage itself only teases 10 of the 17 policies** — an extraction pass
  that only reads the homepage will silently miss 7 policies. Must use `/policy`
  as the entry point, not the homepage.
- Platform is NationBuilder. **URL slugs mangle macrons and can contain visible
  typos**: `/kai_sovereignt` (missing the final "y"), `/mokopuna_m_ori`,
  `/takat_pui` — macron characters (ā, ō) get replaced with underscores or dropped
  entirely in the slug. A crawler must follow the actual `href` from the listing
  page; it cannot reconstruct these URLs from the policy's display name.

### Content structure — most consistent of any party profiled so far

Every one of the 17 policies follows an identical, clean template:
- **Title**
- **"What we'll do"** — a short bullet list of concrete actions
- **"Why it matters"** — a short narrative paragraph
- **"Read more"** link to the full policy page

This is more extraction-friendly than Labour's page, where costings were buried in
a separate FAQ block disconnected from the policy tiles.

### Direct answer to the open question from Labour's profile

**"Cost of living" is a real, named policy category for Te Pāti Māori** — 17th item
on the list, titled exactly "Cost of living," covering income support, welfare, and
transport affordability. This directly confirms `05_voter_topics.md`'s top voter
concern maps onto at least one party's own actual category name — worth testing
whether National, Greens, and NZ First use the same or a different framing for the
same concern once their pages are profiled.

### Costing observed

No dollar figures appear on any of the 17 tiles themselves (same pattern as most of
Labour's tiles). However, external reporting (Waatea News, NZ Herald, both
independent of the party's own site) confirms the Te Tiriti Entrenchment policy
carries a stated $220 million cost over four years for a "Mātike Mai Fund" — this
figure was not found on the tile or in the crawled page text itself, meaning **the
full individual policy page** (`/te_tiriti_entrenchment`) likely contains it and
needs a direct fetch to confirm, the same way Labour's per-policy pages would need
checking beyond the listing page.

### Open question carried forward

Does the $220m figure actually appear on the party's own `/te_tiriti_entrenchment`
page, or only in third-party reporting about it? This matters for the "state what's
checkable" rule — if the cost is announced in media but not on the party's own
site, that's a materially different citation than a figure stated in the party's own
words.
