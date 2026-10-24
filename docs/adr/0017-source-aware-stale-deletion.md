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
  failure, and repeated empty runs do not clean them. `remove_feed` clears a
  survivor the retiring feed owns via `feeds.source_ids` (see the 2026-10-21
  amendment below).
- A source whose *entire* output is merged into another source's survivors has
  no `source_id` in the payload, so its old rows can linger as duplicates. The
  condition self-heals only if the source later emits a non-merged event; a
  source that always duplicates a primary (typically an aggregator) keeps those
  rows indefinitely. Accepted for now — the dropped member of a merge is the
  lower-priority copy, and cleaning orphaned members is a follow-up, not part of
  this change.
- Rows with a NULL `source_id` belong to no source and are never swept when
  `p_sources` is set.

## Amendment 2026-10-21 (#232)

`feeds.source_ids text[]` records every `.ics` stem the feed's build has
produced: `download_feeds.py` for `ics_url`/`curator` rows, and
`run_scrapers_from_db.py` for scraper rows. It is a history because a feed's
URL can change, and rows built under an older stem must stay attributable.

`remove_feed` deletes rows whose `source_id` is in that history, so it clears a
merge survivor the retiring feed owns. A survivor owned by another feed stays,
because its `source_id` names that feed, and so do its saved picks. The
exact-name arm remains for rows built before the mapping existed, and it skips
rows that another same-city feed's history owns. An empty history also raises a
WARNING.

There is no backfill: the mapping fills on the next build. In that window the
name arm still deletes a feed's plain rows, but not a survivor the feed owns,
whose `source` is the comma-joined list — a survivor can outlive its owner
until that feed completes one build.

A stem is an exclusive identity only while one feed claims it. Two same-city
feeds can produce the same stem: Bloomington's two `events.in.gov` rows both
slug to `events_search_events_ics`, because the general slug drops the query
string. `remove_feed` keeps rows that carry a stem another same-city feed also
claims, and warns. Those rows stay until the feeds are disambiguated.

`record_feed_source` appends server-side instead of writing a whole array, so
two overlapping builds — the workflow has no concurrency group — cannot erase
each other's stems.

Retiring the owner of a survivor deletes the survivor even when another member
feed still lists the event. The next build recreates that event under a new row
id, and picks saved on the old row are gone with it. The alternative — keeping
a survivor whose owner is gone — leaves a duplicate that the source-aware sweep
cannot clear, because the retiring feed's `source_id` is no longer in the
payload.

## Amendment 2026-10-23 (#240)

The `events.in.gov` pair was not two sources. The two URLs serve the same
Monroe County Government calendar with identical UIDs, and
`browse_type=school` filters nothing, so the mislabeled duplicate was retired
instead of the slug being disambiguated. The row is a `status='removed'`
tombstone, so the URL cannot return as a new feed and recreate the collision.

The guard stays: a shared stem still identifies neither feed, and
`download_feeds.py` now exits non-zero when two feeds in one city would write
the same `.ics` file, so a feed added through Manage Feeds fails the build
instead of overwriting another source's calendar. `tests/test_feed_slug.py`
also fails when two same-city entries in `feeds.txt` or `pending_feeds.txt`
produce one stem, which catches the pair at PR time.

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

## Amendment 2026-10-22 (#233)

The sweep no longer infers its scope from the payload. Each runner appends the
stem of every source whose ingestion succeeded — a scraper that exits 0 and
leaves a parseable calendar, or a feed fetch that returns a valid ICS body — to
`cities/<city>/ran_sources.txt`. The workflow sends that list to `load-events`
as `ran_sources`, and `load-events` passes it as `p_sources`. A source that ran
and emptied is swept; a source that failed keeps its rows. An absent field falls
back to payload presence (the pre-#233 behavior), and an empty array sweeps
nothing.

This supersedes the per-source guard paragraph under Decision. The 50% check
now raises a WARNING and the sweep proceeds: the manifest is the authority on
which sources ran, so a shrinking source is either real churn or a truncated run
that exited 0, and this layer cannot tell them apart. The aggregate guard on the
legacy `p_sources IS NULL` path is unchanged.

Consequences that remain:

- An all-quiet city never reaches the upload, because `validate_city` treats an
  empty `combined.ics` as an error. Its sources are ran, but the loader never
  runs.
- A per-file `combine_ics` exception prints an error and contributes zero events,
  so a healthy source looks quiet and is swept. The 50% check warns, but the
  notice lands in the Postgres log, not the Actions log (#231).
- A feed whose URL changes gets a new stem in the manifest; rows under the old
  stem stay unswept, exactly as before.

## Amendment 2026-10-23 (#243)

The accepted cost that "a source that runs successfully but has zero upcoming
events is indistinguishable from a failed one" now applies only to scrapers
that have not migrated to the source-reached declaration. `BaseScraper.run()`
fails a scraper that returns no events without declaring it reached its source
(ADR 0018), so a migrated quiet source exits 0 and is swept while an outage
exits non-zero and keeps its rows.
