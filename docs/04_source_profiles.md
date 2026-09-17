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

---

## National (national.org.nz/policies)

**Fetched:** 13 Sep 2026.

### Confirmed correct — first fully-validated claim from the original framing doc

**National's "Modernising Paid Parental Leave" policy is real**, found at
`/policies/paid-parental-leave`. This is the first time a claim flagged as
unverified in `01_framing.md`'s Phase 1 warning note has actually checked out —
unlike the Labour childcare claim, which turned out wrong. Worth registering as a
genuine confirmation, not just another correction.

### Found, not previously documented

1. **The listing page is very likely incomplete as fetched.** Only 14 policy tiles
   came back from a single static fetch, despite category tabs for Economy, Tax,
   Law & Order, Education, and Health, plus a "More Policies" control and a
   "Search policies" field — both strongly suggesting this page loads additional
   content client-side (JavaScript pagination/filtering) rather than rendering
   the full list in the initial HTML. **No policy tiles appeared under "Health" at
   all** in what was fetched, despite Health being a listed category — a strong
   signal content is missing, not that National has zero health policies.
   `02_data_sources.md`'s "~12 individual pages" estimate may have undercounted
   for the same reason. **This needs a follow-up check** — either a browser-based
   fetch that executes JavaScript, or finding whether the "More Policies" control
   hits a discoverable API endpoint — before assuming 14 is the real total.

2. **URLs are nested under `/policies/`**, not flat at root level like Labour and
   Te Pāti Māori (`/policies/paid-parental-leave`, `/policies/kiwisaver`) —
   different convention per party, confirming a crawler cannot assume one URL
   shape works across all seven sources.

3. **No dollar figures on any of the 14 tiles** — consistent with the pattern seen
   on every party's listing page so far (Labour, Te Pāti Māori): costings, where
   they exist, live on individual policy pages or in separate text, not in the
   listing blurb itself. This is now a confirmed pattern across three parties, not
   a one-off — the extraction pipeline should assume listing-page text is
   insufficient for costing data by default, and always plan to check the
   individual policy page.

### Open question carried forward

Is the full policy list only accessible via JavaScript-rendered pagination, and if
so, what's the actual total count and does it change the fetch method needed for
this source specifically (vs. a plain static fetch that works for the others)?

---

## Greens (greens.org.nz/manifesto_2026)

**Fetched:** 13 Sep 2026.

### Confirmed correct

- **The "Children" manifesto page exists and genuinely doesn't mention "childcare"
  by that name** — exactly as `01_framing.md` originally claimed. It covers child
  poverty, whānau support, and wellbeing generally, not childcare as a service or
  cost. This is the second framing-doc claim confirmed right on direct check
  (alongside National's Paid Parental Leave), against one confirmed wrong
  (Labour/Medicard).

### Found, not previously documented

1. **Topic count is 38, not 34.** `02_data_sources.md` estimated a "34-topic
   manifesto" — the actual grid on the live page has 38 distinct topic cards. Minor
   undercount, but worth correcting since an extraction pass built to expect 34
   items would flag a discrepancy that isn't actually an error.

2. **A stale URL from a previous election cycle is still live and serving current
   content.** The "Climate Action: Emissions Reduction" card links to
   `/manifesto_2020_climate_action_emissions_reduction` — note "2020" in the slug —
   while another topic uses a `manifesto_2026_` prefix. The content itself is
   current 2026 policy; only the URL fragment is stale. **Lesson for extraction: a
   URL slug's year cannot be trusted as evidence of which election cycle the
   content actually belongs to** — always check the page's own dated content, not
   the URL string.

   **Correction (17 Sep 2026):** the claim above that "every other topic uses a
   `manifesto_2026_` prefix" was an assumption made from the grid page's link
   list, never verified against an actual fetched page. Fetching the Children's
   Policy page directly shows its real URL is `greens.org.nz/children_policy` —
   a short slug, not `manifesto_2026_children`. So the URL naming convention is
   not consistent across topics at all: some pages use the `manifesto_2026_`
   prefix, at least one uses a bare short slug. This reinforces the same lesson
   already learned from Labour and Te Pāti Māori: **never guess a party's
   per-page URL pattern — always follow the actual href from the listing page.**

3. **Every topic blurb is truncated with "..."** in the grid view — the full text
   of each policy lives only on its own dedicated page, not in the listing. This is
   a stronger version of the pattern already seen with Labour and National: here,
   even the general description is cut off, not just the costing. A crawler must
   visit all 38 individual pages, not just the grid, to get anything more than a
   one-sentence teaser per topic.

4. **Multiple alternate formats exist and are linked directly from the manifesto
   page**: a full single PDF, a separate Māori Manifesto PDF, a large-print/
   screen-reader-friendly version, a spoken/audio recording (hosted on Vimeo), and
   an Easy Read version. The full PDF in particular could be a more efficient
   single-fetch alternative to crawling all 38 individual pages — worth testing
   whether it contains the same content in one document.

5. **No dollar figures anywhere in the grid text** — consistent with the pattern
   across all parties checked so far (Labour, Te Pāti Māori, National, now Greens).
   One general funding statement appears at the top of the manifesto ("Paid for by
   a plan that will tax the super-rich and mega-corporations... and cut income tax
   for 96 percent of people") but this is a whole-manifesto funding narrative, not
   a per-policy costing — a different kind of claim than "$525 million" or "$220
   million," and should be extracted and compared differently if at all.

### Open question carried forward

Does the full single PDF (`manifesto_2026_full`) contain the complete, untruncated
text of all 38 topics in one document? If so, that may be a more reliable single
extraction target than 38 separate page fetches, each individually subject to the
same URL-staleness risk just found.

---

## TOP / Opportunity (opportunity.org.nz/policy)

**Fetched:** 13 Sep 2026.

### Important naming correction — affects every doc in this project

**The party has effectively rebranded from "TOP" to "Opportunity."** The site's own
page title is "The Opportunity Party," and every piece of body text refers to itself
simply as "Opportunity" — never once as "TOP" or "The Opportunities Party." This
matches what was already seen independently in the Roy Morgan poll ("Opportunity
Party support rises... to 9.5%") and the RNZ search snippet ("Opportunity has
outlined its 'Healthy People' policy"). Three independent sources now agree on the
current name. **`02_data_sources.md`, `00_project_overview.md`, and `01_framing.md`
all still refer to this party as "TOP" throughout — this is a naming correction
needed project-wide, not just a note in this file.**

### Found, not previously documented

1. **Policy count is 5 priority + 9 secondary = 14, not 5 + 7 = 12** as
   `02_data_sources.md` estimated. The 9 secondary policies are grouped under three
   sub-themes not previously documented: **Unity** (Citizens' Voice, Future-fit
   Education, Healthy People, Honouring Te Tiriti, Smart On Crime — 5 items),
   **Innovation** (Affordable Housing, Inter-Generational Infrastructure — 2
   items), **Nature** (Climate Action, Healthy Land — 2 items).

2. **This listing page has zero descriptive text for any policy** — not even a
   one-line summary. It's a pure navigational list of titled links grouped by
   theme, no blurb, no preview, nothing. This is the least content-rich listing
   page of any party checked so far (Labour, Te Pāti Māori, National, and Greens
   all had at least a short blurb per item). Every single one of the 14 policies
   requires an individual page fetch just to get a description, let alone a
   costing — there is no shortcut here the way there might be with Greens' single
   PDF.

3. **"Healthy People" is confirmed as their actual health-topic policy name** —
   independently cross-validated against the RNZ search snippet from
   `06_additional_sources.md`, which described the same policy by the same name
   before this page was ever fetched.

4. **"Healthy Oceans" is a Priority policy** — worth noting since this is a
   distinctly different environmental framing than Greens' "Oceans and Fisheries"
   or "Environmental Protection," useful once cross-party topic comparison is
   built.

### Open question carried forward

Given the total absence of descriptive text on the listing page, extraction for
this party will require fetching all 14 individual pages regardless of topic —
there's no way to pre-filter or summarize from the listing alone the way partial
filtering might work for other parties' richer listing pages.

---

## NZ First (nzfirst.nz/policy)

**Attempted:** 13 Sep 2026. **Direct fetch blocked — this is a project-level issue,
not just a note for this file.**

### The blocking issue

`nzfirst.nz` returns a `robots.txt` disallow for automated access. This is a
materially different and more serious problem than RNZ's bot-detection block
(`06_additional_sources.md`): RNZ's site technically blocked the fetch tool without
a published rule against it; NZ First has explicitly published a robots.txt rule
saying automated crawlers should not access the site. **The project's own stated
approach is to link every claim back to the party's own page** — if NZ First's site
cannot be crawled at build or runtime, this party cannot be given the same
treatment as the other six without either (a) a manual, human-performed one-time
capture the same way RNZ is being handled, or (b) explicit permission from the
party to crawl, or (c) accepting a gap and stating it openly rather than silently
using secondary sources dressed up as primary ones. **This needs a decision, not a
default** — see the note to the user accompanying this update.

### What's known from search-result snippets (not a live fetch)

- The `/policy` page itself appears to be a **reverse-chronological list of
  campaign policy announcements**, each with a short lead sentence — consistent
  with `02_data_sources.md`'s existing note that this source is "15+ individual
  announcement pages," weakest of all parties on structured cost/mechanism detail.
- **A real childcare-cost-adjacent policy exists: the "Kiwi Kids Grant"** —
  support for NZ citizens raising their first three children through the first
  three years, explicitly framed around reducing "the costs of raising a child."
  This is a genuine, concrete match to the kind of hidden-under-different-branding
  case `01_framing.md` was originally built around — it just turned out to belong
  to NZ First, not Labour or National, and to be named after a grant, not a
  category.
- A recurring throughline across multiple announced policies (NZ Super
  citizens-only eligibility from 2029, social housing prioritisation for citizens,
  birthright citizenship changes) is a **citizenship-based eligibility framing**
  applied across otherwise-unrelated topics — worth noting as a party-specific
  pattern that a topic tagger might otherwise miss if it only tags by subject
  (health, housing) and not by this recurring eligibility condition.
- A $100 billion Future Fund / 30-year infrastructure plan and a Special Economic
  Zone at Marsden Point were also found — both concrete, costed-sounding
  commitments, reinforcing that this party does have extractable content, just not
  through a source we're currently permitted to crawl directly.

### Open question carried forward — requires a decision, not just more research

How should NZ First be handled given the robots.txt block? Options to weigh:
manual one-time capture (same treatment as RNZ), seeking explicit permission,
or documenting the gap openly in the final submission rather than silently
substituting secondary sources for a party's own words.

### Decision (13 Sep 2026)

NZ First stays in scope — confirmed required, not optional. Given the robots.txt
block rules out automated crawling (and seeking explicit party permission isn't
practical inside the hackathon timeline), NZ First will use **one-time manual
capture**, the same treatment as RNZ: a human visits `nzfirst.nz/policy` and each
individual announcement page, copies the actual page content, and that static
capture is what the extraction pipeline runs against — not a live runtime fetch.

This needs to be stated openly in the submission's text description, not left
implicit: NZ First's content is sourced from the party's own published words,
same as every other party, but captured manually rather than fetched
automatically, because the party's own site disallows automated access. This is
a factual, defensible thing to disclose — it does not weaken the "every claim
links to its own source" rule, since the link still goes to the party's real
page; it only changes how the initial capture happened.

**Practical next step, not yet done:** someone needs to manually visit and save
the content of `nzfirst.nz/policy` and its individual announcement pages. This is
a to-do, not yet completed — noting it here so it isn't lost.
