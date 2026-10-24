# 0007. Remove Sources at the Database Authority, Not the Workflow Layer

Date: 2026-08-30

## Status

Accepted

## Context

The `feeds` table is the authoritative registry of sources: ICS feeds
(`feed_type='ics_url'`) and scrapers (`feed_type='scraper'`), each with a
`status` (`active`, `pending`, `removed`). The tracked `feeds.txt` is a
generated, read-only compatibility layer exported from that table.

In August 2026 the execution authority for scrapers migrated. Before
2026-08-07, scrapers were invoked by explicit lines in
`.github/workflows/generate-calendar.yml`. After `1da6714c7` ("Switch scraper
execution to DB-first"), the workflow scraper lines were deleted and
`scripts/run_scrapers_from_db.py` executes exactly the active `feeds` rows
(`status in ('active','pending')`) for each city.

The Brown County Government regression exposed a hole in that migration.
Timeline:

- **2026-07-17** `71bf04c02` — upstream "Bloomington discovery refresh" adds
  `scrapers/brown_county_gov.py` and a `pending_feeds.txt` entry.
- **2026-08-03** `ce458ba33` — "restore Bloomington discovery scrapers/feeds
  from upstream 71bf04c02" puts Brown County Government back in
  `pending_feeds.txt`.
- **2026-08-04** `6b62f5f5b` — "Process pending feeds into DB": the
  feeds.txt/pending_feeds.txt → `feeds` table migration. `process_pending_feeds.py`
  inserts scraper rows with `status='active'`, so Brown County Government lands
  in the `feeds` table as **active**. `feeds.txt` is regenerated to include it.
- **2026-08-05** `fef80f01f` — "fix(scraper): remove Brown County gov feed".
  This is the deliberate removal. It deletes only the scraper invocation line
  from `generate-calendar.yml` — the execution authority *at that time*. It
  never touches the `feeds` table, so the active DB row survives.
- **2026-08-07** `1da6714c7` — DB-first switch: the workflow is retired and the
  `feeds` table becomes the only execution set. The stale **active** row is
  silently re-enabled.
- **2026-08-08** `522192bf4` — the first CI run under DB-first executes
  `brown_county_gov.py`; "Source: Brown County Government" events reappear in
  the RSS. The scraper runs nightly until the row is finally deleted from the
  DB (~2026-08-31).

Root cause: the removal was recorded at a layer (the workflow YAML) that
ceased to be the authority two days later, and the migration copied *presence*
(active rows) from the old authority without copying *removal intent*. The
block looked correct at the time — and would have been, had the authority not
migrated — but it was never re-applied at the new authority.

## Decision

1. **The `feeds` table is the single authority for source presence *and*
   removal.** Removing a source is a database operation: call the atomic
   `remove_feed(feed_id)` RPC (deletes the source's events and its row in one
   transaction), or set `status='removed'` when archival is wanted. Editing the
   workflow YAML or `feeds.txt` is never sufficient to remove a source, and is
   not a removal.

2. **Additions and removals use the DB-authority tooling.** Additions stage
   through `add_scraper.py` / `add_feed.py` into the `feeds` table; removals go
   through `remove_feed`. `feeds.txt` remains generated and read-only.

3. **Seeding tools treat prior removal intent as removed.** Any process that
   seeds the `feeds` table from another representation (`pending_feeds.txt`,
   `feeds.txt`, a workflow manifest, an upstream sync) must honor a source that
   was deliberately removed at that representation — it must not insert it as
   active. During the migration window the seeding tool only ever inserted and
   had no removal-intent check; that gap is closed by treating the DB as
   authoritative going forward.

## Consequences

**Easier:**
- Removal is a single, atomic, auditable database operation — no second layer
  to keep in sync, no stale-authority resurrection.
- The feed list (`feeds.txt`, UI source list, execution set) always reflects
  the DB, so a removed source stays removed.

**Harder:**
- Removing a source requires a credentialed database caller, not a plain file
  edit. The runbook must point at `remove_feed` (see `supabase/ddl/16_feeds.sql`).
  Since GHSA-69r3-3gxw-fm4g the function also requires an admin identity, so a
  direct SQL session must present one before the call:

  ```sql
  select set_config('request.jwt.claims', '{"sub":"<admin-user-uuid>"}', true);
  select remove_feed(<feed-id>);
  ```

  The Manage Feeds dialog, used while signed in as an admin, needs no such
  preamble.
- Teams with file-only access (forks without DB credentials) cannot remove a
  source locally; they must file the change for a credentialed maintainer.

**Unchanged:**
- `feeds.txt` stays a generated compatibility layer; nobody edits it by hand.
- The fork's intentional divergence (ADR 0002) and sync protocol (ADR 0004) are
  unaffected.

## Alternatives Considered

- **Reinstate a workflow/denylist blocklist as defense-in-depth.** Rejected:
  DB-first execution has no workflow manifest to enforce against, and a
  blocklist would duplicate the DB's authority — creating a second place to
  forget, which is exactly the failure this ADR records.
- **Make `run_scrapers_from_db.py` refuse rows whose scraper file is
  missing.** Doesn't address the case: `brown_county_gov.py` still exists and
  is a legitimate upstream discovery scraper — the *source* was meant to be
  excluded, not the code deleted.
- **Auto-reconcile removal intent during the migration (diff git history for
  deliberately removed sources).** Rejected as a one-time, impractical cost:
  the migration is complete, and the durable fix is DB-authority-only removal.