---
report_id: asheville-2026-08-07-soak
title: Asheville source-health audit soak
city: asheville
date: 2026-08-07
commit: 81200105484254a68c053aaabcde79723e820137
overall_status: partial
summary:
  total_checks: 5
  passed: 3
  failed: 1
  warning: 1
findings:
  - id: F001
    status: pass
    title: Asheville workflow/DB scraper metadata is in full parity once local outputs exist to supply names
    scope: asheville scraper registration
    evidence:
      - type: log
        ref: asheville-drift-dryrun.log (pre-build)
      - type: log
        ref: asheville-drift-dryrun-postbuild.log (post-build)
      - type: log
        ref: asheville-drift-dryrun-postfix.log (post-fix, re-confirmed clean)
    action_ids: []
  - id: F002
    status: pass
    title: The Python 3.10 local audit run completed with zero scraper failures, missing outputs, or validation issues
    scope: asheville local audit
    evidence:
      - type: report
        ref: asheville-build.json
      - type: log
        ref: asheville-build.log
      - type: report
        ref: asheville-validation.json
    action_ids: []
  - id: F003
    status: fail
    title: rhp_events.py silently drops every event for three Asheville venues due to a Python-version date-parsing bug
    scope: shared scraper library
    evidence:
      - type: log
        ref: asheville-build.log
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
      - type: repo-file
        ref: scrapers/rhp_events.py
    action_ids: [A001]
  - id: F004
    status: warning
    title: Ten zero-event live feeds need per-source review before any retirement
    scope: asheville source health
    evidence:
      - type: report
        ref: asheville-build.json
      - type: repo-file
        ref: cities/asheville/SOURCES_CHECKLIST.md
    action_ids: [A002]
  - id: F005
    status: pass
    title: Local and same-code upstream Asheville totals are within normal live-source drift
    scope: asheville local-vs-upstream comparison
    evidence:
      - type: log
        ref: asheville-build.log
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
    action_ids: []
actions:
  - id: A001
    status: done
    title: Fix scrapers/rhp_events.py's ISO-8601 date parsing so it accepts colon-less UTC offsets (e.g. "-0400"), restoring events for The Grey Eagle, The Orange Peel, and Pisgah Brewing Company
    owner: agent
  - id: A002
    status: open
    title: Review the ten zero-event live feeds (seven low-volume Meetup groups, two mid-summer-quiet school calendars, one already-documented dead feed) and decide which need retirement, contact, or continued watching
    owner: human+agent
artifacts:
  - label: Local build report
    type: report
    ref: asheville-build.json
  - label: Local build log
    type: log
    ref: asheville-build.log
  - label: Local feed report
    type: report
    ref: asheville-feeds.json
  - label: Local validation report
    type: report
    ref: asheville-validation.json
  - label: Pre-build drift dry-run (shows the missing-local-output pitfall)
    type: log
    ref: asheville-drift-dryrun.log
  - label: Post-build drift dry-run (clean)
    type: log
    ref: asheville-drift-dryrun-postbuild.log
  - label: Post-fix drift dry-run (re-confirmed clean after A001)
    type: log
    ref: asheville-drift-dryrun-postfix.log
  - label: Upstream Asheville run (schedule, commit 784f5d8a, one metadata commit ahead of the audited HEAD)
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Scraper/DB parity | pass | `--sync-existing --dry-run`, run after a fresh local build regenerated all 43 scraper outputs, reported `0` missing, `0` updates, `0` retirements. Re-confirmed clean after the A001 fix. |
| Local audit health | pass | `0` scraper failures, `0` missing scraper outputs, `0` missing live-feed outputs, `0` validation errors/warnings, `0` build issues. |
| Broken parser | fail (fixed) | `scrapers/rhp_events.py` returned `0` events for all three venues it drives, in both the local run and the same-code upstream run, due to a Python-3.10 `datetime.fromisoformat` incompatibility with the venue site's date format. Fixed and verified 2026-08-07 (A001). |
| Zero-event review queue | warning | `10` live feeds produced zero future events; most are already-documented quiet sources but none have been formally retired or watch-dated. Still open (A002). |
| Local/upstream parity | pass | `4531` combined events locally vs `4599` upstream (same code, ~17h apart) — a `1.5%` delta consistent with ordinary live-source churn, not workflow/DB drift. |

# Findings

## F001 Asheville workflow/DB scraper metadata is in full parity once local outputs exist to supply names

Running `scripts/backfill_scraper_feeds.py --city asheville --sync-existing --dry-run` **before** the local build (i.e. before `cities/asheville/*.ics` outputs existed) reported `5` proposed name updates — `Feed And Seed`, `Haw Creek`, `Beth Hatephila`, `Wortham`, `Mountaintrue` — all weaker, filename-derived names that would have overwritten the DB's richer canonical names (`Feed & Seed`, `Haw Creek Community Association`, `Congregation Beth HaTephila`, `Wortham Center for the Performing Arts`, `MountainTrue`). Confirming against the freshly-built `.ics` outputs' `X-SOURCE` headers showed these canonical names are exactly what the scrapers actually emit; the DB rows were already correct.

This matches the exact pitfall `dbfirst.md` §3 warns about: "Run the city locally first so name derivation can read `X-SOURCE` from outputs; empty/missing outputs may fall back to a weak filename-derived name." Re-running the same dry-run **after** the local build completed (so all 43 outputs existed) reported `Rows to update: 0, Rows to retire: 0, Missing scraper rows: 0` — true parity. A third run after the A001 fix (below) confirmed parity is still clean and additionally reported `Weak-name skips: 0`. No DB write was made; the write form was never run.

Follow-up: none needed. The procedure worked as documented once sequenced correctly (build first, then drift-compare).

## F002 The Python 3.10 local audit run completed with zero scraper failures, missing outputs, or validation issues

The full local run (39 workflow scrapers + all live feeds) produced:

- `0` scraper failures (`returncode != 0`)
- `0` missing scraper outputs
- `0` missing live-feed outputs
- `0` validation errors, `0` validation warnings
- `0` build issues, `0` runtime issues

`combined.ics`: `4531` unique future events; `events.json`: `4531` events; RSS `full=3918 latest=100`.

## F003 rhp_events.py silently drops every event for three Asheville venues due to a Python-version date-parsing bug — FIXED 2026-08-07

`The Grey Eagle`, `The Orange Peel`, and `Pisgah Brewing Company` (all driven by `scrapers/rhp_events.py`) each discovered dozens of recent event URLs from their venue's RSS feed (57, 36, and 20 respectively in the local run) and fetched every page, then logged `Got 0 future events` — in **both** the local run and the same-code upstream GitHub run (commit `784f5d8a`, one metadata-only commit ahead of the audited HEAD).

A read-only diagnostic probe against a live Grey Eagle event page confirmed JSON-LD extraction itself works (`extract_jsonld_blocks`/`extract_events_from_blocks` return a valid Event with `startDate: "2026-08-24T18:00:00-0400"`), ruling out a site-format change. The bug was in `scrapers/rhp_events.py` (`_fetch_event_jsonld`):

```python
dtstart = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
```

On Python 3.10 (the parity interpreter, and the `lxml==4.9.1` pin in `dbfirst.md` implies CI also runs pre-3.11), `datetime.fromisoformat` cannot parse an ISO-8601 offset without a colon (`-0400`) — only `-04:00`. Confirmed directly:

```
>>> datetime.fromisoformat('2026-08-24T18:00:00-0400')
ValueError: Invalid isoformat string: '2026-08-24T18:00:00-0400'
```

Every event on every page threw this `ValueError`, was silently skipped (`_fetch_event_jsonld` returned `None`), and the scraper reported a clean `0 events` — no error surfaced anywhere in the pipeline. This matched the "broken parser, healthy upstream data" class from `dbfirst.md` §4 (the UC Davis Arts pattern), not a quiet source. `rhp_events.py` is used exclusively by these three Asheville sources, so the fix was fully scoped to Asheville.

**Fix (A001, done 2026-08-07):** added a narrow `_normalize_iso_offset()` helper in `scrapers/rhp_events.py` that inserts a colon into a trailing 4-digit UTC offset (and still maps a bare `Z` to `+00:00`) before calling `datetime.fromisoformat()`, applied to both `startDate` and `endDate` parsing. Already-coloned offsets and naive (offset-less) timestamps pass through unchanged. Verified with `/tmp/community-calendar-audit-venv310/bin/python` (3.10.20):

| Venue | Before | After |
| --- | --- | --- |
| The Grey Eagle | 0 events | 56 events |
| The Orange Peel | 0 events | 35 events (36 parsed, 1 filtered beyond the 6-month window) |
| Pisgah Brewing Company | 0 events | 20 events |

Output `.ics` files were spot-checked: correct `X-SOURCE` headers and plausible `SUMMARY` values in each. The fix and verification counts are also recorded in `cities/asheville/SOURCES_CHECKLIST.md`. `--sync-existing --dry-run` was re-run after the fix and remained clean (`0` updates, `0` retirements) — the fix only changes event extraction, not scraper registration.

## F004 Ten zero-event live feeds need per-source review before any retirement

The action report classified `10` live feeds as zero-event review items:

- `7` low-volume Meetup groups (Asheville Community Mom's Group, Asheville Garden Club, Asheville Lose The Booze Crew, Asheville TENS Card Game Group, Not Dead Yet Asheville, Psychedelic Society of Asheville, Sierra Club WENOCA) — the checklist's last snapshot already showed each at only `1`-`3` events, so a drop to `0` is plausible natural quiet rather than new breakage, but none are watch-dated.
- `2` Asheville City Schools elementary calendars (Ira B. Jones, Lucy S. Herring) — already documented in `SOURCES_CHECKLIST.md` as "empty mid-summer, populates for fall term." Expected, no action needed beyond a fall recheck.
- `1` River Arts District (`riverartsdistrict.com/events/?ical=1`) — already flagged in `SOURCES_CHECKLIST.md`'s "To Investigate" list as returning `403` to all user agents, "was 30 events." This is the strongest retirement candidate of the ten; it already has documented evidence, just no decision yet.

None of these produced hard errors (`returncode` 0, valid empty ICS), so per `dbfirst.md` §4 this is "zero events without errors" — record for review, do not auto-retire. **Still open** — none of the ten were retired as part of the A001 fix.

## F005 Local and same-code upstream Asheville totals are within normal live-source drift

Local run (2026-08-07, ~12:36-12:49 PDT, HEAD `8120010`):

- `combined.ics`: `4531` events (`Cross-source dedup: removed 905`, `Geo-filtered 609`)
- `events.json`: `4531` events
- RSS: `full=3918 latest=100`

Upstream scheduled run `31142208913` (2026-08-07T02:45Z, commit `784f5d8a` — one auto-generated-metadata-only commit ahead of the audited HEAD, confirmed via `gh api .../compare`):

- `combined.ics`: `4599` events (`Cross-source dedup: removed 937`, `Geo-filtered 612`)
- `events.json`: `4599` events
- RSS: `full=3968 latest=100`

The `~17` hour gap between runs and ordinary event churn (events aging out, new events posting) fully accounts for the `1.5%` delta (`68` events). No scraper newly failed and no workflow/DB drift opened between the two runs — this is the same pattern documented for Bloomington's F005. (These totals predate the A001 fix; a future full rebuild will show the recovered Grey Eagle/Orange Peel/Pisgah events added back in.)

# Actions

- [x] A001 Fix `scrapers/rhp_events.py`'s ISO-8601 date parsing so it accepts colon-less UTC offsets (e.g. `-0400`), restoring events for The Grey Eagle, The Orange Peel, and Pisgah Brewing Company. Done 2026-08-07 — verified 56/35/20 events respectively.
- [ ] A002 Review the ten zero-event live feeds (seven low-volume Meetup groups, two mid-summer-quiet school calendars, one already-documented dead feed) and decide which need retirement, contact, or continued watching.

# Artifacts

- Local build report: `asheville-build.json`
- Local build log: `asheville-build.log`
- Local feed report: `asheville-feeds.json`
- Local validation report: `asheville-validation.json`
- Pre-build drift dry-run (shows the missing-local-output pitfall): `asheville-drift-dryrun.log`
- Post-build drift dry-run (clean): `asheville-drift-dryrun-postbuild.log`
- Post-fix drift dry-run (re-confirmed clean after A001): `asheville-drift-dryrun-postfix.log`
- Upstream Asheville run: `https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504`

Report-support artifacts above (build/feed/validation reports, logs) were written under the session scratchpad directory, not committed to the repo: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/`. The A001 code fix itself (`scrapers/rhp_events.py`) and its checklist record (`cities/asheville/SOURCES_CHECKLIST.md`) are on disk in the repo, uncommitted, pending user review/commit.

---

NOTE: An attempt to sync this A001-done update into
`/Users/jonudell/community-calendar/reports/asheville-2026-08-07-soak.md`
was denied by the same Bram worklist-guard hook
(`reason=no-coverage-no-opt-out`) — the v167 worklist item covers
`scrapers/rhp_events.py`, `cities/asheville/SOURCES_CHECKLIST.md`, and
`cities/asheville/feeds.txt`, but not `reports/asheville-2026-08-07-soak.md`.
Per instructions, this was not worked around. The repo copy of the report
still shows A001 as open/fail; this scratchpad copy is the current version
with A001 marked done and the verification counts recorded.
