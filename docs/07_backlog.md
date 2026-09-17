# Backlog

Deferred items — things identified as needed but intentionally not actioned yet.
Not a wishlist; only things with a concrete reason they're waiting.

---

## Open

- **NZ First manual content capture** (raised 13 Sep 2026, `04_source_profiles.md`).
  `nzfirst.nz` blocks automated access via robots.txt. Decision made: NZ First
  stays in scope, handled via one-time manual capture (someone visits
  `nzfirst.nz/policy` and each individual announcement page, copies the actual
  content) rather than a live crawl, same treatment as RNZ. **Not yet done.**
  Deferred while extraction schema work proceeds on the six sources that can be
  fetched directly. Must be completed before NZ First can be included in the
  working demo — the extraction pipeline will have nothing to run against for
  this party until this is done.

- **Retry-on-parse-failure logic for the extraction pipeline** (raised 15 Sep
  2026, `08_extraction_schema.md` Round 4). Even at `max_tokens=2000`,
  extraction calls occasionally return truncated/invalid JSON (roughly 1 in 6
  calls observed across testing) — a call-level reliability issue, not a schema
  or prompt problem. The real extraction pipeline (not yet built — currently
  only a test script) needs to retry a call a small number of times when
  `json.loads()` fails, rather than treating one failed call as a permanent
  extraction failure for that policy. **Not yet done** — needed before the
  pipeline runs unattended across all parties' full policy sets.

- **Full agentic system with observability** (raised 15 Sep 2026,
  `09_architecture.md`). Current architecture decision uses a deterministic
  router for the Orchestrator rather than an LLM-based one, deliberately kept
  simple to start (see `09_architecture.md` for the reasoning). Vivek wants to
  come back to a fuller agentic setup later — proper multi-agent orchestration
  with tracing/observability (e.g. logging each sub-agent call, its inputs,
  outputs, latency, and failures in a queryable way) rather than the current
  plain Python logging. **Not yet scoped in detail.** Deferred until the
  simpler deterministic version is working end-to-end and there's a concrete
  reason (real routing failures, or a need to debug production behaviour) to
  justify the added complexity — matches the project's stated principle of not
  over-engineering ahead of actual need.

- **Fetch National's Paid Parental Leave PDF fact sheet directly** (raised 17
  Sep 2026, `08_extraction_schema.md` Round 6). The party's own PDF, linked
  from `national.org.nz/news/paid-parental-leave`, likely contains the actual
  costed figures for the 26-to-30-week extension — but it could not be
  fetched directly in-session (the fetch tool restricts URLs not already
  surfaced by a prior search/fetch result). Three independent news sources
  give partial, non-reconciling figures ($27m/$56.6m/$119m across three years,
  summing to $202.6m, vs. a separately-reported $327m four-year headline
  total). **Not yet resolved** — needs either a different fetch mechanism or
  a manual download, the same pattern as the NZ First backlog item above.
