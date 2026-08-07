---
report_id: toronto-2026-08-07-soak
title: Toronto source-health soak (local audit + dry-run drift comparison)
city: toronto
date: 2026-08-07
commit: 81200105484254a68c053aaabcde79723e820137
overall_status: partial
summary:
  total_checks: 11
  passed: 2
  failed: 2
  warning: 7
findings:
  - id: F001
    status: pass
    title: The Python 3.10 local audit run completed with no scraper hard failures and no missing scraper outputs
    scope: toronto local audit
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log
    action_ids: []
  - id: F002
    status: warning
    title: The audit reported 29 drift items; the dry-run resolves them to 3 name updates and 14 retirements, with full 80/80 workflow-to-DB producer parity on output paths
    scope: toronto workflow/DB drift
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-backfill-dryrun.txt
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.json
    action_ids: [A001]
  - id: F003
    status: fail
    title: All 8 eventbrite_filtered publisher sources are dead in both environments because the eb-to-ical.daylightpirates.org backend returns 404
    scope: toronto scraper health
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913
    action_ids: [A002]
  - id: F004
    status: fail
    title: Fourteen legacy URL-keyed DB scraper rows corrupt the local audit build, including an HTML clobber of blogto.ics that destroyed 1016 scraped events
    scope: toronto DB metadata integrity
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log
      - type: repo-file
        ref: cities/toronto/feeds.txt
    action_ids: [A001, A007]
  - id: F005
    status: warning
    title: Five live ICS endpoints are dead in both local and GitHub runs (Cecil Community Centre, Factory Theatre, Toronto Knitters Guild, UofT Knox College, UofT Social Work)
    scope: toronto live feed health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.json
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913
    action_ids: [A003]
  - id: F006
    status: warning
    title: Eight live feeds return HTML pages instead of ICS while being reported as benign zero-event feeds
    scope: toronto live feed health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.json
    action_ids: [A004]
  - id: F007
    status: warning
    title: Several sources are environment-split - blocked or crashing in GitHub Actions but healthy locally (blogTO, The Annex Residents' Association, York University, UofT sub-calendars)
    scope: toronto local-vs-upstream comparison
    evidence:
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log
    action_ids: [A005]
  - id: F008
    status: warning
    title: Aga Khan Museum and UofT have narrow date-parse warnings with otherwise healthy upstream data
    scope: toronto parser health
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log
    action_ids: [A006]
  - id: F009
    status: warning
    title: Roughly 36 sources are valid-but-quiet zero-event producers needing periodic review only
    scope: toronto source health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.json
    action_ids: [A008]
  - id: F010
    status: warning
    title: Local totals (6224 combined) trail the same-day GitHub run (6960) mainly because the TPL Bibliocommons scrapers under-fetched locally, not because of parity drift
    scope: toronto local-vs-upstream comparison
    evidence:
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log
    action_ids: []
  - id: F011
    status: pass
    title: No orphan static ICS files - every tracked toronto file is configuration or inventory; all ICS outputs are generated
    scope: toronto static file audit
    evidence:
      - type: repo-file
        ref: cities/toronto/feeds.txt
    action_ids: []
actions:
  - id: A001
    status: done
    title: Apply the reviewed backfill sync for toronto (retire the 14 legacy URL-keyed scraper rows, apply the 3 name updates), re-export feeds.txt, and rerun the audit
    owner: agent
  - id: A002
    status: done
    title: Convert the 8 eventbrite_filtered publisher sources to a working Eventbrite path (scrapers/eventbrite.py pattern) or retire them, removing the dead eb-to-ical dependency
    owner: human+agent
  - id: A003
    status: done
    title: Confirm and retire the five dead live ICS endpoints (Cecil, Factory Theatre, Knitters Guild, Knox, Social Work) or find replacement endpoints
    owner: human+agent
  - id: A004
    status: done
    title: Review the eight HTML-returning feeds and convert to scrapers or retire per source (adjudicated 2026-08-07 - 4 converted to tribe_rest, 4 retired)
    owner: human+agent
  - id: A005
    status: done
    title: Decide handling for CI-blocked sources (adjudicated 2026-08-07 - environment splits accepted as policy, documented in checklist; Trinity SSL stays an open review item)
    owner: human+agent
  - id: A006
    status: done
    title: Narrowly repair the Aga Khan Museum date-fragment parsing (three recurring unparseable formats)
    owner: agent
  - id: A007
    status: deferred
    title: Harden local_build.py - do not export URL-keyed scraper rows as live feeds, guard against output-filename collisions, and fix validation misattributing all 8 EventbriteFiltered errors to each publisher
    owner: agent
  - id: A008
    status: deferred
    title: Periodic review of the valid-but-quiet zero-event sources (16 Meetup feeds, Luma collections, Eventbrite organizers, TCDSB, City Planning Consultations)
    owner: human+agent
artifacts:
  - label: Local audit report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.json
  - label: Local build log
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log
  - label: Local feed report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-feeds.json
  - label: Local validation report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-validation.json
  - label: Backfill dry-run output
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-backfill-dryrun.txt
  - label: Same-day upstream GitHub run
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31142208913
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Local audit health | pass | `0` scraper hard failures, `0` missing scraper outputs, `0` runtime issues on Python 3.10.20. |
| Scraper parity | warning | `80/80` workflow producers exist in the DB keyed by output path; `29` drift items reduce to `3` name updates + `14` retirements of legacy URL-keyed duplicates (dry-run only, nothing applied). |
| Hard-broken sources | fail | `8` eventbrite_filtered publishers dead via the retired eb-to-ical service; `14` malformed DB rows corrupt the local build (blogto.ics clobber). |
| Dead endpoints | warning | `5` live ICS endpoints fail in both environments; `8` more return HTML masquerading as "0 events". |
| Review queue | warning | ~`36` valid-but-quiet zero-event sources; environment-split sources (blogTO, UofT, York, Annex) need a policy decision. |
| Remote/local comparison | warning | Local `6224` combined vs upstream `6960` same day; dominated by TPL Bibliocommons under-fetch locally, not parity drift. |

# Findings

## F001 The local audit run is structurally healthy

The 2026-08-07 local run (Python 3.10.20 parity venv) completed end to end:

- `80` workflow scrapers ran, `0` hard failures, `0` missing outputs
- combined `6224` unique future events from `142` source files; events.json `6224`; RSS `full=6024 latest=100`
- cross-source dedup removed `791`; geo filter removed `297`
- `0` runtime issues; the runner exits nonzero only because action items remain open

## F002 Drift: 29 audit items, but the real delta is 3 updates + 14 retirements

`backfill_scraper_feeds.py --city toronto --sync-existing --dry-run` reports:

- Workflow scraper rows: `80`; existing in DB: `80`; missing: `0` (full producer parity on output-path keys)
- `3` UPDATE rows (display-name normalization from output `X-SOURCE`): `University of Toronto` (`cities/toronto/uoft_events.ics`), `City of Toronto Meetings` (`cities/toronto/toronto_meetings.ics`), `City of Toronto Festivals & Events` (`cities/toronto/toronto_festivals.ics`)
- `14` RETIRE rows — legacy scraper rows keyed by website URL instead of output path: A Different Booklist, Bakka Phoenix Books, Ben McNally Books (Bookmanager), Queen Books (Bookmanager), Flying Books, blogTO, Coach House Books, Cormorant Books, Book*hug Press, House of Anansi, Diaspora Dialogues, Penguin Random House Canada, HarperCollins Canada, Simon & Schuster Canada

Every one of the 14 duplicates a producer that already has a correct output-path-keyed row, so the retirements look safe; each should still be eyeballed at apply time. The audit's other `15` "name mismatch" fix items (Ocad U vs OCAD University, Tpl Preschool vs Toronto Public Library — Preschool, etc.) are heuristic noise: the DB name is canonical and the workflow line simply lacks `--name`, so the filename-derived label differs. The dry run proposes no change for them. Tracked `cities/toronto/feeds.txt` is a stale export (182 entries vs 207 in the DB; it lacks the newer rows such as York University and `uoft_events.ics`); the next export will refresh it.

## F003 eventbrite_filtered is dead: the eb-to-ical backend is gone

All `8` publisher sources (Penguin Random House Canada, HarperCollins Canada, Simon & Schuster Canada, Diaspora Dialogues, House of Anansi, Coach House Books, Cormorant Books, Book*hug Press) fetch `https://eb-to-ical.daylightpirates.org/eventbrite-organizer-ical?organizer=...`, which returns `HTTP 404` on every call in both the local run and the upstream run. These are the only ERROR-class lines in the local build log (8 total). This is the known-dead eb-to-ical service (Montclair hit the same wall in 2026); `scrapers/eventbrite.py` is the working replacement pattern. Class: broken shared helper, upstream data (Eventbrite organizer pages) still healthy.

## F004 The 14 legacy rows actively corrupt the local audit build

Because their `url` field is a website URL, the local runner's DB export writes the 14 rows into the live-feeds section of the temporary `feeds.txt`, where the download step fetches each URL as if it were a calendar and saves raw HTML into `cities/toronto/` (`adifferentbooklist.ics` 3.7 KB HTML, `eventbrite_o_*.ics` 138–155 KB HTML each, `shop.ics` written twice by two different bookstores, etc.). Worst case: the row for blogTO derives the output filename `blogto.ics` — the same file the real `scrapers/blogto.py` had just written with `1016` events — and overwrites it with a 91 KB HTML page, so blogTO contributed `0` events to the local combine. The upstream build is unaffected because `download_feeds.py` there reads the DB directly and skips scraper-type rows. The A001 retirements remove the data cause; A007 hardens the runner against the pattern.

## F005 Five live ICS endpoints are dead in both environments

Failed to download (or produced a 0-byte file) both locally and in upstream run 31142208913:

- Cecil Community Centre (`cecilcentre.ca` ai1ec exporter) — missing output in both
- Factory Theatre (`factorytheatre.ics` 0 bytes)
- Toronto Knitters Guild (`torontoknittersguild.ics` 0 bytes)
- UofT Knox College (`knox.ics` 0 bytes)
- UofT Social Work (`socialwork.ics` 0 bytes)

Class: upstream gone / consistently inaccessible in both environments — retire candidates per the Davis Chamber pattern, pending a quick human check for replacement endpoints.

## F006 Eight "zero-event" live feeds actually return HTML

These download "successfully" and are counted as benign zero-event feeds, but the saved files contain HTML, not ICS:

- Buddies in Bad Times Theatre, High Park Nature Centre, Scadding Court Community Centre, Toronto Dance — each exactly `75193` bytes of identical-size HTML (likely a shared platform error page)
- NOW Toronto (38 KB HTML), Ontario Nature (112 KB HTML), Jewel Envy (787 B HTML)
- GardenOntario — a Cloudflare "Just a moment" challenge page

Upstream shows the same `0 events` for these, so the breakage is real, not environmental. Class: dead ICS endpoint; several are Tribe/WordPress sites where a REST-API scraper conversion (Boys & Girls Club pattern) may recover events.

## F007 Environment-split sources: healthy locally, broken in Actions (or vice versa)

- **blogTO**: upstream gets `HTTP 403` on every day fetched (runner IP blocked) and contributes 0; locally the scraper collected `1016` events (then lost them to the F004 clobber).
- **The Annex Residents' Association**: upstream crashed with `ValueError: Expected published recurring board-meeting rule not found` at 03:01Z; the local run at 12:45 PT succeeded with 2 events. Transient upstream page state or flaky markup.
- **York University** (`events.yorku.ca`, downloads as the URL-derived filename `events.ics`): failed upstream ("empty or failed"), succeeded locally with `6958` raw / `236` future events.
- **UofT sub-calendars**: upstream 403'd on 7 sub-calendars (CDTPS, CANSSI, Entrepreneurship, Arts & Science, Events, Environment, Hart House); locally only Hart House 403'd. Trinity College fails on an SSL verification error in both.

Class: environment-dependent access, not source death. Needs a policy decision (headers/UA, retries, accept the CI gap) rather than retirement.

## F008 Narrow parser warnings with healthy upstream data

- Aga Khan Museum: 3 recurring unparseable date fragments (`Doors Open • May 23, 2026`, `August 28 • 8 pm August 29 • 8 pm ...`, `November 18`) — identical warnings upstream; scraper still yields ~15 events. UC Davis Arts-style narrow repair candidate.
- UofT: 1 unparseable date (`Now - Aug 13, 2026`).

## F009 Valid-but-quiet zero-event sources (~36) — review, don't retire

Zero events with a syntactically valid empty calendar and no errors:

- `16` Meetup feeds (Civic Tech, Hiking Network, Improv, Little Sunbeams, Mindful Movement, Mini + Me, Python Toronto, SAI Dham, 3D Printing, Canoe Trippers, Dads Group, JavaScript, Paddlers, Photography, Postgres, Wellness)
- Eventbrite organizer scrapers: The Rosedale Centre, Hand Eye Society, Forest Bathing Club, Fuzzy Lab Toronto, Open Studio, Being and Becoming, Radical Aliveness Toronto, Head Out Toronto, All About Intimacy
- Luma collections: Toronto Social Mixer, Toronto Tech Week, Devtools Toronto, Intuit Open Source Meetup
- Civic scrapers: City Planning Consultations, TCDSB Meetings (both valid empty output; plausibly quiet in August)

Per the playbook these are recorded for periodic review only; an empty valid calendar may just be quiet.

## F010 Local vs upstream totals: live drift, not parity drift

Same-day comparison (upstream scheduled run 31142208913, 02:45Z):

| Metric | Local | Upstream |
| --- | --- | --- |
| Combined events | 6224 | 6960 |
| events.json | 6224 | 6960 |
| RSS full / latest | 6024 / 100 | 6791 / 100 |
| Cross-source dedup removed | 791 | 936 |
| Geo-filtered | 297 | 296 |
| Combine source files | 142 | 127 |

The gap is dominated by the TPL Bibliocommons scrapers fetching fewer pages locally (School Age `312` vs `906`; Teens `97` vs `637`; no errors logged — likely rate limiting or pagination variance), partially offset by York University working locally (+236) while failing upstream. Geo-filter agreement (297 vs 296) confirms pipeline parity.

## F011 No orphan static ICS

Tracked files under `cities/toronto/` are inventory/config only (`feeds.txt`, `SOURCES_CHECKLIST.md`, `LUMA_HOSTS.md`, `city.conf`, `geo_allowlist.txt`, `bookstore_venue_denylist.txt`, `pending_feeds.txt` template). Every `.ics` present is an untracked generated output. Pass.

# Actions

- [x] A001 Apply the reviewed backfill sync for toronto (retire the 14 legacy URL-keyed scraper rows, apply the 3 name updates), re-export feeds.txt, and rerun the audit.
- [x] A002 Convert the 8 eventbrite_filtered publisher sources to a working Eventbrite path (scrapers/eventbrite.py pattern) or retire them, removing the dead eb-to-ical dependency.
- [x] A003 Confirm and retire the five dead live ICS endpoints (Cecil, Factory Theatre, Knitters Guild, Knox, Social Work) or find replacement endpoints.
- [x] A004 Review the eight HTML-returning feeds and convert to scrapers or retire per source. Adjudicated 2026-08-07: converted Buddies in Bad Times (REST 7), High Park Nature Centre (15), Scadding Court (157), Jewel Envy (18, flowing) to `tribe_rest.py`; retired Toronto Dance, Ontario Nature, NOW Toronto, GardenOntario (all 0 events, rows removed). The three SiteGround sites' `tribe_rest.py --user-agent` patch landed the same day (flag added to scraper, workflow lines, and DB commands); local re-verification still hit the transient sgcaptcha interstitial after this network's probe bursts, so first event counts are expected from the next CI run.
- [x] A005 Decide handling for CI-blocked sources. Adjudicated 2026-08-07: environment splits (blogTO 403 in Actions, York upstream failure, UofT sub-calendar 403s) accepted as policy and documented in the checklist maintenance log; Trinity SSL remains an open review item.
- [x] A006 Narrowly repair the Aga Khan Museum date-fragment parsing.
- [ ] A007 Harden local_build.py: do not export URL-keyed scraper rows as live feeds, guard output-filename collisions, fix validation misattributing all 8 EventbriteFiltered errors to each publisher.
- [ ] A008 Periodic review of the valid-but-quiet zero-event sources.

# Artifacts

- Local audit report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.json`
- Local build log: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-build.log`
- Local feed report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-feeds.json`
- Local validation report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-validation.json`
- Backfill dry-run output: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/toronto-backfill-dryrun.txt`
- Same-day upstream GitHub run: `https://github.com/judell/community-calendar/actions/runs/31142208913`
