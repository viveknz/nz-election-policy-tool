# Extraction Schema — Design and Debugging Record

This documents the core extraction schema tested against real Labour policy text
(`extraction/test_extraction_schema.py`), and the debugging path taken to get from a
naive schema to one that reliably produces clean, non-hallucinated output. Recorded
in full because the failure modes found here apply to every party's extraction, not
just this one test case.

**Tested: 15 Sep 2026**, against Labour's Graduate Nurse Job Guarantee page
(`labour.org.nz/election-policy-pages/graduate-nurse-job-guarantee/`), using
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` via Nebius Token Factory.

---

## The schema (current, working version)

Fields: `policy_name`, `party`, `stated_position`, `is_costed`, `amount`,
`start_date`. `source_url` is deliberately **not** a model-extracted field — see
below.

Every free-text field carries a `maxLength`. `amount` additionally carries a regex
`pattern`. This wasn't the original design — it's the result of three rounds of a
real failure being found and fixed.

## The debugging path — three distinct failure modes, in order

### Round 1: nullable types silently produced empty strings

Original schema used `"type": ["string", "null"]` for `amount` and `start_date`.
Result: both fields came back as **empty strings**, even though "$525 million" and
"July 2026" are both clearly present in the source text. The model correctly set
`is_costed: true` but didn't populate the value that should have gone with it.

**Fix:** dropped the nullable type union, used plain `"string"` with an instruction
that empty string means "not stated." This is likely a constrained-decoding
limitation specific to this backend — nullable/multi-type fields under `strict:
true` mode appear to make the model default to an empty fallback rather than reason
about actual content.

### Round 2: unconstrained free-text fields produced repetition loops

With plain `"string"` type and no length limit, `amount` came back as:

```
fund_amount_nzd_million_2025_2026_2027_2028_...(repeated years)..._An other
form of costing is the funding of $525 million
```

The real answer was in there, buried at the end of a long run of repeated
snake_case tokens. **A naive sanity check that just does a substring search (`"525"
in amount`) would have reported this as a PASS** — worth flagging on its own: a
check that only confirms a fact's presence, not the field's overall shape, can hide
a broken extraction behind a green checkmark.

**Fix attempt 1:** added `maxLength: 40` and a regex `pattern` to `amount` alone.
This fixed `amount` completely, but the same underlying problem simply moved to the
next unconstrained field.

### Round 3: the same root cause escalated to outright hallucination

Once `amount` was constrained, the next free-text field left unconstrained
(`source_url`, then `start_date` once `source_url` was removed) exhibited a worse
version of the same failure — not repetition this time, but **fabricated content**:
a multi-paragraph invented fiscal analysis referencing a "Stage Graduation
Account," an entity called "SCERTI," a citation to "Labour Plan 38," and an
internal monologue questioning its own assumptions — none of which appears
anywhere in the real source text. This is confabulation, not extraction, and it
happened silently inside a field that looked plausible enough (starts with "2027")
that the naive substring check passed it as correct.

**This is the most important finding in this document.** The project's core rule —
no invented claims, only what's checkable and sourced — was violated one layer
below the user-facing app, inside the extraction step itself, and a shallow sanity
check did not catch it.

**Fix:** `maxLength` applied to every remaining free-text field (`policy_name: 80`,
`party: 40`, `stated_position: 200`, `start_date: 60`), and the sanity checks
rewritten to verify length and shape (no `?`, no runaway size), not just "does the
right substring appear somewhere in this string."

## Confirmed working result (after all fixes)

```json
{
  "policy_name": "Graduate Nurse Job Guarantee",
  "party": "Labour",
  "stated_position": "Offer every eligible New Zealand-trained graduate nurse a job in the health system",
  "is_costed": true,
  "amount": "$525 million",
  "start_date": "2027 (roles offered from 2027, graduates sitting State Final"
}
```

Clean, no repetition, no fabrication. One minor cosmetic issue remains: `start_date`
is hard-truncated mid-word by the 60-character limit ("...sitting State Final" cuts
off before "examination"). This is truncation working as designed, not a new bug —
noted as a small follow-up (raise the limit slightly, or instruct the model to
self-truncate to a complete clause) rather than an urgent fix.

## Standing lessons for every field added to this schema going forward

1. **Never use a nullable/multi-type field** (`["string", "null"]`) under this
   model's structured output — use plain `"string"` with an empty-string
   convention instead.
2. **Every free-text field needs a `maxLength`, no exceptions.** An unconstrained
   string field is not a "probably fine, just less structured" choice — it's a
   demonstrated route to either repetition loops or outright hallucination with
   this specific model/backend combination.
3. **Never ask the model to extract or echo back information already known
   to the calling code** (like `source_url`, which we control because we did the
   fetching). Attach it programmatically after parsing instead — this removes an
   entire field from the failure surface for free.
4. **A sanity check that only confirms a fact's presence (substring search) is not
   a real check.** It can and did pass on a field containing a wall of fabricated
   text, simply because the correct year appeared somewhere within it. Real checks
   need to verify length/shape as well as content.

---

## Round 4 (15 Sep 2026): consistency testing and a second real party

Testing expanded to include a second, harder real source (Te Pāti Māori's Te
Tiriti Entrenchment page — see `04_source_profiles.md`), and each case run 3x
to check whether results are actually reliable rather than lucky once.

### Finding: the model missed a dollar figure phrased as an action, not a cost statement

Te Pāti Māori's page never uses the word "cost" — the $220m figure is embedded
in an action bullet ("establish a $220 million Mātike Mai Fund"), unlike
Labour's explicit "Costed at $525 million." Initial runs correctly identified
`is_costed` but left `amount` empty, or vice versa. **Fix:** broadened the
schema's field descriptions to explicitly say a dollar figure counts regardless
of whether it's framed as an explicit cost statement.

### Finding: `is_costed` and `amount` can contradict each other in the same response

Even after the above fix, some runs returned `amount: "$220 million"` and
`is_costed: false` **in the same JSON object** — an internal contradiction, not
just an occasional miss. The model was treating "is this costed" as an
independent judgment rather than deriving it from whether it had actually found
a figure.

**Fix:** removed `is_costed` from the schema entirely. It's now computed in
code — `is_costed = bool(amount)` — after parsing, the same pattern already
used for `source_url`. This is a generalizable lesson: **any field whose value
is fully determined by another field the model already extracts should not be
asked of the model as a separate judgment.** It adds a second chance to get the
same fact wrong, and — as seen here — a chance to contradict the first answer
outright.

### Finding: `temperature=0` gives repeatability, not correctness

Before this fix, the same exact input produced inconsistent results across
runs (sometimes correct, sometimes not) even before `temperature=0` was set.
Setting `temperature=0` was tested as a fix — it did make output more
consistent, but on one test run it consistently reproduced the *same wrong*
answer three times in a row, and separately, one run produced a fully invented
ISO timestamp (`2025-11-03T00:00:00Z`) with no basis anywhere in the source
text. **Determinism is not the same as accuracy** — a model can be perfectly
repeatable and repeatably wrong. This doesn't mean `temperature=0` was a bad
choice (it's still kept, since unpredictable variance is worse for a factual
task than consistent behaviour that can be tested and fixed) — it means
`temperature=0` alone was never going to be a complete fix, and wasn't treated
as one.

### Finding: occasional JSON truncation persists even at `max_tokens=2000`

The model's hidden reasoning trace (visible in Phase 0's raw responses)
consumes tokens from the same budget as the actual JSON answer. At
`max_tokens=800`, this caused frequent truncation (valid start of a JSON object,
cut off mid-string, no closing brace). Raising to `max_tokens=2000` reduced but
did **not** eliminate this — one run out of six across this round's testing
still truncated. Unlike every other finding in this document, this isn't a
prompt or schema problem to solve with better instructions — it's an inherent
reliability characteristic of the call.

**Decision:** rather than continuing to raise `max_tokens` as a blunt fix, the
real extraction pipeline needs **retry-on-parse-failure logic** — if
`json.loads()` fails, retry the call (with a small retry cap) rather than
treating a single failed call as a permanent extraction failure. This is a
pipeline-level design requirement, not a schema field, and is carried forward
to whichever module actually runs extraction across all seven parties.

### Result after all Round 4 fixes

Te Pāti Māori: **3/3 clean runs**, no contradiction, correct amount every time.
Labour: **2/3 clean runs**, with the one failure being a JSON truncation (an
infrastructure reliability issue, not a wrong-value or hallucination issue) —
confirming the retry-logic decision above rather than requiring a further
schema change.

## Standing lessons, updated after Round 4

5. **Don't ask the model to independently judge something fully derivable from
   another field it already extracted** (e.g. `is_costed` from `amount`).
   Compute it in code instead — this removes an entire class of self-
   contradictory output.
6. **`temperature=0` improves consistency, not correctness.** Keep it for
   factual extraction tasks, but don't treat it as a substitute for actually
   checking whether repeated results are right.
7. **Occasional call-level failures (JSON truncation) are a pipeline concern,
   not a schema concern.** The fix is retry logic around the call, not an
   ever-increasing `max_tokens` value chasing a moving target.

---

## Round 5 (17 Sep 2026): fabricated dates, and the first real multi-party corpus

Extending the corpus to National (two real texts: an explicitly uncosted
policy, and a genuinely costed-in-reality policy whose dollar figure doesn't
actually appear in the fetched HTML — see `04_source_profiles.md` for the PDF
question this raises) surfaced a new, serious instance of fabrication.

### Finding: the model invented a fully fictional ISO date, twice, with two different fake values

For National's "Flexible Use of Paid Parental Leave" — a real page whose actual
text contains **no dates or numbers of any kind** ("This is a simple,
pragmatic change that will come at no extra cost to the taxpayer") — the model
returned `start_date: "2023-06-14T00:00:00+00:00"` on one run and
`"2025-01-01T00:00:00Z"` on a re-run of the identical input. Neither date
appears anywhere in the source. This is confabulation, the same category as
the earlier "Stage Graduation Account" incident in Round 3, but this time
producing a precise, plausible-looking, fully structured timestamp instead of
prose — arguably more dangerous, since a clean ISO date is far more likely to
be trusted downstream without a human noticing anything is wrong.

**This also confirms a separate, important fact: `temperature=0` does not
guarantee identical output across calls on this backend.** The same exact
input produced two different fabricated dates on two different runs. This
doesn't contradict Round 4's finding that "temperature=0 gives repeatability,
not correctness" — it sharpens it. Repeatability itself isn't fully
guaranteed either, at least not on this hosted serving stack (likely due to
batching or kernel-level non-determinism common to many hosted LLM backends,
not a project-specific bug).

### Fix: validate extracted values against the source text, don't just trust the model's own claim

Added `_validate_against_source()` to `extraction/extract.py`: after
extraction, any 4-digit year appearing in `amount` or `start_date` is checked
against the actual source text. If the year doesn't appear anywhere in the
real text, the field is discarded (set to empty string) rather than trusted.

**First attempt was too strict and produced a false positive.** An initial
version checked every digit sequence (not just years), which correctly
rejected the fabricated `2023` date but also rejected a **genuinely correct**
date (`2027-07-01`) for National's other policy, because the source spells the
month out as "1 July 2027" — the digits "07" and "01" never literally appear
in a source that writes "July," even though the underlying date is right.
**Fix, narrowed:** check only 4-digit year tokens, not day/month numbers. Every
fabrication actually observed so far has been a wrong year; day/month
reformatting is a legitimate, correct transformation that a naive digit check
punishes for no real safety gain.

### Result: the fix worked against two different fabricated values, not just the one it was built to catch

Confirms this is a real, generalizable validation, not a patch tuned to one
specific wrong answer: the second test run produced a *different* fabricated
date than the first, and the same check caught it without any change.

### First real, validated multi-party corpus

`data/policies.json` now contains four genuinely extracted, validated policies
across three parties (Labour, Te Pāti Māori, National x2), including two
distinct legitimate reasons for `is_costed: false` (an explicit "no cost"
policy, and a real policy whose costing exists only in a linked PDF, not the
crawled HTML) — this is the first real dataset this project has, replacing
every invented placeholder example used earlier in `01_framing.md`.

## Standing lessons, updated after Round 5

8. **Never trust a model's own claim about a fact when the source text is
   available to check it against.** Post-extraction validation against the
   actual source — not just tighter prompts or schema constraints — is what
   caught two separate, differently-worded fabricated dates that better
   instructions alone did not prevent.
9. **A validation check should target the general failure pattern, not the
   specific wrong value observed.** Checking "does this exact string appear"
   would have been too narrow to generalize; checking "does this specific
   *kind* of claim (a year) appear anywhere in context" caught a second,
   different fabrication for free.
10. **`temperature=0` does not guarantee identical output run-to-run** on this
    hosted backend. Design pipelines assuming genuine non-determinism is
    possible even at the most conservative setting, rather than treating a
    single successful run as proof of stability.

---

## Round 6 (17 Sep 2026): two real schema gaps found via Greens and Opportunity

Extending the corpus to Greens and Opportunity surfaced two distinct gaps —
one a genuine schema limitation, one a genuine data-source limitation. Both
addressed rather than left as silent blind spots.

### Gap 1: percentage-of-GDP fiscal commitments (schema gap, fixed)

Opportunity's Healthy People policy commits to lifting health funding to "9%
of GDP" — a real, quantified fiscal claim, but not a dollar figure. The
existing `amount` field (deliberately dollar-only, via its regex) correctly
declined to force this into itself, but the claim was then invisible to
`is_costed` entirely — a real fiscal commitment silently untracked.

**This isn't a minor edge case.** Treasury's own BEFU figures
(`02_data_sources.md`) are themselves stated as %GDP ("OBEGALx deficit 2.4% of
GDP", "net core Crown debt peaks 46.1% of GDP") — so this exact format is what
Fiscal Compare will need to match against baselines later, not a rare
one-off.

**Fix:** added `percentage_target` as its own field, separate from `amount`
(never merged into it — keeping them distinct preserves which kind of figure
is actually being compared downstream). Same discipline as every other field:
`maxLength`, a regex pattern, and a source-text validation check (the number
before the `%` must appear in the real text, or it's discarded as likely
fabricated — same principle as the year-fabrication check from Round 5).
`is_costed` is now `True` if *either* `amount` or `percentage_target` is
non-empty.

### Gap 2: costing that exists only in a linked PDF, not the crawled HTML (data-source gap, partially resolved)

National's "extend to 30 weeks" paid parental leave page links to a PDF fact
sheet that (per third-party reporting) contains the actual costed figures.
The page's own HTML text doesn't state them.

**Attempted resolution:** tried to fetch the PDF directly. **Could not** —
the fetch tool restricts URLs that weren't already surfaced by a prior search
or fetch result, and this asset link fell into that restriction within this
session. **What was recovered instead:** three independent news outlets (NZ
Herald, RNZ, b2bnews) converge on the same year-by-year figures — $27m in
2027/28, $56.6m in 2028/29, $119m in 2029/30. These three years sum to
$202.6m, which does **not** match NZ Herald's separately-reported headline
figure of "$327 million over four years" — implying a fourth year's figure
that none of these three sources actually states. **This discrepancy is
recorded, not resolved** — the real fix needs either a different fetch
mechanism capable of reaching the PDF directly, or a human downloading it
manually the same way NZ First's manual-capture backlog item works. Added to
`07_backlog.md`.

### A third fabrication found while testing the percentage_target fix

The first version of `percentage_target` validation only checked that the
*number* appeared somewhere in the source — not that it was actually attached
to a `%` sign there. This let through two fabrications: Labour's
`"0.8% FTE (minimum)"` (the real text says "0.8 FTE", no `%` anywhere) and Te
Pāti Māori's `"40%"` (fabricated from "40" inside "2040", a year, not a
percentage). **Fix:** require the literal `<number>%` substring in the source
text, not just the bare number.

Testing that fix then surfaced a **fourth**, different fabrication:
Opportunity's `amount` came back as `"$9"` — cross-contaminated from the
correctly-extracted "9% of GDP" into a fabricated dollar figure, in a source
that states no dollar amount at all. This revealed that `amount` had never
had a real content check — only the schema's format regex, which confirms a
string *looks like* a dollar figure without confirming its digits are
grounded in the source. **Fix:** added `_validate_amount_against_source`, the
same literal-substring-in-source check already applied to
`percentage_target`.

**After both fixes, re-running surfaced an honest trade-off rather than a new
bug:** Opportunity's real "9% of GDP" was correctly validated when the model
extracted it, but on a later identical re-run the model simply didn't extract
it at all (no discard warning — the field was empty from the model itself,
not rejected by validation). This is the same temperature=0 non-determinism
documented in Round 5, now observed on a new field. **This is the accepted
trade-off, not a bug to chase further right now**: an honest empty result
when the model misses a real value is preferable to a fabricated-but-plausible
one slipping through — consistent with the project's core rule to state only
what's checkable. A missed real value can be recovered by re-running; a
fabricated one is much harder to catch after the fact.

## Standing lessons, updated after Round 6

11. **A format-valid regex is not a content-grounding check.** `amount`
    passed its schema's dollar-format pattern for months without ever being
    checked against the actual source text — the format check only confirms
    a string *looks like* the right kind of value, not that its specific
    digits are real. Every quantified field needs both.
12. **A validation check needs to verify the exact claimed relationship, not
    just that its parts exist somewhere.** Checking "does this number appear
    anywhere in the source" let two different numbers slip through
    (`0.8` from "0.8 FTE", `40` from "2040") because each number was real —
    just not attached to the thing being claimed about it (a percentage). The
    fix was checking the literal combined pattern (`<number>%`, `$<number>`),
    not the number in isolation.

---

## Round 7 (17 Sep 2026): content-free summaries and garbled script injection

Extending the corpus with Te Pāti Māori's Income policy (correcting an
earlier mis-transcription — see `04_source_profiles.md`) surfaced two more
distinct failure modes.

### Finding: schema field descriptions are weaker than main prompt instructions

`stated_position` twice returned a content-free structural placeholder for
the same list-style source — first "will implement the following measures,"
then (after tightening the schema's field *description*) "will:" — a
different placeholder, same underlying problem. **Tightening a schema
field's description alone did not fix this.** The real fix needed the
instruction moved into the main prompt text itself, with a concrete
good/bad example, plus a dedicated validation check (`_is_placeholder_position`)
that treats a content-free summary as a retry-triggering failure, the same
as a JSON parse error.

### Finding: retrying an identical request at temperature=0 can reproduce an identical wrong answer

Te Pāti Māori's Te Tiriti Entrenchment policy returned the exact string
"Launched today" on three consecutive retries — proving retries are only
useful against random failures, not deterministic ones. **Fix, first
attempt:** nudge temperature up on retries. This worked for unblocking the
stuck output, but introduced a new, worse problem (below). **Fix, final:**
instead of touching temperature, feed the model's own previous bad output
back into the next attempt's prompt as an explicit correction ("you said X,
which is inadequate, don't repeat it"). This gives real signal to diverge
without touching temperature at all.

### Finding: raising temperature caused garbled non-English characters to leak into English text

The temperature-nudge fix above caused CJK characters to appear mid-word in
otherwise-English output (`"without任何"`, `"double基"`, `"from業"`) —
confirmed, not assumed, via a direct isolation test: forcing temperature=0 on
every attempt made the garbling disappear across a full corpus run.
Nemotron-3's documented multilingual support appears to surface at higher
temperatures. This is why the fix above settled on prompt-based correction
rather than a temperature nudge.

### Finding: temperature=0 reduces but does not fully eliminate the garbling

After reverting to temperature=0 on every attempt, a **second run** still
produced one instance of the same CJK leakage (`"through the既有"`) — on a
retry after a JSON parse failure, at temperature=0. This means the earlier
isolation test's conclusion was too strong: temperature=0 is much safer, not
fully safe. **Fix:** added a direct content check (`_contains_unexpected_script`)
scanning `policy_name` and `stated_position` for CJK Unicode ranges, treated
as a retry-triggering failure like everything else — checking the actual
output rather than trusting a generation setting to prevent a problem by
itself. This deliberately checks only CJK scripts, not all non-ASCII
characters, since legitimate te reo Māori macrons (ā, ō, etc.) are ordinary
Latin-extended characters that must not be flagged.

### Result

After all three fixes: all 7 policies extracted cleanly, Te Pāti Māori's
previously-stuck policy now has a real substantive summary, and the "cost of
living" query in Topic-Match correctly matched both genuinely relevant
policies (Te Pāti Māori's Incomes Policy, Greens' Children's Policy) for the
right reason — real content, not a suggestively-named policy title carrying
the match on its own.

## Standing lessons, updated after Round 7

13. **A schema field's `description` carries less instructional weight than
    the main prompt text.** When a description-only fix fails twice on the
    same failure pattern, move the instruction (with a concrete example) into
    the prompt itself rather than continuing to tighten the description.
14. **Retrying an identical request at temperature=0 will reproduce an
    identical wrong answer if the failure is deterministic, not random.**
    A useful retry needs to change something about the request itself (e.g.
    feeding back the specific prior failure as a correction), not just repeat
    it and hope.
15. **Never fix a reliability problem by changing a generation parameter
    without directly testing whether the fix introduces a new problem.** The
    temperature nudge silently traded one failure mode (a stuck placeholder)
    for a worse one (fabricated foreign-language content) — caught only
    because the actual output was checked, not because the fix was assumed
    safe.
16. **A generation-parameter fix (like temperature=0) can reduce a failure's
    frequency without eliminating it.** Don't stop at "the problem didn't
    reappear once" — a direct content check catches what a safer setting
    only makes rarer.

---

## Round 8 (17 Sep 2026): building the real Fetch module

Every corpus entry until now was manually curated by Claude (real text
fetched via Anthropic's own tools, then hand-copied into `build_corpus.py`).
A real pipeline needs this automated — `fetch/fetch.py` was built to do it.

### Finding: Python's RobotFileParser.read() can give a false "disallow"

First version correctly fetched real pages but wrongly reported Labour's
robots.txt as disallowing everything. Root cause: `RobotFileParser.read()`
fetches robots.txt internally via `urllib.request`, using Python's generic
default user agent — a string commonly blocked or challenged by WAFs/CDNs,
independent of whether the site actually disallows crawling. **Fix:** fetch
robots.txt manually with the same working `requests` session and custom user
agent already used for the real page, then hand its text to
`RobotFileParser.parse()` instead of letting it do its own internal fetch.

### Finding: NZ First's robots.txt likely targets named AI crawlers specifically, not bots in general

After the fix above, our Fetch module's generic user agent was **not**
blocked by NZ First's robots.txt — despite Anthropic's own fetch tool being
explicitly disallowed on the identical URL earlier in this project. Most
likely explanation: the site's rule names specific AI crawlers rather than
blocking broadly, and our unbranded script simply isn't recognized by that
rule. **Decision (not a code fix):** do not use this as a way to route around
the block. NZ First stays on manual capture or is skipped, exactly as
originally decided — using a differently-named user agent to bypass a rule
clearly aimed at this kind of use would sit against the project's own
transparency standard.

---

## Round 9 (17 Sep 2026): first fully-automated corpus run, and the CJK check proves itself live

Running `build_corpus.py` fully wired to the real Fetch module for the first
time (no manually-curated text anywhere in the loop) produced 6 of 7
policies successfully, fully automated, end to end.

### Finding: browser-like headers weren't enough to fix National's 404

Adding `Accept`/`Accept-Language` headers (Round 8) did not fix National's
Flexible Parental Leave page returning a 404 to our Fetch module, despite
being confirmed live via a real fetch. This points to protection deeper than
header-level checking — likely TLS fingerprinting or full request-signature
profiling, which a plain `requests`-based client cannot resolve without a
real browser engine. **Decision:** stop iterating on this with header
guesses; backlog it as needing a heavier fetch mechanism (Playwright/Selenium
or a TLS-spoofing client) rather than keep patching blindly.

### The CJK-injection check proved itself in a real, unscripted run

Not a controlled test this time — a normal corpus build run. Two different
policies (Te Pāti Māori's Te Tiriti Entrenchment, National's Paid Parental
Leave extension) both had Chinese characters injected into otherwise-English
text on their first extraction attempt (`独立资源`, `规`, `旧`), and both
were automatically caught and retried until clean, with no manual
intervention. This is the Round 7 fix working exactly as designed under real
conditions, not just in the isolation test that originally validated it.

### Minor, lower-priority cosmetic note

Opportunity's `stated_position` ended with `"v‑v"` — an odd truncation
artifact at the field's `maxLength` boundary, not a CJK match (didn't trigger
the script check) and not a fabrication (no invented content). Noted, not
fixed — cosmetic, cut off mid-word the same way several earlier `start_date`
values were.
