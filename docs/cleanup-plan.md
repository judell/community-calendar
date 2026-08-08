# Cleanup Plan

This note captures the cleanup work needed before handing the new
feeds/scraper mechanism to any downstream fork. The goal is a clean,
repeatable process that gets the main `judell/community-calendar`
instance to the desired end state sanely, with auditability and
without depending on ad hoc fixes in GitHub Actions.

## Desired End State

- `feeds` is the operational source of truth for source status **and
  scraper execution** (DB-first: active scraper rows are the only
  execution set).
- Add, remove, disable, and reconcile are server-owned operations.
- Workflow fallback behavior is temporary, measurable, and removable.
- One audit command can prove the system is clean.
- Builds can be run locally so we can test and reconcile without
  pushing changes first.

## Status as of 2026-08-07, end of day

Switchover steps 1–4 are complete. The five-city soak (santarosa,
asheville, lancaster, raleighdurham, toronto), the Davis
reconciliation, and the first Montclair audit (reports in
`reports/*-2026-08-07-*.md`) brought **all eight surviving cities to
the clean gate**. Four cities (dc-music, newcastleva, petaluma,
tetonvalley) were removed outright, shrinking the migration surface.

Landed after the audit commit (`d66d2487`):

- `87780bc` — `delete_stale_events` guard (live, probe-verified).
- 129 legacy `cmd:`-prefixed scraper commands normalized DB-wide;
  every one of the 368 scraper rows' commands now starts with
  `python ` (verified full-set).
- `6355b2f` — insert-time scraper-row validation trigger (live,
  probe-verified: junk insert refused, all 350 active rows pass).
- `a135e16` — atomic `remove_feed` (live, probe-verified: events +
  row in one transaction, counts returned, unknown id raises).
- Montclair fixes: `montclair_film.py` rewritten for the site
  redesign (50 screenings recovered), Montclair Foundation converted
  to `tribe_rest` (114 events), one dead Meetup feed retired, Temple
  Ner Tamid + YWCA converted preemptively (SiteGround pattern).
- `a70bd88` — DB-first scraper runner
  (`scripts/run_scrapers_from_db.py` + `local_build.py --db-first`)
  with the eight-city parity proof
  (`reports/db-first-parity-2026-08-07.md`): static ALL-MATCH on all
  350 commands, dynamic 8/8 clean builds, fallback telemetry loud,
  counted, and failure-inducing on a credentialed run.

City clean-gate scoreboard (final `--sync-existing --dry-run` results):

| City | Status |
|---|---|
| bloomington | clean (70/70) |
| santarosa | clean (64/64) |
| toronto | clean (84/84) |
| asheville | clean (43/43) |
| lancaster | clean (30/30) |
| raleighdurham | clean (22/22) |
| davis | clean (8/8) — Chamber row retired, names reconciled |
| montclair | clean (29/29) — first audit + fixes complete |

## Cleanup Items

1. **Add a full dry-run reconciler** — **DONE.**
   `scripts/local_build.py` (per-city audit: workflow manifest, DB
   rows, exported `feeds.txt`, output paths, actual outputs) plus
   `scripts/backfill_scraper_feeds.py --sync-existing --dry-run`
   (classified insert/update/retire plan). Mismatches are classified,
   not dumped.

2. **Define mismatch classes explicitly** — **DONE.**
   Drift types (`scraper_name_mismatch`, `scraper_command_mismatch`,
   `workflow_scraper_missing_from_db`, `db_scraper_missing_from_workflow`,
   `removed_db_scraper_still_in_workflow`), registration notes
   (`legacy_url_keyed_scraper_row`, `live_feed_filename_collision`),
   output classes (`missing` / `not_ics` / `no_events` / `ok` with
   `content_kind` sniffing), and weak-name-skip reporting.

3. **Add a reconcile/apply mode** — **DONE.**
   `--sync-existing` write form, with name-provenance safety
   (filename-derived fallbacks never overwrite DB names) proven
   against the santarosa weak-name clobber class.

4. **Normalize scraper command storage** — **DONE.**
   One-time DB-wide normalization stripped all 129 legacy `cmd:`
   prefixes (0 remain; all 368 scraper commands start with
   `python `), and the `feeds_validate_scraper_row` trigger
   (`6355b2f`, live) rejects malformed rows — http-keyed urls, empty
   commands, non-`python scrapers|scripts/` commands — on every
   write path at once. Removed-status tombstones exempt.

5. **Make feed removal atomic** — **DONE.**
   `remove_feed` (`a135e16`, live) deletes the feed's events and its
   row in one transaction, returns the counts, and raises for an
   unknown id. Backward compatible with callers that still
   pre-delete events.

6. **Make scraper removal atomic** — **DONE.** Same RPC (feeds rows
   of every type go through it).

7. **Make add operations durable** — **PARTIAL.**
   The insert-time trigger now blocks malformed adds on every path,
   which was the DB-first-blocking half. Consolidating the add paths
   themselves (`pending_feeds.txt` / `add_scraper.py` / Manage
   Feeds) into one canonical flow remains post-switch work.

8. **Choose the final execution source of truth** — **DECIDED: DB-first.**
   Active DB scraper rows become the only execution set. The first
   attempt (`0fc14a1e3`..`54a1ffc6f`) was rolled back by `f5623cc7e`
   because the data wasn't trustworthy yet; the city-by-city clean
   pass above was the remedy. See the switchover sequence below.

9. **Measure and expose fallback usage** — **DONE.**
   The DB-first runner logs `[db-first] fallback=feeds.txt
   reason=...`, counts fallbacks in the audit report
   (`db_first_fallbacks`), and a fallback on a credentialed
   `--db-first` run fails the build. The fallback exists solely for
   forks without database credentials; `feeds.txt` itself remains a
   generated, read-only, human-readable reference for what the
   database canonically drives.

10. **Handle static ICS sources explicitly** — **DONE for audited cities.**
    The soak retired the orphan class (`new_world_ballet.ics`, the
    URL-keyed North Bay Derby row, toronto's 14 legacy rows); the
    audit runner now flags orphans as they appear.

11. **Add validator coverage for the new mechanism** — **PARTIAL.**
    Local validation fails on unusable commands surfaced by the
    audit, `not_ics` outputs, missing outputs, and removed-rows-
    still-running; insert-time validation is now enforced DB-side
    (4). Remaining: CI-side coverage of the DB-first runner once it
    exists.

12. **Improve pipeline reporting** — **DONE.**
    Structured per-city report: failures (with RUN/EXIT-scoped
    attribution), missing / zero-event / non-ICS outputs, drift,
    notes, action report (fix/review/retire buckets).

13. **Harden the Manage Feeds UX** — **NOT DONE.**
    Depends on 5/6 (atomic server ops) so the dialog can report one
    truthful outcome.

14. **Support local build runs** — **DONE.**
    `scripts/local_build.py` + `docs/local-build.md`; proven across
    eight cities including local-vs-CI parity comparisons.

15. **Create a clean-state runbook** — **NOT DONE.**
    Write after the DB-first switch so it documents the real
    operations, not the transitional ones.

16. **Define the pre-handoff gate** — **UNCHANGED.**
    Reconciler clean, no malformed rows, no orphans, no fallback in
    normal builds, atomic add/remove, runbook matches reality.

17. **Document the migration cutoff** — **NOT DONE.**
    Declare forbidden legacy paths once DB-first is stable; the
    fallback telemetry (9) supplies the evidence for retirement.

## Switchover Sequence (to DB-first, scrapers out of the workflow)

Ordered so every intermediate piece lands before the switch itself.
Steps 1–4 completed 2026-08-07.

1. **Finish the city clean gates.** — **DONE** (all eight cities;
   see scoreboard above; Davis reconciliation and first Montclair
   audit in `reports/davis-2026-08-07-reconcile.md` and
   `reports/montclair-2026-08-07-soak.md`).

2. **Land `guard_delete_stale_events`.** — **DONE** (`87780bc`,
   live and probe-verified against davis).

3. **One-time command normalization + insert-time validation.** —
   **DONE** (DB-wide normalization + `feeds_validate_scraper_row`
   trigger, `6355b2f`).

4. **Atomic server-owned remove.** — **DONE** (`a135e16`). The
   durable-add consolidation half of item 7 is deliberately deferred
   to post-switch; the validation trigger covers the risk that
   blocked DB-first.

5. **Reintroduce the DB-first runner, hardened** (items 8–9). —
   **DONE** (`a70bd88`; parity proof in
   `reports/db-first-parity-2026-08-07.md`).
   Execution set = active DB scraper rows only. Feeds.txt/manifest
   fallback allowed only as an explicit, logged, counted migration
   path with a retirement date. Prove parity locally first: run each
   city DB-first and diff against the workflow-driven outputs from
   the same day.

6. **Switch the workflow and delete the scraper lines.** — **NEXT**
   (proposed as worklist item `switch-workflow-to-db-first`).
   Replace every per-city scrape block with one "run scrapers from
   DB" step. The workflow keeps only checkout, deps, the DB-first
   runner, combine/convert/RSS/validate/report, and upload. The same
   item must retire the workflow-as-authority premise in the tooling:
   `backfill_scraper_feeds.py --sync-existing` would otherwise read
   an empty workflow manifest as "retire all 350 rows", and
   `local_build.py`'s workflow mode and drift comparison lose their
   subject — both need guards/removal in the same change.

7. **Verify, then codify.**
   A full CI run per city agrees with the local DB-first run; then
   write the runbook (15) and the migration cutoff (17), and check
   the pre-handoff gate (16).
