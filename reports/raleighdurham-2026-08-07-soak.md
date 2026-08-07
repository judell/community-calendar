---
report_id: raleighdurham-2026-08-07-soak
title: Raleigh-Durham local/upstream parity audit (soak)
city: raleighdurham
date: 2026-08-07
commit: 81200105484254a68c053aaabcde79723e820137
overall_status: partial
summary:
  total_checks: 9
  passed: 4
  failed: 1
  warning: 4
findings:
  - id: F001
    status: pass
    title: Scraper metadata is in DB/workflow parity; the audit tool's own drift check is a false positive from a name-derivation timing bug
    scope: raleighdurham scraper registration
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-drift-dryrun.log
      - type: code
        ref: scripts/local_build.py:536-539
    action_ids: [A001]
  - id: F002
    status: fail
    title: Three ?ical=1 endpoints return an identical generic 403 page instead of a calendar
    scope: raleighdurham live feed health
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.log
      - type: repo-file
        ref: cities/raleighdurham/apsofdurham.ics
    action_ids: [A002]
  - id: F003
    status: fail
    title: Two more live feeds silently return their HTML events page instead of ICS after a URL/permalink change
    scope: raleighdurham live feed health
    evidence:
      - type: repo-file
        ref: cities/raleighdurham/raleighmasjid_programs.ics
      - type: repo-file
        ref: cities/raleighdurham/gatheringplacegames.ics
    action_ids: [A003, A004]
  - id: F004
    status: fail
    title: The Durham Board Games Meetup feed returns a "Group not found" JSON error, not a calendar
    scope: raleighdurham live feed health
    evidence:
      - type: repo-file
        ref: cities/raleighdurham/meetup_durham_board_games_meetup_group.ics
    action_ids: [A005]
  - id: F005
    status: warning
    title: The local audit and validator both classify all six broken feeds above as healthy "0 events," masking real failures behind the zero-event review bucket
    scope: local audit procedure
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.json
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-validation.json
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
    action_ids: [A006]
  - id: F006
    status: warning
    title: NC Cultural Resources (1,411 upstream events) failed to download locally on an SSL trust-store gap, not a source problem
    scope: local runtime parity
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.log
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
    action_ids: [A007]
  - id: F007
    status: pass
    title: Every scraper (19/19) matched its upstream GitHub Actions event count within normal live-source drift
    scope: raleighdurham scraper health
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.log
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
    action_ids: []
  - id: F008
    status: warning
    title: Carolina Performing Arts returned zero events from a healthy API call, matching upstream on the same day
    scope: raleighdurham source health
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.log
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
    action_ids: [A008]
  - id: F009
    status: pass
    title: The remaining eight zero-event Meetup live feeds are genuinely valid-but-quiet, not broken
    scope: raleighdurham source health
    evidence:
      - type: repo-file
        ref: cities/raleighdurham/meetup_blacks_in_tech_bit_rdu_durham_raleigh_meetup.ics
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.json
    action_ids: []
actions:
  - id: A001
    status: done
    title: Fix local_build.py to compute scraper drift after scrapers run (or reuse the prior run's outputs) so name-derivation via X-SOURCE isn't starved by clean_known_outputs(). Done 2026-08-07 in the runner-hardening pass — drift now computed post-build from re-derived rows with name provenance; filename-derived names no longer count as drift or overwrite DB names in --sync-existing
    owner: agent
  - id: A002
    status: done
    title: "Resolved 2026-08-07 (user-adjudicated, executed): initial re-verification showed a contradiction — apsofdurham.org, durhamcentralpark.org, and secondchancenc.org's Tribe REST endpoint returned HTTP 403 on every attempt (default UA, full Chrome UA, full browser header set, and a live tribe_rest.py run), contradicting reported working totals (64/0/6). Follow-up probing resolved the contradiction: durhamcentralpark.org's endpoint returned HTTP 200/total:64 once, then 403'd 4 more times minutes later via the actual scraper; secondchancenc.org and apsofdurham.org consistently hit SiteGround's sgcaptcha bot-challenge page (HTTP 202 + meta-refresh) on every attempt. Conclusion: an intermittently-permissive/stateful WAF, not fixed UA or IP filtering. User decided to convert all three anyway (flakiness accepted). EXECUTED: added 3 scrapers/tribe_rest.py lines to the raleighdurham workflow block, removed the 3 old ics_url rows (278/289/290, 0 events each) via the Manage Feeds sequence, backfill_scraper_feeds.py --sync-existing dry-run confirmed exactly 3 inserts then applied (Inserted: 3, Errors: 0), feeds.txt re-exported, final dry-run 22/22 rows clean. Durham Central Park verified once via raw HTTP (total 64) but not yet via the scraper itself; APS of Durham and Second Chance Pet Adoptions have no successful run yet this session — documented as verified-intermittent, not reverted. See cities/raleighdurham/SOURCES_CHECKLIST.md 2026-08-07 follow-up entry for full evidence"
    owner: human+agent
  - id: A003
    status: done
    title: Update the Islamic Association of Raleigh feed URL from /programs/?ical=1 to /masjid-programs/?ical=1 (confirmed working, valid ICS) after the permalink change. Done 2026-08-07 — feed row PATCHed; re-verified HTTP 200, valid BEGIN:VCALENDAR, 1 event
    owner: agent
  - id: A004
    status: done
    title: "Resolved 2026-08-07 (user-adjudicated): probed /events/list/?ical=1, /feed/events/, /events-2/list/?ical=1, ?post_type=tribe_events&ical=1, and /wp-json/tribe/events/v1/events for The Gathering Place Games — all return HTML or 404 (rest_no_route), no ICS, no machine-readable events surface. Decision: retire. Feed (id 291) removed via the Manage Feeds sequence (events DELETE affected 0 rows since none had ever loaded, then remove_feed RPC); row confirmed gone. Documented in the checklist with a note to re-add if they restore a working export"
    owner: human+agent
  - id: A005
    status: done
    title: Find the Durham Board Games Meetup group's current slug or retire the source if it is gone. Done 2026-08-07 — group is deleted upstream; feed (id 313) removed via the Manage Feeds sequence (events DELETE affected 0 rows since none had ever loaded, then remove_feed RPC); row confirmed gone
    owner: human+agent
  - id: A006
    status: done
    title: Make the local audit and validate_pipeline distinguish a live feed that fetched valid empty ICS from one that fetched HTML/JSON instead of ICS. Done 2026-08-07 in the runner-hardening pass — outputs without BEGIN:VCALENDAR now classify as not_ics with a content_kind sniff, land in the fix bucket, raise validation findings, and fail the runner's exit code
    owner: agent
  - id: A007
    status: open
    title: Fix the local machine's curl/TLS trust store so events.dncr.nc.gov's DigiCert G5 chain verifies (or document the gap) so local audits stop under-counting by ~1,400 events
    owner: human
  - id: A008
    status: deferred
    title: Re-check Carolina Performing Arts in a few weeks; zero events during early August may be a normal between-seasons gap at Memorial Hall rather than a break
    owner: human+agent
artifacts:
  - label: Local build report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.json
  - label: Local build log
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.log
  - label: Local feed report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-feeds.json
  - label: Local validation report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-validation.json
  - label: Drift dry-run (post-build, corrected)
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-drift-dryrun.log
  - label: Upstream Raleigh-Durham run
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Scraper/DB parity | pass | 19 workflow scraper rows, 19 DB rows, 0 missing, 0 to retire, 0 genuine name/command drift once the dry run is re-run against fresh scraper output (see F001). |
| Broken live feeds | fail | 6 of 15 flagged live feeds are not "quiet" — 3 return an identical 403 block page, 2 return their HTML events page, 1 returns a Meetup "Group not found" JSON error. None of these are ICS. |
| Audit classification gap | warning | `local_build.py`/`validate_pipeline.py` only check for `BEGIN:VEVENT` count, so all 6 broken feeds above were reported as healthy "0 future events," identically in the local run and the 2026-08-07 upstream GitHub run. |
| Local/upstream scraper parity | pass | All 19 scrapers reproduced upstream counts within normal live-source drift (catscradle 92/92, motorco 45/45, carolina_theatre 81/81, duke_arts 55/55, dpac 46/46, etc.). |
| Local runtime parity | warning | The single missing live-feed output (NC Cultural Resources, normally ~1,400 events) is a local SSL trust-store gap (`unable to get local issuer certificate` for `events.dncr.nc.gov`'s DigiCert G5 chain), confirmed working both upstream and via `curl -k`. This alone explains nearly the entire combined-event gap between the local run (2,639) and the same-day upstream run (4,014). |
| Zero-event review queue | pass | The other 8 zero-event Meetup feeds and Carolina Performing Arts (API scraper) are genuinely valid, quiet sources — confirmed by inspecting raw output and cross-checking the same-day upstream run. |

# Findings

## F001 Scraper metadata is in DB/workflow parity; the audit tool's own drift check is a false positive

`scripts/backfill_scraper_feeds.py --city raleighdurham --sync-existing --dry-run`, re-run against the completed local build's fresh `.ics` outputs, reports:

```
Workflow scraper rows: 19
Existing scraper rows: 19
Missing scraper rows: 0
Rows to update: 0
Rows to retire: 0
```

But the audit's own `local-build-report.json` lists 8 `scraper_name_mismatch` drift items (Wake County Legistar, Chapelhill Legistar, Durhamcounty Legistar, Durham Chamber, Wakeforest Chamber, Apex Chamber, Catscradle, Motorco), and my own first dry run — launched while the build was still mid-scrape — showed 2 proposed updates for Catscradle and Motorco that would have **regressed** the DB's proper display names ("Cat's Cradle", "Motorco Music Hall") to weak filename-derived ones ("Catscradle", "Motorco").

Root cause: `run_city()` in `scripts/local_build.py:536-539` calls `build_scraper_drift()` using `workflow_scraper_rows()` **before** `clean_known_outputs()` (line 565) deletes the prior run's `.ics` files and before the scraper loop regenerates them. `derive_name()` in `scripts/backfill_scraper_feeds.py` falls back from an explicit `--name` flag to reading `X-SOURCE`/`X-WR-CALNAME` from the existing output file, and only then to a weak filename-derived title. On a clean checkout (no prior `.ics` files on disk, as here), that fallback always misses, so every scraper lacking an explicit `--name` flag in its workflow command is reported as a name mismatch regardless of whether the DB name is actually correct. Confirmed by re-running the same dry run after the build finished (`.ics` files with real `X-SOURCE` headers now present): 0 updates.

This is 8 of 8 "fix" items in the action report being false positives — a majority of the reported drift.

## F002 Three ?ical=1 endpoints return an identical generic 403 page instead of a calendar

`cities/raleighdurham/apsofdurham.ics`, `durhamcentralpark.ics`, and `secondchancenc.ics` are byte-identical (md5 `dcc4e47f2e8acc6928ab7e5d2fa69d61`, 75,193 bytes), each containing `<title>403 - Forbidden</title>`. Confirmed live with a direct `curl` (both the scraper's declared User-Agent and a full browser User-Agent return HTTP 403):

- `https://www.apsofdurham.org/events/?ical=1`
- `https://durhamcentralpark.org/events/list/?ical=1`
- `https://secondchancenc.org/events/?ical=1`

The identical byte-for-byte response across three unrelated domains points to a shared hosting/WAF provider blocking the request outright, not three independent site outages. This matches the checklist's existing "Mod_Security blocks automated requests" non-starter pattern (Downtown Cary, Durham Convention Center) rather than a dead source — worth checking whether GitHub Actions' network path is exempt before deciding to retire.

## F003 Two more live feeds silently return HTML instead of ICS after a URL/permalink change

- **Islamic Association of Raleigh**: `https://raleighmasjid.org/programs/?ical=1` redirects (302) to `https://raleighmasjid.org/masjid-programs/` (the WordPress permalink changed), dropping the `?ical=1` query and landing on the human-readable events page. I confirmed the corrected URL still works: `https://raleighmasjid.org/masjid-programs/?ical=1` returns valid `BEGIN:VCALENDAR` content (read-only check, not applied).
- **The Gathering Place Games**: `https://gatheringplacegames.com/events/?ical=1` redirects to `https://gatheringplacegames.com/events-2/?ical=1`, but that URL still returns the site's normal HTML events page, not ICS — the Tribe Events ICS export appears to be disabled or moved. Needs further investigation before any URL fix is proposed.

## F004 The Durham Board Games Meetup feed returns a "Group not found" JSON error, not a calendar

`cities/raleighdurham/meetup_durham_board_games_meetup_group.ics` is 29 bytes: `{"message":"Group not found"}`. The Meetup group at `durham-board-games-meetup-group` no longer resolves — likely renamed, merged, or deleted. This is an "upstream gone" class source; needs a search for the group's current slug or retirement.

## F005 The local audit and validator both classify all six broken feeds above as healthy "0 events"

Both `scripts/download_feeds.py` (`✅ {filename}: {events} events`, counting `BEGIN:VEVENT` occurrences) and `scripts/validate_pipeline.py`'s empty-ICS check only look at event counts, never at whether the fetched bytes are actually an ICS calendar (`BEGIN:VCALENDAR`). All 6 broken feeds in F002–F004 were logged as `✅ ... 0 events` in both `raleighdurham-build.log` and the same-day upstream GitHub Actions job log (`31142208913`/`92754273504`), and `local-build-report.json` bucketed all 6 under `action_report.review` alongside 8 genuinely-quiet Meetup feeds — indistinguishable without opening the files. This is the same class of gap the Davis audit (`reports/davis-2026-08-06-31129696051.md`, F006) found for scraper error counting; here it recurs for live-feed content-type validation.

## F006 NC Cultural Resources failed to download locally on an SSL trust-store gap, not a source problem

`cities/raleighdurham/events_1_ics.ics` (NC Cultural Resources, `https://events.dncr.nc.gov/calendar/1.ics`) is the one `missing_live_feed_output` in the local run. Direct diagnosis (read-only):

```
curl: SSL certificate problem: unable to get local issuer certificate
```

for the DigiCert G5 chain served by `events.dncr.nc.gov`. General network access is fine (`google.com` returns 200), and `curl -k` against the same URL returns valid ICS content immediately. The same-day upstream GitHub Actions run combined **1,411** future events from this exact feed (`events_1_ics.ics (NC Cultural Resources)`), confirming the source itself is healthy. This single feed plausibly explains nearly all of the gap between the local run's combined total (2,639) and the same-day upstream total (4,014) — dedup/geo-filter counts were close in both runs (local: dedup 120, geo-filtered 140; upstream: dedup 125, geo-filtered 176). This is a local-machine environment gap (macOS/LibreSSL trust store missing a current DigiCert root), not a repo or scraper change.

## F007 Every scraper reproduced its upstream count within normal live-source drift

Side-by-side (local / upstream, same day):

| Scraper | Local | Upstream |
| --- | --- | --- |
| Cat's Cradle | 92 | 92 |
| Motorco Music Hall | 45 | 45 |
| Carolina Theatre | 81 | 81 |
| Duke Arts | 55 | 55 |
| DPAC (Ticketmaster) | 46 | 46 |
| Raleigh Little Theatre | 64 | 65 |
| Wake Forest Chamber | 31 | 31 |
| Apex Chamber | 18 | 18 |
| Durham Chamber | 7 | 7 |
| Martin Marietta (Ticketmaster) | 86 | 72 |

The Martin Marietta and Raleigh Little Theatre gaps are consistent with normal live-API/time-of-day drift (Ticketmaster inventory changes hourly), not a scraper defect. No scraper failed (`0/19` nonzero return codes, `0` missing scraper outputs).

## F008 Carolina Performing Arts returned zero events from a healthy API call

`carolina_performing_arts.py` hit `https://carolinaperformingarts.org/wp-json/cpa/v1/performances/` and got a clean `200`/`API returned 0 events` both locally and in the same-day upstream run. `SOURCES_CHECKLIST.md` documents ~18 events as typical for this source ("Clean JSON REST API ... ~18 events at Memorial Hall"). Because both runs agree and there's no transport error, this reads as valid-but-quiet (possibly an early-August between-seasons gap at a university performance hall) rather than broken — recommend a re-check in a few weeks rather than immediate action.

## F009 The remaining eight zero-event Meetup feeds are genuinely valid-but-quiet

`meetup_blacks_in_tech_bit_rdu_durham_raleigh_meetup.ics`, `meetup_chicktech_rdu.ics`, `meetup_futureofdata_triangle.ics`, `meetup_pydata_triangle.ics`, `meetup_raleigh_wordpress_meetup_group.ics`, `meetup_research_triangle_analysts.ics`, `meetup_triangle_devops.ics`, and `meetup_tripython.ics` all contain well-formed `BEGIN:VCALENDAR` / Meetup-branded ICS with legitimately zero `VEVENT`s — these Meetup groups exist but currently have no scheduled events. No action needed beyond the standing periodic review.

# Actions

- [ ] A001 Fix `local_build.py` to compute scraper drift after scrapers run (or reuse the prior run's outputs) so name-derivation via `X-SOURCE` isn't starved by `clean_known_outputs()`.
- [ ] A002 Investigate whether apsofdurham.org, durhamcentralpark.org, and secondchancenc.org block the scraper's requests at the hosting/WAF layer, and whether GitHub Actions' network path is exempt; retire or find an alternate path if the block is durable.
- [ ] A003 Update the Islamic Association of Raleigh feed URL from `/programs/?ical=1` to `/masjid-programs/?ical=1` (confirmed working, valid ICS) after the permalink change.
- [ ] A004 Investigate The Gathering Place Games ICS export; the events page moved to `/events-2/` but neither the old nor new path returns ICS with `?ical=1`.
- [ ] A005 Find the Durham Board Games Meetup group's current slug (the group may have been renamed) or retire the source if it is gone.
- [ ] A006 Make the local audit and `validate_pipeline` distinguish a live feed that fetched valid empty ICS from one that fetched HTML/JSON instead of ICS (check for `BEGIN:VCALENDAR`, not just `BEGIN:VEVENT` count).
- [ ] A007 Fix the local machine's curl/TLS trust store so `events.dncr.nc.gov`'s DigiCert G5 chain verifies (or document the gap) so local audits stop under-counting by ~1,400 events.
- [ ] A008 Re-check Carolina Performing Arts in a few weeks; zero events during early August may be a normal between-seasons gap at Memorial Hall rather than a break.

# Artifacts

- Local build report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.json`
- Local build log: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-build.log`
- Local feed report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-feeds.json`
- Local validation report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-validation.json`
- Drift dry-run (post-build, corrected): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/raleighdurham-drift-dryrun.log`
- Upstream Raleigh-Durham run: `https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504`
