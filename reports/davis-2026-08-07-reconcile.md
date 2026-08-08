---
report_id: davis-2026-08-07-reconcile
title: Davis DB/workflow reconciliation
city: davis
date: 2026-08-07
commit: d66d24873e0342a4c0feb5f8c9d7e6177fcb0280
overall_status: pass
summary:
  total_checks: 4
  passed: 3
  failed: 0
  warning: 1
findings:
  - id: F001
    status: pass
    title: Fresh local Davis build produced 633 combined/JSON events and full=603/latest=100 RSS counts
    scope: davis pipeline output
    evidence:
      - type: report
        ref: davis-reconcile-build.json (scratchpad)
    action_ids: []
  - id: F002
    status: pass
    title: Davis Chamber of Commerce DB row retired, completing the 2026-08-06 repo-side retirement
    scope: feeds table
    evidence:
      - type: report
        ref: davis-reconcile-build.json (scratchpad)
    action_ids: [A001]
  - id: F003
    status: pass
    title: Three scraper display-name mismatches reconciled from workflow/X-SOURCE
    scope: feeds table
    evidence:
      - type: report
        ref: davis-reconcile-build.json (scratchpad)
    action_ids: [A002]
  - id: F004
    status: warning
    title: UC Davis Library and three not_ics live feeds remain open review items
    scope: davis sources
    evidence:
      - type: report
        ref: davis-reconcile-validation.json (scratchpad)
    action_ids: [A003, A004]
actions:
  - id: A001
    status: done
    title: Retire the active-but-unused Davis Chamber of Commerce DB row so feeds.txt stops exporting it
    owner: agent
  - id: A002
    status: done
    title: Rename DB rows for UC Davis CampusGroups, Yolo Library, and UU Davis to match the workflow's display names
    owner: agent
  - id: A003
    status: open
    title: Determine whether UC Davis Library's continued zero-event output is a real upstream problem
    owner: human+agent
  - id: A004
    status: open
    title: Review the three not_ics live feeds (Putah Creek Council, Visit Davis, Visit Yolo) for repair or retirement
    owner: human+agent
artifacts:
  - label: Local build report
    type: report
    ref: davis-reconcile-build.json (scratchpad)
  - label: Local build log
    type: log
    ref: davis-reconcile-build.log (scratchpad)
  - label: Local feed report
    type: report
    ref: davis-reconcile-feeds.json (scratchpad)
  - label: Local validation report
    type: report
    ref: davis-reconcile-validation.json (scratchpad)
  - label: Prior audit
    type: report
    ref: reports/davis-2026-08-06-31129696051.md
---

# Outcome

This closes the "Important unfinished Davis reconciliation" gap left by the
2026-08-06 audit (`reports/davis-2026-08-06-31129696051.md`): the repo-side
fixes/retirements were committed, but the `feeds` table still disagreed with
the workflow. This pass ran a fresh local build so name derivation could read
current `X-SOURCE` headers, applied the one retirement and three renames
`--sync-existing` proposed, regenerated `feeds.txt`, and reached a clean
dry-run gate.

| Area | Status | Notes |
| --- | --- | --- |
| Aggregate output | pass | `combined.ics`: 633 events; `events.json`: 633 events; RSS `full=603 latest=100`. |
| Davis Chamber DB retirement | pass | DB row `id=55` moved `active` → `removed`; `feeds.txt` no longer exports it. |
| Scraper name reconciliation | pass | 3 DB rows renamed to match workflow/X-SOURCE display names. |
| Mondavi verification | pass | Absent from both the workflow and active `feeds` rows for `city=davis`. |
| Clean gate | pass | Final `--sync-existing --dry-run`: 0 missing, 0 updates, 0 retirements, 0 skips. |
| Open review items | warning | UC Davis Library (0 events, no hard error) and 3 not_ics live feeds remain unresolved by design — not enough evidence yet to fix or retire. |

# Applied changes

1. **Retired** `feeds` row `id=55` — `Davis Chamber of Commerce`
   (`cities/davis/davis_chamber.ics`), `status: active` → `removed`, via
   `scripts/backfill_scraper_feeds.py --city davis --sync-existing`. The
   workflow invocation was already removed on 2026-08-06
   (`web.davischamber.com` no longer resolves); the DB row was the last piece
   out of sync.
2. **Renamed** `feeds` row `id=50` — `UC Davis Campus Groups` →
   `UC Davis CampusGroups`.
3. **Renamed** `feeds` row `id=52` — `Yolo County Library` → `Yolo Library`.
4. **Renamed** `feeds` row `id=53` — `Unitarian Universalist Church of Davis`
   → `UU Davis`.
5. **Regenerated** `cities/davis/feeds.txt` via
   `scripts/export_feeds_txt.py davis` (20 feeds) to reflect the DB state.
6. **Updated** `cities/davis/SOURCES_CHECKLIST.md` with the reconciliation
   record, current event counts, and the open review items below.

All three renames were checked against the `X-SOURCE` header written into
each scraper's own `.ics` output (`UC Davis CampusGroups`, `Yolo Library`,
`UU Davis`) and match the workflow's scraper naming exactly — not
filename-derived fallbacks. `scripts/backfill_scraper_feeds.py` reported
`Weak-name skips: 0` on both the dry-run and the applied run.

No workflow edit was needed or made: Davis's workflow block
(`.github/workflows/generate-calendar.yml`) already has no Davis Chamber or
Mondavi Center lines.

# Final clean dry-run

```
$ python scripts/backfill_scraper_feeds.py --city davis --sync-existing --dry-run
Workflow scraper rows: 8
Existing scraper rows: 8
Missing scraper rows: 0
Rows to update: 0
Rows to retire: 0
Weak-name skips: 0
```

# Aggregate counts (this build)

- `combined.ics`: 633 events
- `events.json`: 633 events
- RSS: `full=603 latest=100`
- Validation: 0 errors, 4 warnings (all covering the 3 not_ics live feeds
  below)
- Scraper failures: 0; missing scraper outputs: 0; zero-event scraper
  outputs: 1 (UC Davis Library)

# Open items (not resolved this pass)

- **UC Davis Library** (action A004 in the 2026-08-06 report, still open):
  produced 0 events with no hard transport error in both the 2026-08-06 and
  2026-08-07 local runs. Two consecutive quiet runs is stronger signal than
  one but still not proof of upstream breakage — left active, needs a
  source-side check.
- **Putah Creek Council, Visit Davis, Visit Yolo** (live feeds, not
  scrapers — outside `backfill_scraper_feeds.py` scope): all three `?ical=1`
  URLs returned HTML instead of ICS in this run
  (`putahcreekcouncil.ics`, `visitdavis.ics`, `visityolo_event.ics`). Each
  needs an upstream check (broken/blocked/error page) before deciding to fix
  or retire.
- **Meetup: Winters Shut Up & Write** returned zero future events (pre-existing,
  flagged for periodic review, not new drift).

# Files changed

- `cities/davis/feeds.txt` (regenerated from DB)
- `cities/davis/SOURCES_CHECKLIST.md` (reconciliation record)
- `reports/davis-2026-08-07-reconcile.md` (this report)
- `feeds` table rows `id=50,52,53,55` (Supabase, not a repo file)
