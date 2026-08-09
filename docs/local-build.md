# Local Build

Use `scripts/local_build.py` to run the relevant calendar build pipeline
locally for one city or all cities and produce a structured audit report.

This is intended for cleanup and migration work where we need to inspect:

- scraper failures
- missing outputs and zero-event inventory
- DB/workflow drift
- live feed download problems
- validation failures
- build-log errors worth triaging

It is designed to be **read-only against upstream state**. It does **not**
process `pending_feeds.txt` into the DB, mark feeds active, upload events,
or refresh Supabase-side materialized state.

## Prerequisites

- `python3`
- project dependencies already installed (`pip install -r requirements.txt`)
- optional but recommended for DB-backed comparison/export:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `TICKETMASTER_API_KEY` for cities that use Ticketmaster scrapers

Without DB credentials, the runner still works, but it falls back to the
tracked `feeds.txt` files and cannot report DB/workflow drift.

The runner auto-loads a repo-local `.env` file if present, without overriding
already-exported variables.

For close GitHub parity, use the same runtime family as the workflow:

- GitHub Actions runs `python-version: 3.10`
- the repo currently pins `lxml==4.9.1`
- that `lxml` pin does not build cleanly on Python 3.13/3.14, so a modern
  Homebrew `python3` can produce unavoidable local drift before the build even
  starts

If you need local-vs-GitHub reconciliation, treat Python 3.10 plus a clean
`pip install -r requirements.txt` environment as part of the test setup, not
as an optional nice-to-have.

## Usage

Run one city:

```bash
python3 scripts/local_build.py --city santarosa
```

Run several cities:

```bash
python3 scripts/local_build.py --cities santarosa,bloomington
```

Run all cities:

```bash
python3 scripts/local_build.py --all
```

Set the scraper horizon:

```bash
python3 scripts/local_build.py --city santarosa --months 2
```

Keep the DB-exported `feeds.txt` files instead of restoring tracked copies:

```bash
python3 scripts/local_build.py --city santarosa --keep-db-export
```

## DB-first execution (the default)

Since the workflow switch (`switch-workflow-to-db-first`), scraper
execution is DB-first everywhere: the GitHub workflow's single "Run
scrapers from DB" step and `local_build.py`'s default scraper phase both
execute the active `feeds`-table rows as the only execution set. The
workflow carries no per-scraper lines; adding or removing a scraper is a
database operation.

`scripts/run_scrapers_from_db.py` is the runner. It can run standalone
(`--city`, `--list` to preview the execution set) or supply the scraper
phase of `local_build.py`, where the full audit/report/validation
machinery measures the build unchanged.

`--workflow-mode` remains as a legacy escape hatch that executes from
the workflow manifest — only meaningful on historical checkouts or forks
whose workflows still carry scraper lines. For the same reason, the
audit's workflow/DB drift comparison runs only when a workflow scraper
manifest actually exists (`drift_skipped` is reported otherwise), and
`backfill_scraper_feeds.py --sync-existing` refuses to plan against an
empty manifest rather than reading it as a mass retirement.

Rows whose stored command lacks an output flag get `--output <row.url>`
appended; each run is bracketed with the same `RUN`/`EXIT` log lines the
build-log error attribution parses.

**`feeds.txt` is a generated, read-only artifact.** It keeps its two
sections (direct ICS feeds and scrapers) and exists as a human-readable
reference for what the database canonically drives — it is never edited
by hand and never an execution authority. The only executable use is
the runner's explicit fallback for forks without database credentials:
fallback use is logged (`[db-first] fallback=feeds.txt reason=...`),
counted in the audit report (`db_first_fallbacks`), and in `--db-first`
mode a fallback on a credentialed instance fails the run — the DB was
not actually driving execution.

The audit report's per-city `execution` object records the mode
(`db` / `feeds.txt-fallback` / `workflow`), the row count, and any
fallback reason.

**The tracked `rss/` directory is CI-owned published state** — GitHub
Pages serves it as the live feed URLs, and each build's `-latest.xml`
is diffed against the previously committed full feed. Local runs never
write it: the runner sends RSS output to a per-run temp directory
(recorded as `rss.outdir` in the audit report) while still reading the
tracked feeds as the diff baseline via `generate_rss.py --state-dir`.

**`cities/<city>/geo_filtered.json` is likewise CI-owned generated
state** (committed by the nightly metadata step, read into the feed
health report). Local runs write the sidecar to a per-run temp path
(recorded as `combine.geo_report` in the audit report) via
`combine_ics.py --geo-report`; the local feed report's geo section
therefore reflects the tracked baseline, not the local run.

## What It Runs

For each selected city, the runner:

1. reads the workflow scraper manifest from
   `.github/workflows/generate-calendar.yml`
2. queries live `feeds` metadata when DB credentials are available
3. temporarily writes a DB-backed `feeds.txt` snapshot for local use, then
   restores the tracked file unless `--keep-db-export` is used
4. cleans known generated outputs for the selected city
5. runs workflow-first scraper commands locally
6. runs `download_feeds.py` in fallback mode against the temporary
   `feeds.txt` snapshot so no feed status is mutated upstream
7. runs `combine_ics.py`
8. runs `ics_to_json.py`
9. runs `generate_rss.py`
10. runs `validate_pipeline.py` logic in-process
11. runs `report.py` logic to produce a local feed health report

## Outputs

By default the runner writes:

- `local-build.log` — raw build log
- `local-build-report.json` — structured audit report
- `local-feed-report.json` — feed-health report based on the local run
- `local-validation-report.json` — machine-readable validation summary

## Audit Report Contents

`local-build-report.json` summarizes:

- runtime metadata and compatibility warnings
- `.env` keys loaded automatically by the runner
- per-city scraper command results
- per-scraper logged errors and warnings from the build log
- per-city live-feed download results
- missing outputs
- zero-event outputs reported separately as informational inventory
- non-ICS outputs (`status: not_ics`) — files that exist but contain no
  `BEGIN:VCALENDAR`, typically 403 block pages, HTML error pages, or JSON
  error bodies saved with an `.ics` extension; a `content_kind` field
  (`html`, `json`, `empty`, `unknown`) hints at what came back. These are
  broken sources, not quiet ones, and are kept out of the zero-event queue
- workflow/DB scraper drift
- per-city registration notes (`legacy_url_keyed_scraper_row` for DB scraper
  rows keyed by an http(s) URL instead of an output path, and
  `live_feed_filename_collision` for live feeds whose slugified download
  filename would overwrite a workflow scraper's output — such feeds are
  excluded from the temporary snapshot to protect scraped events)
- per-city action report grouped into `fix`, `review`, and `retire`
- pending `pending_feeds.txt` entries
- validation results
- parsed build-log issues

Drift is computed after the build, from freshly re-derived workflow rows, so
display-name derivation can read each output's `X-SOURCE` header. Workflow
names that fall back to filename derivation (missing output, no `X-SOURCE`)
are treated as too weak to count as name drift; the same rule makes
`backfill_scraper_feeds.py --sync-existing` skip name updates that would
overwrite an existing DB name with a filename-derived fallback (reported as
weak-name skips in its output).

Build-log issues inside a scraper's `RUN ... EXIT` bracket are attributed to
that specific source's display name, so several sources sharing one scraper
script (for example multiple publishers running `eventbrite_filtered.py`) no
longer each inherit every sibling's errors.

Current scraper drift classes include:

- `scraper_name_mismatch`
- `workflow_scraper_missing_from_db`
- `db_scraper_missing_from_workflow`
- `removed_db_scraper_still_in_workflow`
- `scraper_command_mismatch`

Command failures are also classified when possible, for example:

- `arg_error`
- `http_error`
- `timeout`
- `connection_error`
- `traceback`

## Exit Status

The runner exits non-zero if it sees any of:

- validation errors
- scraper command failures
- missing scraper outputs
- non-ICS scraper outputs
- missing live-feed outputs
- non-ICS live-feed outputs
- parsed build-log errors

Warnings, drift items, and zero-event outputs are still reported in JSON even when they do not
independently force the exit code.

Workflow scrapers that exit `0` but produce zero events are now surfaced
separately from empty live ICS feeds. That makes it easier to distinguish
"source might simply be quiet today" from "scraper likely degraded but did
not crash."

Runtime mismatches are reported in the audit summary but do not independently
force a non-zero exit code. They are parity warnings, not pipeline failures.

The action report is the fastest way to answer "what do we fix now?" after a
city run:

- `fix` means the run found a concrete pipeline inconsistency or missing output
- `review` means the source was quiet or warning-level and should be checked
  before changing pipeline state
- `retire` is reserved for sources the current configuration already marks as
  removed but that still remain wired into execution

## Notes

- This is a cleanup tool, not a production deploy path.
- It intentionally stops short of upload/refresh steps that would mutate
  upstream state.
- If DB credentials are available, it uses the live `feeds` table only for
  comparison and temporary local export.
- If a local run shows a source that should be retired, fix the source
  registration separately; the runner is diagnostic, not authoritative.
