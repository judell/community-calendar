---
report_id: lancaster-2026-08-07-soak
title: Lancaster local/upstream parity audit and DB drift soak
city: lancaster
date: 2026-08-07
commit: 81200105484254a68c053aaabcde79723e820137
overall_status: partial
summary:
  total_checks: 6
  passed: 2
  failed: 0
  warning: 4
findings:
  - id: F001
    status: pass
    title: The Python 3.10 local audit run completed with zero hard failures
    scope: lancaster local audit
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.log
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-validation.json
    action_ids: []
  - id: F002
    status: pass
    title: Local and same-day upstream Lancaster builds converge on the same source-health picture
    scope: lancaster local-vs-upstream comparison
    evidence:
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504.log
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.log
    action_ids: [A005]
  - id: F003
    status: warning
    title: Three scraper rows have workflow/DB metadata drift, one of which stores a scraper command that would fail if executed
    scope: lancaster scraper registration
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-backfill-dryrun.log
      - type: repo-file
        ref: scrapers/sidearm.py
    action_ids: [A001]
  - id: F004
    status: warning
    title: Four venues run duplicate Songkick and Ticketmaster producers, two of which double-count live events
    scope: lancaster source registration
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.log
      - type: repo-file
        ref: .github/workflows/generate-calendar.yml
    action_ids: [A002]
  - id: F005
    status: warning
    title: Ten scraper outputs and eighteen live feeds produced zero future events without hard errors, in the same pattern locally and upstream
    scope: lancaster source health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504.log
    action_ids: [A003, A004]
  - id: F006
    status: warning
    title: Zero DB-only or workflow-only scraper rows exist, so the sync-existing dry run proposes updates only, no inserts or retirements
    scope: lancaster DB/workflow parity
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-backfill-dryrun.log
    action_ids: [A001]
actions:
  - id: A001
    status: done
    title: Apply the three dry-run-confirmed scraper metadata updates (Penn Medicine Park name, F&M Athletics command, Lancaster Catholic name) with --sync-existing (no --dry-run), scoped to lancaster
    owner: agent
  - id: A002
    status: done
    title: "Decide which producer to keep for the four dual-represented venues. Adjudicated 2026-08-07: Chameleon Club retired on both producers (venue closed permanently in 2020, building sold — workflow lines removed, DB rows marked removed); Freedom Hall, Tellus 360, and Phantom Power keep both producers by decision (active venues, dedup reconciles overlap)"
    owner: human+agent
  - id: A003
    status: open
    title: Review the ten zero-event scraper outputs individually and decide fix/watch/retire per source
    owner: human+agent
  - id: A004
    status: open
    title: Review the eighteen zero-event live feeds and the seven-file empty-ICS validation warning
    owner: human+agent
  - id: A005
    status: open
    title: Re-run the upstream/local comparison after A001-A004 land to confirm the clean gate for Lancaster
    owner: agent
artifacts:
  - label: Local build report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.json
  - label: Local build log
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.log
  - label: Local feed report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-feeds.json
  - label: Local validation report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-validation.json
  - label: backfill_scraper_feeds.py --sync-existing --dry-run output
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-backfill-dryrun.log
  - label: Upstream Lancaster run (scheduled, success)
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
  - label: Upstream job log
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504.log
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Local audit health | pass | `0` scraper failures, `0` missing outputs, `0` validation errors, `0` build/runtime issues. |
| Local-vs-upstream parity | pass | Same-day upstream run agrees on the same 10 zero-event scrapers and the same class of empty-ICS warning; aggregate counts differ by roughly 1%, consistent with live-source drift between the two run times. |
| DB/workflow drift | warning | `3` scraper rows need a metadata sync; `0` are missing from the DB and `0` are orphaned DB-only rows. |
| Broken DB-stored command | warning | The DB's F&M Athletics command uses `--url`, a flag `scrapers/sidearm.py` no longer accepts (`--base-url` is required); it would fail if executed as stored. |
| Duplicate producers | warning | Four venues (Tellus 360, Chameleon Club, Freedom Hall, Phantom Power) are scraped by both `songkick.py` and `ticketmaster.py`; two currently double-report live events, relying on cross-source dedup to reconcile. |
| Zero-event review queue | warning | `10` zero-event scraper outputs and `18` zero-event live feeds, plus one validation warning naming 7 empty ICS files, need source-by-source review before any retirement. |

# Findings

## F001 The Python 3.10 local audit run completed with zero hard failures

Using `/tmp/community-calendar-audit-venv310/bin/python` (3.10.20, `requests`/`icalendar`/`lxml` all import cleanly), `scripts/local_build.py --city lancaster` ran end to end:

- `0` scraper failures
- `0` missing scraper outputs
- `0` missing live-feed outputs
- `0` build-log errors/warnings
- `0` runtime errors/warnings
- Validation: `0` errors, `1` warning (7 empty ICS files)

`combined.ics` had `2516` unique future events (`Cross-source dedup: removed 148 duplicate events`, `Geo-filtered 81 events outside allowed cities`); `events.json` converted the same `2516`; `generate_rss.py` produced `full=2240 latest=100`.

## F002 Local and same-day upstream Lancaster builds converge on the same source-health picture

The most recent successful `generate-calendar.yml` run (`31142208913`, scheduled, completed `2026-08-07T03:33:33Z`) scraped Lancaster with no errors or warnings in its "Scrape Lancaster sources" step. Its Lancaster combine/convert/RSS/validate numbers:

- `combined.ics`: `2485` unique future events (`Cross-source dedup: removed 155`, `Geo-filtered 78`)
- `events.json`: `2485`
- RSS: `full=2194 latest=100`
- Validation: `⚠️ [WARNING] lancaster: 7 empty ICS files` (`0` errors)
- Upload: `{"success":true,"inserted":2485,"deleted":160}`

Local numbers (`2516`/`2516`/`2240`/`1` warning) are within about 1% of upstream, and both runs flag the identical set of 10 zero-event scraper outputs (see F005). The gap is consistent with live-source churn between the upstream 03:07 UTC scrape and the local ~19:36 UTC scrape, not a workflow/DB or code-path divergence.

## F003 Three scraper rows have workflow/DB metadata drift, one of which stores a scraper command that would fail if executed

`backfill_scraper_feeds.py --city lancaster --sync-existing --dry-run` reported `32` workflow rows, `32` existing DB rows, `0` missing, `0` to retire, `3` to update — the same three items the local audit's `drift` array independently flagged:

```
UPDATE lancaster: Penn Medicine Park [cities/lancaster/tm_penn_medicine_park.ics] -> {"name": "Penn Medicine Park"}
UPDATE lancaster: F&M Athletics [cities/lancaster/fandm_athletics.ics] -> {"scraper_cmd": "python scrapers/sidearm.py --base-url \"https://godiplomats.com\" --name \"F&M Athletics\" --home-only -o cities/lancaster/fandm_athletics.ics"}
UPDATE lancaster: Lancaster Catholic [cities/lancaster/maxpreps_lancaster_catholic.ics] -> {"name": "Lancaster Catholic"}
```

Penn Medicine Park and Lancaster Catholic are cosmetic: the DB display name (`"Ticketmaster"`, `"High school athletics (MaxPreps)"`) is a generic scraper-type label instead of the workflow's specific venue/school name — command/name-drift class, no functional risk.

F&M Athletics is not cosmetic. The DB command is `python scrapers/sidearm.py --url https://godiplomats.com --name 'F&M Athletics'`, but `scrapers/sidearm.py` (line 312) only defines `--base-url` as its required URL flag — `--url` is not recognized. The DB-stored command would error on `--base-url: required` if it were ever executed as-is, and it also silently drops the workflow's `--home-only` scope flag. This is a stronger case than ordinary display-name drift: it is a malformed/unusable stored command, the exact condition the clean-gate checklist calls out ("no malformed active scraper rows or unusable commands").

## F004 Four venues run duplicate Songkick and Ticketmaster producers, two of which double-count live events

Cross-referencing the workflow block against the local build log shows four Lancaster venues wired to both a `songkick.py` scraper and a `ticketmaster.py` scraper for the same physical venue:

| Venue | Songkick events (local) | Ticketmaster events (local) |
| --- | --- | --- |
| Tellus 360 | 4 | 5 |
| Chameleon Club | 0 | 0 |
| Freedom Hall | 0 (1 raw, filtered to 0) | 0 |
| Phantom Power | 5 | 3 |

Tellus 360 and Phantom Power actively produce overlapping events from both producers today; the pipeline's cross-source dedup (148 duplicates removed locally, 155 upstream) is absorbing the overlap rather than the source registration reflecting one canonical producer per venue. This is the same "duplicate producers" class documented for Bloomington's Bluebird venue (Songkick vs. first-party producer) — here it is Songkick vs. Ticketmaster. Chameleon Club and Freedom Hall are currently zero on both producers (see F005), so consolidating those two costs nothing operationally right now; Tellus 360 and Phantom Power need a judgment call on which producer is more reliable before retiring the other.

## F005 Ten scraper outputs and eighteen live feeds produced zero future events without hard errors, in the same pattern locally and upstream

Zero-event scraper outputs (identical set in both the local run and the upstream `31142208913` run, no scraper errors or exceptions in either):

- Tellus360 - The Temple (Songkick)
- Chameleon Club (Songkick)
- Freedom Hall (Songkick)
- The Village (Songkick)
- Lancaster Dispensing Co. (Songkick)
- Penn Medicine Park (Ticketmaster)
- Fulton Opera House (Ticketmaster)
- Freedom Hall (Ticketmaster)
- Chameleon Club (Ticketmaster)
- Lampeter-Strasburg (MaxPreps)

Zero-event live feeds (local run; `18` total, `7` overlap with the validation warning's empty-ICS list): Candy Is Sweet, Lancaster Trust, Meetup: Central PA Open Source Conference, Meetup: GAME Lancaster, Meetup: Lancaster Craft Club, Meetup: Lancaster Elastic User Group, Meetup: Lancaster Guided Meditation, Meetup: Lancaster Nature & Culture Photography, Meetup: Lancaster Photography, Meetup: Lancaster Sierra Club, Meetup: Lancaster Social, Meetup: Lancaster Young Adults, Meetup: Level Up Lancaster, Meetup: Mental Health America of Lancaster County, Meetup: Women's Friendship 60+, Meetup: WordPress Lancaster, Visit Lancaster City, Zest Chef.

Per dbfirst.md §4, zero events is not itself failure. Fulton Opera House stands out as worth prioritizing in review: it is an actively-operating performing-arts venue, and `Ticketmaster: 0 events across 0 pages` (0 pages, not a paginated 0-results page) matches the shape of a venue-ID or catalog-coverage problem rather than a quiet season, unlike Lampeter-Strasburg (plausibly pre-season with no schedule posted) or the many Meetup groups with genuinely low/no upcoming RSVPs. The other nine scraper zero-outputs and the Meetup/tourism live feeds should be reviewed individually, not batch-retired — several (the 4 dual-producer Songkick/Ticketmaster venues from F004, most Meetup groups) may simply be quiet today.

## F006 Zero DB-only or workflow-only scraper rows exist, so the sync-existing dry run proposes updates only, no inserts or retirements

The dry run's `Missing scraper rows: 0` and `Rows to retire: 0` mean Lancaster's workflow and `feeds` table already agree on which 32 scrapers should run — unlike Davis (dead Chamber/Mondavi rows) or Bloomington (retired Songkick-Bluebird row), Lancaster has no orphaned or missing producer registrations to reconcile. The only outstanding drift is the three name/command-metadata mismatches in F003.

# Actions

- [x] A001 Apply the three dry-run-confirmed scraper metadata updates (Penn Medicine Park name, F&M Athletics command, Lancaster Catholic name) with `--sync-existing` (no `--dry-run`), scoped to `--city lancaster`.
- [ ] A002 Decide which producer to keep for the four dual-represented venues (Tellus 360, Chameleon Club, Freedom Hall, Phantom Power) and retire the duplicate, following the Bluebird pattern.
- [ ] A003 Review the ten zero-event scraper outputs individually and decide fix/watch/retire per source, prioritizing Fulton Opera House.
- [ ] A004 Review the eighteen zero-event live feeds and the seven-file empty-ICS validation warning.
- [ ] A005 Re-run the upstream/local comparison after A001-A004 land to confirm the clean gate for Lancaster.

# Follow-up execution (2026-08-07, same day)

A001 was executed and Fulton Opera House (part of A003) was investigated,
user-authorized in a second phase of this same audit session:

- **A001 applied.** Re-verified dry run showed the identical 3 updates with
  `Weak-name skips: 0`, then `scripts/backfill_scraper_feeds.py --city
  lancaster --sync-existing` (no `--dry-run`) ran with `Updated: 3, Inserted:
  0, Retired: 0, Errors: 0`. `scripts/export_feeds_txt.py lancaster`
  regenerated `cities/lancaster/feeds.txt` from the DB; a final
  `--sync-existing --dry-run` now reports `Rows to update: 0, Rows to
  retire: 0, Missing scraper rows: 0` — Lancaster's DB/workflow drift is
  fully clean.
- **Fulton Opera House investigated (A003, partial).** Direct read-only
  Ticketmaster Discovery API probes confirm the workflow's venue ID
  `ZFr9jZe1Fk` is correct (the only venue matching "Fulton Opera House" in
  PA) and that Ticketmaster's own catalog reports `totalElements: 0` for
  that venue right now — independent of the repo's scraper. Classified as
  valid-but-quiet, not a broken ID; no corrected command to propose. See
  `cities/lancaster/SOURCES_CHECKLIST.md` "2026-08-07 Audit Findings" for
  full detail.
- Findings, the applied fixes, and the Fulton investigation are recorded in
  `cities/lancaster/SOURCES_CHECKLIST.md`. A002 and the remainder of
  A003/A004 remain open — no source retirements were made.
- This report file (`reports/lancaster-2026-08-07-soak.md`) could not be
  edited in place to reflect A001 as done: the Bram worklist guard denied
  the edit (`reason=no-coverage-no-opt-out`, path not in the covered-files
  list). This scratchpad copy carries the update instead.

# Artifacts

- Local build report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.json`
- Local build log: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-build.log`
- Local feed report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-feeds.json`
- Local validation report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-validation.json`
- `backfill_scraper_feeds.py --sync-existing --dry-run` output: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/lancaster-backfill-dryrun.log`
- Upstream Lancaster run: `https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504`
- Upstream job log: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504.log`
