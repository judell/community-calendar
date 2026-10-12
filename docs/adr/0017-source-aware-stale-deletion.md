# 0017. Source-Aware Stale Deletion

Date: 2026-10-11

## Status

Accepted

## Context

`load-events` upserts a city's payload by `source_uid`, then calls
`delete_stale_events(p_city, p_source_uids)` to remove rows the build no longer
lists. The sweep deleted *every* city row whose `source_uid` was absent from the
incoming list. That is correct only while the payload contains an entry for
every source that exists.

It does not. A feed that 404s or a scraper that crashes contributes nothing to
`combined.ics`, so it contributes nothing to `events.json` and nothing to the
payload — and the sweep treated that silence exactly like a valid-empty
calendar, deleting the source's previously built events. Raising inside a
scraper (the fix in #219/#226) made the failure loud and attributable but could
not preserve the rows, because the destructive step runs later and elsewhere.

## Decision

**Scope the sweep to the sources present in the payload.**
`delete_stale_events` gains a third argument `p_sources text[]`, the set of
`source_id`s carried by the incoming events. Only rows whose `source_id` is in
that set are eligible for deletion; a source absent from the payload is left
untouched. `load-events` derives `p_sources` from the payload in both of its
paths (direct POST and the GitHub fallback) and always passes it.

`source_id` is the identity, not `source`: it is the ICS filename stem, stable
and unique per feed/scraper, whereas the display `source` becomes a comma-joined
aggregate after a merge and can itself contain commas.

`p_sources DEFAULT NULL` preserves the old whole-city behavior for a caller that
has not been updated, and the two-argument pgTAP calls document the legacy path.
Because `CREATE OR REPLACE` cannot change an argument list (it overloads instead
of replacing), the migration drops the two-argument function first.

The 50% partial-load guard is evaluated per present source, so a healthy
source's uid count cannot mask a truncated one. A source that would lose more
than half its rows is preserved and the rest are swept, with a WARNING naming
it; one source winding down (a festival, a semester) therefore cannot block
cleanup for the whole city. The cost is that such a source keeps its rows,
including any that were genuinely removed, until it stops tripping the guard.
The guard reads each source's current row count, so the caller must upsert the
payload before the sweep (`load-events` does).

## Consequences

**Easier:**
- A failed source keeps its events; the pipeline no longer needs a scraper-level
  workaround to preserve them.
- The partial-load accident is structurally contained: a short payload can only
  sweep the sources it actually names.

**Harder / surprising:**
- A source that runs successfully but has zero upcoming events is
  indistinguishable from a failed one, so its rows are preserved until its next
  non-empty run. The preserved rows are not necessarily past: if a source
  removed or cancelled its future events, those rows stay and remain visible as
  upcoming. This is the deliberate cost of never deleting on a transient
  failure, and repeated empty runs do not clean them. `remove_feed` deletes
  only rows whose `source` equals the feed's name, so it leaves a merge survivor
  (whose `source` is the comma-joined member names) for the next build to
  re-attribute; matching the survivor by name would delete an event owned by
  another feed and cascade away its saved picks. Clearing a survivor when its
  own feed is retired needs a durable feed-to-`source_id` mapping and is a
  follow-up.
- A source whose *entire* output is merged into another source's survivors has
  no `source_id` in the payload, so its old rows can linger as duplicates. The
  condition self-heals only if the source later emits a non-merged event; a
  source that always duplicates a primary (typically an aggregator) keeps those
  rows indefinitely. Accepted for now — the dropped member of a merge is the
  lower-priority copy, and cleaning orphaned members is a follow-up, not part of
  this change.
- Rows with a NULL `source_id` belong to no source and are never swept when
  `p_sources` is set.

## Alternatives Considered

- **Block the whole city upload on any scraper failure.** Rejected in #226: one
  flaky scraper would freeze an entire city for the run.
- **Have the pipeline emit a manifest of sources that ran successfully.**
  Correctly distinguishes "failed" from "ran empty", but requires plumbing
  through `run_scrapers_from_db.py`, `download_feeds.py`, the workflow, and the
  edge function. Deferred until the stale-empty-source cost justifies it.
- **Match on `source_names` (the route's structured name array).** Handles the
  merged-away-source case, but names can be slug fallbacks and the predicate
  becomes an array intersection. Rejected in favor of the stable `source_id`.
