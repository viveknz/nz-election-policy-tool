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
