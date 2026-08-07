---
report_id: santarosa-2026-08-07-soak
title: Santa Rosa read-only source-health soak
city: santarosa
date: 2026-08-07
commit: 81200105484254a68c053aaabcde79723e820137
overall_status: partial
summary:
  total_checks: 8
  passed: 2
  failed: 1
  warning: 5
findings:
  - id: F001
    status: pass
    title: The Python 3.10 local audit ran all 65 workflow producers to completion with healthy aggregates
    scope: santarosa local audit
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.log
    action_ids: []
  - id: F002
    status: fail
    title: Two scrapers hard-fail identically locally and in GitHub Actions — Cafe Frida (upstream gone) and Spreckels (broken parser, healthy upstream)
    scope: santarosa scraper failures
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.log
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913
    action_ids: [A001, A002]
  - id: F003
    status: warning
    title: Thirty workflow/DB drift items; the sync dry run proposes 12 updates and 2 retirements, but several proposed name updates are weak fallback names that must not be applied
    scope: santarosa workflow/DB parity
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.json
      - type: repo-file
        ref: scripts/backfill_scraper_feeds.py
    action_ids: [A003, A004]
  - id: F004
    status: warning
    title: Sonoma Valley Events is status=removed in the DB while the workflow still runs it and it produces about 500 events; the checklist blesses it, so reactivation, not workflow removal, is the right resolution
    scope: santarosa source status contradiction
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.json
      - type: repo-file
        ref: cities/santarosa/SOURCES_CHECKLIST.md
    action_ids: [A003]
  - id: F005
    status: warning
    title: Fourteen non-failing scrapers produced zero events; Cinnabar is a repairable date-range parser break, the rest are quiet, superseded, or checklist-flagged-dead sources
    scope: santarosa scraper health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.log
    action_ids: [A005, A007]
  - id: F006
    status: warning
    title: Twelve live feeds produced zero events, and at least six of them are removals the source checklist already directed but that were never executed against the feeds table
    scope: santarosa live-feed health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-feeds.json
      - type: repo-file
        ref: cities/santarosa/SOURCES_CHECKLIST.md
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-feeds-db-export.txt
    action_ids: [A006, A007]
  - id: F007
    status: pass
    title: Local and upstream runs agree on producer set, failure pair, and the zero-event roster; aggregate deltas are live-source drift, with one divergence (Sonoma Community Center REST) to watch
    scope: santarosa local-vs-upstream comparison
    evidence:
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-logs/0_generate-calendar.txt
    action_ids: [A007]
  - id: F008
    status: warning
    title: Two DB-only scraper rows are malformed (New World Ballet has no command; a duplicate North Bay Derby row uses the page URL as its output) and many DB commands carry a doubled "cmd: cmd:" prefix
    scope: santarosa DB row hygiene
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-feeds-db-export.txt
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.json
    action_ids: [A003]
actions:
  - id: A001
    status: done
    title: Retire the Cafe Frida producer and DB row — the venue rebranded to Cafe Little Deer and no public events surface exists on the successor site (checked 2026-08-07)
    owner: agent
  - id: A002
    status: done
    title: Rewrite the Spreckels scraper against the redesigned site (WordPress /show/2026-27-season/ pages with Arts People ticketing; the Tribe REST API is gone)
    owner: human+agent
  - id: A003
    status: done
    title: "Apply the narrow, safe subset of the sync dry run — retire the New World Ballet and malformed North Bay Derby rows, normalize the Sonoma County Board of Supervisors command, and reactivate Sonoma Valley Events — then re-export feeds.txt and rerun. NOTE: the Sonoma Valley Events reactivation was reversed later on 2026-08-07 by owner decision (the DB removal had been deliberate — the site has a history of rejecting probes); workflow line, 333 events, and feed row 1066 all removed for good. See the checklist's Reconciled section"
    owner: human+agent
  - id: A004
    status: done
    title: "Resolve the display-name mismatches at the source. Adjudicated 2026-08-07: the 6 MaxPreps workflow lines gained explicit --name flags matching the DB's 'Athletics' names (DB scraper_cmd synced to match); santa_rosa_arts_center.py and movingwriting.py now emit stable X-WR-CALNAME values, eliminating the '- 2026/08' title artifacts; the weak filename-derived fallback class (Cafefrida, Spreckels) was already neutralized by the sync tool's name-provenance guard. Post-fix dry run fully clean: 63/63, 0 updates, 0 retirements"
    owner: human+agent
  - id: A005
    status: done
    title: Repair the Cinnabar date-range parser (four shows skipped on formats like "Sept. 18 – Oct. 4 2026"), which currently yields zero events from a healthy upstream
    owner: agent
  - id: A006
    status: done
    title: Execute the checklist's pending Manage Feeds removals — old Sonoma County DSA gcal (Google 404), Meetup Go Wild Hikers and Sonoma County Boomers (groups deleted), The Big Easy Tribe ICS, Redwood Cafe My Calendar ICS and its Songkick interim, Sonoma Community Center ?ical=1, Santa Rosa Symphony ?ical=1
    owner: human+agent
  - id: A007
    status: done
    title: "A007 review queue adjudicated 2026-08-07 — Barrel Proof repaired (wfea JSON, 291 events), Sweetwater repaired (Py3.10 ISO-offset fix, 33 events, Songkick duplicate kept), Luther Burbank + Uptown Theatre Napa converted to tribe_rest by final user adjudication despite the SiteGround PoW WAF (old feed rows 393/400 removed, new scraper rows synced, --user-agent flag on the workflow lines; blocked days yield valid-empty calendars, reliable coverage still needs a venue WAF-allowlist or headless harness — that follow-up stays open), Sonoma County AA / sonoma.com / Santa Rosa Arts Center / 9 quiet Songkick venues deliberately kept watching"
    owner: human+agent
artifacts:
  - label: Local audit build report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.json
  - label: Local audit build log
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.log
  - label: Local feed report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-feeds.json
  - label: Local validation report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-validation.json
  - label: DB-export feeds.txt snapshot (taken mid-run before restore)
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-feeds-db-export.txt
  - label: Upstream GitHub run (scheduled, same day)
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31142208913
  - label: Upstream run log (downloaded)
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-logs/0_generate-calendar.txt
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Local audit health | pass | Python 3.10.20 parity run completed: `65` producers, `0` runtime issues, combined `5902` events, JSON `5902`, RSS full `5438` / latest `100`. |
| Hard failures | fail | `2` scrapers exit 1 with missing outputs: Cafe Frida (`404`, venue rebranded) and Spreckels (Tribe REST gone). Identical failures in the upstream run. |
| Workflow/DB parity | warning | `30` drift items; dry run proposes `0` inserts, `12` updates, `2` retirements. A safe subset is ready; several name updates are weak fallbacks that must not be applied as-is. |
| DB row hygiene | warning | `2` malformed DB-only rows (New World Ballet, duplicate North Bay Derby) plus widespread doubled `cmd: cmd:` prefixes in scraper commands. |
| Scraper review queue | warning | `14` zero-event non-failing scrapers: `1` repairable parser break (Cinnabar), `13` quiet/superseded/checklist-flagged. |
| Live-feed review queue | warning | `12` zero-event live feeds; `6+` are removals the checklist already directed but that never reached the feeds table. |
| Remote/local comparison | pass | Same producer set, same two failures, same zero-event roster. Local `5902` vs upstream `5588` combined is live-source drift. One divergence: Sonoma Community Center REST yields `305` locally, `0` upstream. |
| Generated-file dirt | pass | Run left only expected dirt: `cities/santarosa/geo_filtered.json`, `rss/santarosa-full.xml`, `rss/santarosa-latest.xml` (all regenerable); `.ics` outputs are gitignored; `feeds.txt` was restored. |

# Findings

## F001 The Python 3.10 local audit ran all 65 workflow producers to completion with healthy aggregates

The run used `/tmp/community-calendar-audit-venv310/bin/python` (3.10.20, matching the upstream `pythonLocation` 3.10.20) and completed with `0` runtime issues. All `65` workflow scraper invocations executed (including Sonoma Valley Events, see F004), the `51`-feed live download succeeded (`download_returncode: 0`), and the pipeline produced:

- combined: `5902` unique future events
- JSON: `5902` events
- RSS: full `5438`, latest `100`

## F002 Two scrapers hard-fail identically locally and in GitHub Actions

- **Cafe Frida** (`scrapers/cafefrida.py`): `HTTP Error 404` on `https://www.cafefridagallery.com/events`, exit 1, no output. The domain root now redirects to `https://www.cafelittledeer.com/` (venue rebranded); the successor site has no public events page (only `/private-event-booking`; `/events`, `/calendar` 404). Upstream run 31142208913 fails with the same traceback and produces no `cafefrida.ics`. Class: **upstream gone** — retire (Davis Chamber/Mondavi pattern).
- **Spreckels** (`scrapers/spreckels.py`): `404` on `https://spreckelsonline.com/wp-json/tribe/events/v1/events`, exit 1, no output, same failure upstream. The site itself is alive (200) and still WordPress, but the Tribe plugin is gone; shows are server-rendered at `/show/2026-27-season/<slug>/` with Arts People ticketing links. Class: **broken parser, healthy upstream data** — repair (UC Davis Arts pattern).

These two account for all `4` validation errors (command failed + output missing, each).

## F003 Thirty drift items; the sync dry run proposes 12 updates and 2 retirements — apply only the safe subset

Drift breakdown from the audit: `26` scraper_name_mismatch, `1` scraper_command_mismatch, `1` removed_db_scraper_still_in_workflow, `2` db_scraper_missing_from_workflow.

`backfill_scraper_feeds.py --city santarosa --sync-existing --dry-run` (run post-audit so name derivation could read `X-SOURCE`): workflow rows `65`, existing rows `65`, missing `0`, updates `12`, retirements `2`.

Safe, mechanical subset:

- `RETIRE New World Ballet` — active DB row with no command and no producer (F008).
- `RETIRE North Bay Derby [https://www.northbayderby.org/events]` — malformed duplicate row; the proper `squarespace_northbayderby.ics` row remains.
- `UPDATE Sonoma County Board of Supervisors` — normalizes DB `--name` to the workflow's `--source` form plus `--output` (pure command drift).
- `UPDATE Sonoma Valley Events -> {"status": "active"}` — see F004.

Unsafe subset — **do not apply as-is**:

- `{"name": "Cafefrida"}` and `{"name": "Spreckels"}` are filename-derived fallbacks (their outputs are missing because the scrapers failed) and would clobber the good DB names "Cafe Frida" / "Spreckels Performing Arts Center".
- `{"name": "Santa Rosa Arts Center - 2026/08"}` and `{"name": "MovingWriting - 2026/08"}` carry calendar-title month suffixes — weak derived names.
- The six MaxPreps `--school` rows would drop the "Athletics" suffix ("Santa Rosa High School" vs "Santa Rosa High School Athletics"). The workflow commands lack `--name`; the better fix is adding explicit names to the workflow (A004), not regressing the DB display names.

The remaining ~20 name mismatches (Library Intercept vs Sonoma County Library, Bohemian vs North Bay Bohemian, etc.) are cosmetic artifacts of first-party scrapers not passing a name flag; the dry run leaves most untouched, confirming they are derivation noise rather than DB damage.

## F004 Sonoma Valley Events: DB says removed, workflow still runs it, checklist blesses it

The DB row for `cities/santarosa/sonoma_valley_events.ics` is `status='removed'`, but the workflow still invokes `scrapers/gatherboard.py --url "https://www.sonomavalleyevents.com"`, which produced `451` events upstream and `503` future events locally. `cities/santarosa/SOURCES_CHECKLIST.md` records it as a deliberately added aggregator ("Formerly 'RSS Coming Soon'", 594 events at wiring time). The audit's action_report suggests "Remove retired scraper Sonoma Valley Events from the workflow", but that contradicts the checklist; the DB removal looks accidental (likely a Manage Feeds deletion that never touched the workflow). Recommendation: accept the dry run's `status: active` reactivation (A003). This is a human-confirm decision point.

## F005 Fourteen non-failing scrapers produced zero events

Distinct classes, per the dbfirst.md taxonomy:

- **Broken parser, healthy upstream**: Cinnabar — `4` warnings skipping every show over unparsed date ranges (`'Sept. 18 – Oct. 4 2026'`, `'Jan. 22 – Feb. 7, 2027'`, `'April 9 – 25 2027'`, `'June 11 – 27 2027'`), yielding zero events. Repairable (A005).
- **Checklist-flagged dead**: Barrel Proof Lounge — zero locally and upstream; checklist: "scraper dead ... repair or retire, investigate separately".
- **Duplicate producer, quiet member**: first-party Sweetwater (`sweetwater.py`) zero while `songkick_sweetwater` carries 4 events; Redwood Cafe Songkick zero while first-party `redwood_cafe.py` carries events and the checklist already ordered the Songkick interim removed.
- **Valid but quiet (Songkick venues with no current listings)**: Elephant in the Room, The Will Call, Rancho Nicasio, The Big Easy, Twin Oaks Roadhouse, The Fern Bar, Shady Oak Barrel House, THE 222, HenHouse Brewing. Zero both locally and upstream; not failures.
- **Quiet, needs a look**: Santa Rosa Arts Center — file exists, no events, no errors, locally and upstream.

Jack London Park logged `3` "No date found" warnings but still produced events (partial extraction, minor).

## F006 Twelve zero-event live feeds; six-plus are checklist-directed removals that never reached the feeds table

Zero-event live feeds locally, classified:

- **Dead, checklist ordered removal, still active in DB** (the export snapshot proves the rows persist): old Sonoma County DSA gcal (`dsasonomacounty@gmail.com` — the downloaded "ics" is a Google `Error 404` HTML page), Meetup Go Wild Hikers and Meetup Sonoma County Boomers (groups deleted), The Big Easy Tribe ICS (site replatformed; 33KB of past-only events), Sonoma Community Center `?ical=1` (0 bytes; `tribe_rest` scraper supersedes at 305 events locally), Santa Rosa Symphony `?ical=1` (0 bytes; `santa_rosa_symphony.py` supersedes), Redwood Cafe My Calendar ICS (checklist: broken per-event URLs; note it still emits ~10 events, so removal trades a little coverage for the first-party scraper).
- **Blocked/dead upstream ICS, no supersession yet**: Luther Burbank Center and Uptown Theatre Napa — both `?ical=1` URLs return an identical 75,193-byte `403 - Forbidden` HTML page saved as `.ics`; both are also `0` events in the upstream run. Sonoma County AA — empty reply locally and upstream (upstream validation flags it every run).
- **Expected/quiet**: "Jon" (personal my-picks feed), Meetup Women's Creativity Collective (checklist: dormant-not-dead, keep watching).
- **Malformed row artifact**: the duplicate North Bay Derby row's URL was downloaded as a 596KB HTML "ics" (0 events) — retired by A003.

The pattern to name: the checklist's "Remove via Manage Feeds" list from the last discovery pass was written but never executed. That is exactly the repo/DB reconciliation debt this clean pass exists to pay down (A006).

## F007 Local and upstream agree on structure; aggregate deltas are live drift

Upstream scheduled run 31142208913 (2026-08-07T02:45Z, Python 3.10.20): `51` feeds downloaded, `5588` combined, `5588` JSON, RSS full `5147` / latest `100`, upload inserted `5588` deleted `8`. Its scraper results table lists `16` zero-event warnings and the same two missing outputs (cafefrida, spreckels never appear). The local run (2026-08-07 ~12:35 local) matches the producer set, the failure pair, and the zero-event roster nearly one-for-one; local combined `5902` vs upstream `5588` (+314, ~5.6%) across a ~10-hour gap is live-source and dedup drift, not parity failure.

One real divergence: **Sonoma Community Center** (`tribe_rest.py`) produced `305` events locally but `0` upstream ("no events (but file exists)") — consistent with the REST API rate-limiting or blocking GitHub's datacenter IPs. Watch across the next upstream runs (A007).

## F008 Malformed DB scraper rows and doubled command prefixes

The mid-run DB export snapshot shows:

- `New World Ballet` — an active scraper row with an output path and **no command at all**; no workflow producer, no way to run it. Retire (in A003).
- A second `North Bay Derby` row whose output field is the literal page URL `https://www.northbayderby.org/events`; the feed downloader dutifully fetched 596KB of HTML as an `.ics`. Retire (in A003).
- Roughly two-thirds of scraper rows carry a doubled `cmd: cmd:` prefix in the export (e.g. `# cmd: cmd: python scrapers/barrel_proof.py`) — the legacy-prefix drift class that `a127740d2` had to work around. The rows the dry run does not propose to touch still carry it; worth normalizing when the narrow sync is applied so the export stops advertising stale prefixes.

# Actions

(A001/A002/A003/A005/A006 executed 2026-08-07 in the follow-up fix phase; row ids and evidence in the "Clean pass (2026-08-07)" section of `cities/santarosa/SOURCES_CHECKLIST.md`.)

- [x] A001 Retire the Cafe Frida producer and DB row — venue rebranded to Cafe Little Deer, no public events surface on the successor site (checked 2026-08-07). (agent)
- [x] A002 Rewrite the Spreckels scraper against the redesigned site (`/show/2026-27-season/` pages, Arts People ticketing); the Tribe REST API is gone. (human+agent)
- [x] A003 Apply the narrow safe subset of the sync dry run — retire New World Ballet and the malformed North Bay Derby row, normalize the Sonoma County Board of Supervisors command, reactivate Sonoma Valley Events — then re-export feeds.txt and rerun the audit. (human+agent)
- [ ] A004 Fix the 26 display-name mismatches at the source (explicit `--name`/`--source` in workflow commands, or sync logic that prefers DB names); do not apply the dry run's weak fallback names. (human+agent)
- [x] A005 Repair the Cinnabar date-range parser; four shows are skipped and the scraper yields zero events from a healthy upstream. (agent)
- [x] A006 Execute the checklist's pending Manage Feeds removals: old Sonoma County DSA gcal, Meetup Go Wild Hikers, Meetup Sonoma County Boomers, The Big Easy Tribe ICS, Redwood Cafe My Calendar ICS and Songkick interim, Sonoma Community Center `?ical=1`, Santa Rosa Symphony `?ical=1`. (human+agent)
- [~] A007 Review queue adjudicated 2026-08-07 (details in the "Adjudicated 2026-08-07 (A007 review queue)" section of `cities/santarosa/SOURCES_CHECKLIST.md`):
  - [x] Barrel Proof Lounge repaired — `/events/` `wfea_events` JSON, 291 events (was 0).
  - [x] Sweetwater Music Hall repaired — Python 3.10 ISO-offset parse fix, 33 events (was 0); Songkick duplicate kept per user decision.
  - [ ] Luther Burbank Center + Uptown Theatre Napa — REST conversion NOT viable: SiteGround serves `requests`/CI a PoW challenge + hard 403 (browser-only JSON; both already 0 in the upstream run). Feed rows kept; needs venue WAF allowlist or a headless-browser harness.
  - [ ] Sonoma County AA, sonoma.com, Santa Rosa Arts Center, 9 quiet Songkick venues, Sonoma Community Center REST (CI-quiet) — deliberately kept watching. (human+agent)

# Artifacts

- Local audit build report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.json`
- Local audit build log: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-build.log`
- Local feed report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-feeds.json`
- Local validation report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-validation.json`
- DB-export feeds.txt snapshot (mid-run, before restore): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/santarosa-feeds-db-export.txt`
- Upstream GitHub run (scheduled, same day): `https://github.com/judell/community-calendar/actions/runs/31142208913`
- Upstream run log (downloaded): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-logs/0_generate-calendar.txt`
