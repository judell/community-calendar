---
report_id: bloomington-2026-08-07-postsync
title: Bloomington post-sync local audit
city: bloomington
date: 2026-08-07
commit: 81200105484254a68c053aaabcde79723e820137
overall_status: partial
summary:
  total_checks: 5
  passed: 3
  failed: 0
  warning: 2
findings:
  - id: F001
    status: pass
    title: Bloomington scraper metadata is now in DB/workflow parity
    scope: bloomington scraper registration
    evidence:
      - type: report
        ref: /tmp/bloomington-postsync-audit.json
      - type: repo-file
        ref: cities/bloomington/feeds.txt
    action_ids: []
  - id: F002
    status: pass
    title: The Python 3.10 local audit run completed without runtime, scraper, or validation errors
    scope: bloomington local audit
    evidence:
      - type: report
        ref: /tmp/bloomington-postsync-audit.json
      - type: log
        ref: /tmp/bloomington-postsync-build.log
    action_ids: []
  - id: F003
    status: pass
    title: Boys & Girls Club Bloomington was repaired by switching from a dead ICS feed to a Tribe REST scraper
    scope: bloomington source remediation
    evidence:
      - type: repo-file
        ref: cities/bloomington/feeds.txt
      - type: workflow
        ref: .github/workflows/generate-calendar.yml
    action_ids: [A001]
  - id: F004
    status: warning
    title: Thirty-one Bloomington sources produced zero future events and still need human review
    scope: bloomington source health
    evidence:
      - type: report
        ref: /tmp/bloomington-postsync-audit.json
      - type: report
        ref: /tmp/bloomington-postsync-validation.json
    action_ids: [A002, A003]
  - id: F005
    status: warning
    title: The 2026-08-07 local totals differ from the 2026-08-06 GitHub run, but not because of scraper parity drift
    scope: bloomington local-vs-upstream comparison
    evidence:
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31130806514/job/92719021634
      - type: log
        ref: /tmp/bloomington-gh.log
      - type: log
        ref: /tmp/bloomington-postsync-build.log
    action_ids: [A004]
actions:
  - id: A001
    status: done
    title: Repair the Boys & Girls Club Bloomington source by replacing the dead ICS feed with a Tribe REST scraper and removing the old DB row
    owner: agent
  - id: A002
    status: deferred
    title: Review the seven zero-event live feeds and decide which are expected silence versus broken sources
    owner: human+agent
  - id: A003
    status: deferred
    title: Review the twenty-three zero-event scraper outputs and decide which should be fixed, watched, or retired
    owner: human+agent
  - id: A004
    status: deferred
    title: Run a fresh same-day upstream Bloomington build if we want a strict remote/local parity comparison after the DB sync
    owner: agent
artifacts:
  - label: Post-sync local audit
    type: report
    ref: /tmp/bloomington-postsync-audit.json
  - label: Post-sync local build log
    type: log
    ref: /tmp/bloomington-postsync-build.log
  - label: Post-sync local validation
    type: report
    ref: /tmp/bloomington-postsync-validation.json
  - label: Prior GitHub Bloomington run
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31130806514/job/92719021634
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Scraper parity | pass | The post-sync audit reported `0` drift items between workflow scrapers and DB scraper rows. |
| Local audit health | pass | The Python 3.10 run had `0` runtime issues, `0` scraper failures, and `0` validation errors. |
| Concrete fixes still needed | pass | No concrete fix items remain open in this report; Boys & Girls Club Bloomington was repaired after the post-sync audit. |
| Review queue | warning | `31` sources produced zero future events and should be reviewed before any retirements or scraper changes. |
| Remote/local comparison | warning | The 2026-08-07 local run produced `6357` combined events versus `6297` in the 2026-08-06 GitHub run; this is live-source and dedup drift, not workflow/DB mismatch. |

# Findings

## F001 Bloomington scraper metadata is now in DB/workflow parity

The post-sync local audit reported `0` drift items for Bloomington. The DB-only `songkick_bluebird` row was retired, and the remaining scraper rows now match the workflow metadata.

## F002 The Python 3.10 local audit run completed without runtime, scraper, or validation errors

The post-sync run completed with:

- `0` runtime issues
- `0` scraper failures
- `0` missing scraper outputs
- `0` validation errors

The only validation result was the existing warning about `uplandbeer.ics` and `bloomingtoncommunityband.ics` being empty.

## F003 Boys & Girls Club Bloomington was repaired by switching from a dead ICS feed to a Tribe REST scraper

The post-sync audit surfaced one concrete `fix` item for Boys & Girls Club Bloomington. That item has now been resolved by replacing the dead `?ical=1` feed with a `tribe_rest.py` scraper in the workflow and Bloomington source inventory, then removing the obsolete `ics_url` row from the feeds table.

## F004 Thirty-one Bloomington sources produced zero future events and still need human review

The post-sync action report classified `31` items as `review`:

- `7` zero-event live feeds
- `23` zero-event scraper outputs
- `1` validation warning for `uplandbeer.ics` and `bloomingtoncommunityband.ics`

These are not auto-fix or auto-retire cases. They need source-by-source review.

## F005 The 2026-08-07 local totals differ from the 2026-08-06 GitHub run, but not because of scraper parity drift

The post-sync local run produced:

- `6357` combined events
- `5462` full RSS events
- `881` cross-source dedup removals
- `108` geo-filtered events

The GitHub run from 2026-08-06 produced:

- `6297` combined events
- `5383` full RSS events
- `851` cross-source dedup removals
- `106` geo-filtered events

Because scraper drift is now zero and the comparison crosses different run dates, this remaining delta should be treated as live-source drift and dedup variability, not as a DB/workflow parity failure.

# Actions

- [x] A001 Repair the Boys & Girls Club Bloomington source by replacing the dead ICS feed with a Tribe REST scraper and removing the old DB row.
- [ ] A002 Review the seven zero-event live feeds and decide which are expected silence versus broken sources.
- [ ] A003 Review the twenty-three zero-event scraper outputs and decide which should be fixed, watched, or retired.
- [ ] A004 Run a fresh same-day upstream Bloomington build if we want a strict remote/local parity comparison after the DB sync.

# Artifacts

- Post-sync local audit: `/tmp/bloomington-postsync-audit.json`
- Post-sync local build log: `/tmp/bloomington-postsync-build.log`
- Post-sync local validation: `/tmp/bloomington-postsync-validation.json`
- Prior GitHub Bloomington run: `https://github.com/judell/community-calendar/actions/runs/31130806514/job/92719021634`
