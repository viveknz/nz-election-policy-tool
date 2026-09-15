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
