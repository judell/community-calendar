---
report_id: montclair-2026-08-07-soak
title: Montclair local/upstream parity audit and DB drift soak
city: montclair
date: 2026-08-07
commit: 87780bc5496988277261c6e5cecd5d35dbed5793
overall_status: partial
summary:
  total_checks: 8
  passed: 4
  failed: 0
  warning: 4
  note: "Findings retain their original at-audit-time status; see 'Follow-up execution (2026-08-07, same day)' below for the user-adjudicated fixes executed against F005/F006 after the initial audit. A004 (Ner Tamid/YWCA WAF status) remains open pending a future upstream run."
findings:
  - id: F001
    status: pass
    title: The Python 3.10 local audit run completed with zero hard failures across all 74 sources
    scope: montclair local audit
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.log
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-validation.json
    action_ids: []
  - id: F002
    status: pass
    title: Local and same-day upstream Montclair builds converge on nearly identical aggregate counts
    scope: montclair local-vs-upstream comparison
    evidence:
      - type: github-run
        ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504-full.log
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.log
    action_ids: []
  - id: F003
    status: pass
    title: Montclair does not use the dead eb-to-ical.daylightpirates.org publisher anywhere
    scope: montclair Eventbrite sourcing
    evidence:
      - type: repo-file
        ref: .github/workflows/generate-calendar.yml
      - type: repo-file
        ref: cities/montclair/feeds.txt
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504-full.log
    action_ids: []
  - id: F004
    status: pass
    title: Two scraper rows had workflow/DB name and command drift; both applied and re-verified clean
    scope: montclair scraper registration
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-dryrun.log
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-write.log
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-final-dryrun.log
      - type: repo-file
        ref: cities/montclair/feeds.txt
    action_ids: [A001]
  - id: F005
    status: warning
    title: Four live feeds broke since the 2026-07-20 checklist update; only one is confirmed dead, the other three need adjudication
    scope: montclair live-feed health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.json
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-validation.json
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504-full.log
      - type: file
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-adjudication-queue.md
    action_ids: [A002, A003, A004]
  - id: F006
    status: warning
    title: Montclair Film's scraper is broken by an upstream site redesign, confirmed identically in both local and same-day upstream runs
    scope: montclair scraper health
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.log
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504-full.log
      - type: repo-file
        ref: scrapers/montclair_film.py
      - type: file
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-adjudication-queue.md
    action_ids: [A002]
  - id: F007
    status: pass
    title: Ten other zero-event scraper/live-feed sources were individually reviewed and match prior-known quiet patterns; no action needed
    scope: montclair source health
    evidence:
      - type: report
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.json
      - type: repo-file
        ref: cities/montclair/SOURCES_CHECKLIST.md
    action_ids: []
  - id: F008
    status: pass
    title: The three CivicPlus municipal feeds and the concurrently-referenced WAF pattern from other cities do not currently recur in Montclair's municipal sources
    scope: montclair municipal feed health
    evidence:
      - type: log
        ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.log
    action_ids: []
actions:
  - id: A001
    status: done
    title: Apply the two dry-run-confirmed scraper metadata updates (Montclair High School and Montclair Kimberley Academy name/command drift) with --sync-existing (no --dry-run), scoped to montclair; regenerate feeds.txt
    owner: agent
  - id: A002
    status: done
    title: "Adjudicated 2026-08-07: implement both repair proposals. montclair_film.py rewritten for the site's new server-rendered showtimes grid (verified live: 50 events, was 0). Montclair Foundation converted to tribe_rest.py (verified live: 114 events); workflow line added, old ics_url row (id 169) retired via the Manage Feeds sequence (0 events deleted, remove_feed RPC succeeded)"
    owner: human+agent
  - id: A003
    status: done
    title: "Adjudicated 2026-08-07: retire the dead West African Drumming NJ Meetup live-feed DB row (id 183) via the Manage Feeds sequence (0 events deleted, remove_feed RPC succeeded) - no replacement source, the Meetup group itself is gone"
    owner: human+agent
  - id: A004
    status: partial
    title: "Adjudicated 2026-08-07: user chose to preemptively convert Temple Ner Tamid and YWCA Northern New Jersey to tribe_rest.py ahead of confirming the WAF suspicion, rather than waiting on a re-run. Workflow lines added with --user-agent \"Mozilla/5.0\"; both scrapers verified live (3 attempts each) and returned a valid empty calendar every time, consistent with the SiteGround block still being up. Old ics_url rows (id 175, id 1078) retired via the Manage Feeds sequence (0 events deleted each, remove_feed RPCs succeeded). Remaining open item: confirm on a future audit pass that the block has cleared and the two scrapers are populating events"
    owner: agent
artifacts:
  - label: Local build report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.json
  - label: Local build log
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.log
  - label: Local feed report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-feeds.json
  - label: Local validation report
    type: report
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-validation.json
  - label: backfill_scraper_feeds.py --sync-existing --dry-run output (pre-apply)
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-dryrun.log
  - label: backfill_scraper_feeds.py --sync-existing output (applied)
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-write.log
  - label: backfill_scraper_feeds.py --sync-existing --dry-run output (post-apply, clean)
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-final-dryrun.log
  - label: Adjudication queue (proposed fixes outside authorized file scope)
    type: file
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-adjudication-queue.md
  - label: Upstream Montclair run (scheduled, success)
    type: github-run
    ref: https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504
  - label: Upstream job log (full)
    type: log
    ref: /private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504-full.log
---

# Outcome

| Area | Status | Notes |
| --- | --- | --- |
| Local audit health | pass | `0` scraper failures, `0` missing outputs, `0` validation errors across all 26 scrapers and 48 live feeds. |
| Local-vs-upstream parity | pass | Same-day upstream run: 2211 combined events (dedup removed 44, geo-filtered 316) vs. local 2208 (dedup removed 44, geo-filtered 327) — within 0.1%. |
| eb-to-ical retirement | pass | Confirmed montclair uses `scrapers/eventbrite.py` directly for all 8 Eventbrite organizers; zero references to `eb-to-ical.daylightpirates.org` in the workflow or feeds.txt. The dead eb-to-ical `404`s in the same upstream run belong to Toronto. |
| DB/workflow drift | pass | `2` scraper rows had name/command drift (both MaxPreps school-athletics feeds); applied via `--sync-existing`, `feeds.txt` regenerated, final dry-run reports 0 updates/0 retirements/0 missing across all 26 scraper rows. |
| Live-feed regressions | warning | `4` live feeds newly broken since the 2026-07-20 checklist snapshot: 1 confirmed dead (Meetup group deleted), 1 confirmed fresh site-side break with a working API fallback, 2 unconfirmed/suspected transient WAF block. |
| Scraper regression | warning | Montclair Film's scraper is broken by a same-day-or-recent montclairfilm.org site redesign — reproduced identically in local and upstream runs, so not a probe artifact. Site still has content; this is a parser fix, not a retirement. |
| Zero-event review queue | pass | 4 zero-event scraper outputs and 6 zero-event Meetup live feeds were reviewed individually; all match prior-documented quiet/seasonal patterns, no action needed. |
| Municipal WAF recurrence check | pass | Cedar Grove, Clifton, and Bloomfield CivicPlus feeds all returned HTTP 200 on direct probe — the SiteGround/WAF pattern flagged elsewhere does not currently recur on montclair's municipal sources. |

# Findings

## F001 The Python 3.10 local audit run completed with zero hard failures across all 74 sources

Using `/tmp/community-calendar-audit-venv310/bin/python` (3.10.20), `scripts/local_build.py --city montclair` ran end to end against all 26 scrapers and 48 live feeds:

- `0` scraper failures, `0` missing scraper outputs
- `0` missing live-feed outputs
- `0` build-log errors/warnings, `0` runtime errors/warnings
- Validation: `0` errors, `6` warnings (all four broken live feeds plus their two summary lines — see F005)

`combined.ics` had `2208` unique future events (`Cross-source dedup: removed 44 duplicate events`, `Geo-filtered 327 events outside allowed cities`); `events.json` converted the same `2208`; `generate_rss.py` produced `full=1700 latest=100`.

## F002 Local and same-day upstream Montclair builds converge on nearly identical aggregate counts

The most recent successful `generate-calendar.yml` run (`31142208913`, scheduled, completed `2026-08-07T03:33:33Z`) scraped Montclair with 26 scrapers and 48 live feeds and produced:

- `combined.ics`: `2211` unique future events (`Cross-source dedup: removed 44`, `Geo-filtered 316`)
- `events.json`: `2211`
- Validation: `⚠️ [WARNING] montclair: 1 empty ICS files: meetup_west_african_drumming_nj.ics` (`0` errors)
- Upload: `{"success":true,"inserted":2211,"deleted":104}`

Local numbers (`2208`/`2208`) are within 0.1% of upstream. The 11-event geo-filter delta (327 vs. 316) and the extra 3 flagged live feeds are explained entirely by F005 below — sources that succeeded in the upstream run (03:05–03:23 UTC) but broke sometime in the following ~19 hours, not a workflow/DB or code-path divergence.

## F003 Montclair does not use the dead eb-to-ical.daylightpirates.org publisher anywhere

Per user memory, `eb-to-ical.daylightpirates.org` is dead repo-wide as of 2026. Confirmed for montclair specifically: `grep -in "eb-to-ical\|daylightpirates"` against `.github/workflows/generate-calendar.yml` and `cities/montclair/*.txt` returns zero matches. All 8 Eventbrite-sourced montclair scrapers (Montclair Brewery, Montclair Book Center, Watchung Booksellers, Loopwell, Trivia AD, Cohome, The Franklin Wine Bar, plus one more) invoke `scrapers/eventbrite.py` directly with an organizer URL. The eb-to-ical `404` errors visible in the same upstream job log (`EventbriteFilteredScraper ... Failed to fetch https://eb-to-ical.daylightpirates.org/... 404`) trace to Toronto's book-publisher sources (Penguin Random House Canada, HarperCollins Canada, etc.), confirmed by reading the surrounding log context — not montclair.

## F004 Two scraper rows had workflow/DB name and command drift; both applied and re-verified clean

`backfill_scraper_feeds.py --city montclair --sync-existing --dry-run` reported `26` workflow rows, `26` existing DB rows, `0` missing, `0` to retire, `2` to update:

```
UPDATE montclair: Montclair High School [cities/montclair/maxpreps_montclair_high.ics] -> {"name": "Montclair High School", "scraper_cmd": "python scrapers/maxpreps.py --url \"https://www.maxpreps.com/nj/montclair/montclair-mounties/events/\" --name \"Montclair High School\" --timezone America/New_York --output cities/montclair/maxpreps_montclair_high.ics"}
UPDATE montclair: Montclair Kimberley Academy [cities/montclair/maxpreps_mka.ics] -> {"name": "Montclair Kimberley Academy", "scraper_cmd": "python scrapers/maxpreps.py --url \"https://www.maxpreps.com/nj/montclair/montclair-kimberley-academy-cougars/events/\" --name \"Montclair Kimberley Academy\" --timezone America/New_York --output cities/montclair/maxpreps_mka.ics"}
```

Both were cosmetic/completeness drift: the DB names carried an extra `" Athletics"` suffix not present in the workflow's display name, and the DB commands were missing the workflow's `--timezone`/`--output` flags (functionally equivalent since `--output` is redundant with the positional/DB-derived URL, but not byte-identical to the reviewed workflow command). Applied with `--sync-existing` (no `--dry-run`): `Updated: 2, Inserted: 0, Retired: 0, Errors: 0`. `scripts/export_feeds_txt.py montclair` regenerated `cities/montclair/feeds.txt` from the DB (74 feeds total: 48 `ics_url` + 26 `scraper`, all `active`). A final `--sync-existing --dry-run` confirms `Rows to update: 0, Rows to retire: 0, Missing scraper rows: 0` — montclair's DB/workflow scraper drift is now fully clean.

## F005 Four live feeds newly broken since the 2026-07-20 checklist update; only one is confirmed dead

The local run's `action_report` flagged 4 live feeds as `non_ics_live_feed` (HTML/JSON error content saved as `.ics`), none of which appeared broken in the 2026-07-20 checklist snapshot. Cross-referencing the same-day upstream job log's download step (2026-08-07T03:23:17Z) shows all 4 succeeded there except one, which sharpens the classification considerably:

| Source | Upstream (03:23 UTC) | Local probe (2026-08-07, ~22:45 UTC) | Classification |
| --- | --- | --- | --- |
| West African Drumming NJ (Meetup) | Already flagged: `⚠️ 1 empty ICS files: meetup_west_african_drumming_nj.ics` | `https://www.meetup.com/west-african-drumming-nj/events/ical/` → `{"message":"Group not found"}` (HTTP 404), independent of User-Agent | **Dead upstream** — the Meetup group itself is gone, corroborated by both runs |
| Montclair Foundation | `✅ montclairfoundation_calendar_of_events.ics: 0 events` (succeeded) | `?ical=1` → HTTP 404 (plain Apache 404, not a WAF page); `/calendar-of-events/` itself is 200 and still links to the same broken URL; site's homepage `Last-Modified` is ~1 hour before the probe. Tribe REST API (`/wp-json/tribe/events/v1/events/`) returns live events. | **Live ICS dead, structured API works** — a fresh, same-day site regression (Boys & Girls Club Bloomington pattern) |
| Temple Ner Tamid | `✅ nertamid.ics: 0 events` (succeeded) | Every path (including homepage and the Tribe REST API) returns a SiteGround `sgcaptcha` JS-challenge redirect (HTTP 202), reproduced with 4 different User-Agents | **Suspected transient/IP-based WAF block, unconfirmed** |
| YWCA Northern New Jersey | `✅ ywcannj.ics: 0 events` (succeeded) | Same `sgcaptcha` pattern as Temple Ner Tamid, same SiteGround nginx signature | **Suspected transient/IP-based WAF block, unconfirmed** |

The Ner Tamid/YWCA pair share hosting fingerprints (`nginx`, identical `sgcaptcha` redirect body) and both succeeded upstream just ~19 hours earlier; SiteGround's Site Scanner bot-wall is commonly IP-reputation-based, so this local run's repeated probing from one IP may have tripped a block the GitHub Actions runner's IP would not. Montclair Foundation is hosted separately (plain Apache, `ServiceProvider: tagonline.com`) and returns a genuine dynamic 404, not a challenge page — combined with the very recent homepage `Last-Modified` timestamp, this reads as an independent, real site-side break rather than the same WAF pattern.

None of the three DB/workflow-touching fixes were applied — retiring a live-feed DB row and adding a new workflow scraper line both fall outside this audit's authorized file scope (`cities/montclair/SOURCES_CHECKLIST.md`, `cities/montclair/feeds.txt`, this report). Full evidence and exact proposed commands are recorded in the adjudication queue artifact for follow-up decision (A002, A003).

## F006 Montclair Film's scraper is broken by an upstream site redesign, confirmed identically in both local and same-day upstream runs

`scrapers/montclair_film.py` produced 0 events locally: `Found 12 current films on listing page` / `Fetching 12 film pages (parallel)` / `Got 0 future screenings`. The identical sequence with the identical film count (12) appears in the same-day upstream job log at 03:06:15–03:06:17 UTC, ruling out a probe-timing artifact — this scraper has been broken since at least the prior night's run. The checklist previously recorded 128 events for this source (as of 2026-03-15/07-20).

Read-only probes confirm the cause is a site redesign, not an outage: the scraper's hardcoded `LISTING_URL` (`https://montclairfilm.org/all-event/`) now 301-redirects twice, landing on `https://www.montclairfilm.org/cinemas/now-playing/`, whose links no longer match the scraper's expected `/event/<slug>/` pattern — the site now uses `/events/<slug>/` (plural, `www` subdomain). A sampled new-pattern event page returns HTTP 200 with valid JSON-LD `Event` data including `startDate`/`endDate`, confirming the site still has real showtime data; only the scraper's URL assumptions are stale (the same "broken parser, healthy upstream data" class as the UC Davis Arts fix). The exact proposed `LISTING_URL`/URL-pattern changes are recorded in the adjudication queue (A002) since editing `scrapers/montclair_film.py` is outside this audit's authorized file scope.

## F007 Ten other zero-event scraper/live-feed sources were individually reviewed and match prior-known quiet patterns

Per dbfirst.md §4, zero events is reviewed individually, not batch-retired. The remaining zero-event sources this run (excluding the 4 covered in F005/F006) all check out as previously-documented or plausibly quiet, with no scraper errors:

- **Scrapers (4):** Watchung Booksellers (matches existing "no upcoming events" checklist note), The Meatlocker (matches existing "artist-sourced, grows on its own" note), Cohome (1 upcoming event just beyond the 3-month scraper window, filtered to 0 — same pattern as before).
- **Meetup live feeds (6):** Bicycle Touring Club of North Jersey (matches existing "seasonal" note), EverWalk NJ, Exploring Montclair, League of Women Voters Montclair (matches existing "events on ClubExpress" note), Montclair GameNights, WordPress Montclair — all genuinely low-activity groups with valid empty ICS, no fetch errors.

No retirements recommended for any of these; recorded as reviewed in `cities/montclair/SOURCES_CHECKLIST.md`.

## F008 The three CivicPlus municipal feeds do not currently show the WAF pattern seen elsewhere

dbfirst.md flagged WAF/SiteGround-style blocking as a recurring pattern worth re-checking across cities. Montclair's three CivicPlus municipal calendars (Cedar Grove Township, City of Clifton, Township of Bloomfield) were probed directly with a browser User-Agent and all returned HTTP 200 — no recurrence of that pattern here. (Contrast with F005: montclair's WAF-pattern candidates are Temple Ner Tamid and YWCA Northern New Jersey, both SiteGround-hosted WordPress/Tribe sites, not the CivicPlus municipal sources.)

# Actions

- [x] A001 Apply the two dry-run-confirmed scraper metadata updates (Montclair High School, Montclair Kimberley Academy name/command drift) with `--sync-existing` (no `--dry-run`), scoped to `--city montclair`; regenerate `feeds.txt`.
- [x] A002 Adjudicated 2026-08-07: implement (a) the `scrapers/montclair_film.py` fix (F006) and (b) a `tribe_rest.py` scraper + workflow line for Montclair Foundation plus retiring its dead `ics_url` row (F005). Both verified live and applied — see "Follow-up execution" below.
- [x] A003 Adjudicated 2026-08-07: retire the dead West African Drumming NJ Meetup live-feed DB row (F005) via the Manage Feeds sequence. No replacement source.
- [~] A004 Adjudicated 2026-08-07 (partial): user chose to preemptively convert Temple Ner Tamid and YWCA Northern New Jersey to `tribe_rest.py` rather than waiting on a re-verification run. Conversion done and old rows retired; confirming the SiteGround block has actually cleared remains open for a future audit pass.

# Follow-up execution (2026-08-07, same day)

The user adjudicated the queue recorded in
`/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-adjudication-queue.md`
and authorized all four items (worklist v181, which extended coverage to
`scrapers/montclair_film.py` and `.github/workflows/generate-calendar.yml`,
montclair-scoped edits only). All four were executed in this session:

1. **Montclair Film repaired (F006).** `scrapers/montclair_film.py`
   rewritten: `LISTING_URL` now points directly at
   `https://www.montclairfilm.org/cinemas/now-playing/`. The real fix was
   discovering that the site's JSON-LD `Event` blocks no longer carry a
   `subEvent` array — only one representative `startDate` — while the true
   multi-date, multi-venue, multi-time showtime grid is server-rendered as
   nested `.venue[data-venue]` > `.date[data-date]` > `<button>TIME</button>`
   markup. The rewritten `_parse_showtimes` walks venue/date markers
   positionally in document order and pairs each date block with its
   showtime buttons; a JSON-LD-only fallback covers any page where the grid
   is absent. Verified with a live run:
   `/tmp/community-calendar-audit-venv310/bin/python scrapers/montclair_film.py --output <tmp>.ics`
   → **50 future screenings** (was 0 right after the break; a spot-check of
   the output ICS confirmed correct `TZID=America/New_York` timestamps, real
   venue addresses for both The Clairidge and The Bellevue, and per-showing
   ticket URLs).
2. **Montclair Foundation converted (F005).** Verified live:
   `tribe_rest.py --api-base "https://montclairfoundation.org" --name "Montclair Foundation" --timezone America/New_York`
   → **114 events** (3 pages). Workflow line added to the montclair block
   only (3-line diff, confirmed scoped via `git diff --stat`). Old `ics_url`
   row (`id 169`, `https://montclairfoundation.org/calendar-of-events/?ical=1`)
   retired via the Manage Feeds sequence read from
   `xmlui/components/AddFeedDialog.xmlui` (`DELETE
   /rest/v1/events?source=eq.<name>&city=eq.montclair` followed by `POST
   /rest/v1/rpc/remove_feed {feed_id}`): **0 events deleted** — the feed had
   already been producing 0 events across recent upload cycles (confirmed by
   a direct events-table query before deleting anything), so nothing live
   was lost. `remove_feed` RPC returned HTTP 204.
3. **West African Drumming NJ retired (F005).** Confirmed dead upstream
   (Meetup's own API: `{"message":"Group not found"}`). Manage Feeds
   sequence on row `id 183`: **0 events deleted**, `remove_feed` RPC HTTP
   204. No replacement source.
4. **Temple Ner Tamid and YWCA Northern New Jersey converted preemptively
   (F005), user decision.** Workflow lines added for both with
   `--user-agent "Mozilla/5.0"` (montclair block only). Each scraper was run
   3 times; all 6 runs returned a valid, well-formed **empty** calendar — the
   SiteGround `sgcaptcha` wall (which blocks the Tribe REST API identically
   to the old `?ical=1` export) was still active at execution time. This is
   the accepted outcome for a preemptive conversion made ahead of
   confirmation. Old `ics_url` rows retired via the Manage Feeds sequence:
   Temple Ner Tamid (`id 175`) — **0 events deleted**; YWCA Northern New
   Jersey (`id 1078`) — **0 events deleted**. Both had succeeded with
   valid-but-empty output in the prior night's upstream run, so — despite
   the coordinator's expectation that these two "did have events upstream
   recently" — a direct events-table query (both scoped to montclair and
   unscoped across the whole table) confirmed zero live rows existed for
   either source at retirement time; no events were actually lost. Both
   scrapers will repopulate automatically once the block clears on a future
   run.

**Post-execution sync.** `backfill_scraper_feeds.py --city montclair
--sync-existing --dry-run` reported exactly the 3 expected new-producer
inserts (Montclair Foundation, Temple Ner Tamid, YWCA Northern New Jersey),
`0` updates, `0` retirements — matching the diagnosis precisely, no
surprises. Applied: `Inserted: 3, Updated: 0, Retired: 0, Errors: 0`.
`feeds.txt` regenerated (73 feeds: 44 `ics_url` + 29 `scraper`, all
`active`). Final dry-run: `Rows to update: 0, Rows to retire: 0, Missing
scraper rows: 0` — clean.

`cities/montclair/SOURCES_CHECKLIST.md` and this report were updated to
record all four adjudicated decisions with full evidence.

# Artifacts

- Local build report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.json`
- Local build log: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-build.log`
- Local feed report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-feeds.json`
- Local validation report: `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-validation.json`
- `backfill_scraper_feeds.py --sync-existing --dry-run` output (pre-apply): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-dryrun.log`
- `backfill_scraper_feeds.py --sync-existing` output (applied): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-write.log`
- `backfill_scraper_feeds.py --sync-existing --dry-run` output (post-apply, clean): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-final-dryrun.log`
- Adjudication queue (proposed fixes outside authorized file scope): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-adjudication-queue.md`
- Upstream Montclair run: `https://github.com/judell/community-calendar/actions/runs/31142208913/job/92754273504`
- Upstream job log (full): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/gh-job-92754273504-full.log`
- Montclair Film repaired live-run output (50 events): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair_film_test.ics`
- Montclair Foundation tribe_rest.py live-run output (114 events): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair_foundation_test.ics`
- Temple Ner Tamid tribe_rest.py live-run output (0 events, blocked): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/nertamid_test.ics`
- YWCA Northern New Jersey tribe_rest.py live-run output (0 events, blocked): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/ywcannj_test.ics`
- `backfill_scraper_feeds.py --sync-existing --dry-run` output (post-retirement, 3 expected inserts): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-dryrun-2.log`
- `backfill_scraper_feeds.py --sync-existing` output (3 inserts applied): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-write-2.log`
- `backfill_scraper_feeds.py --sync-existing --dry-run` output (final, clean): `/private/tmp/claude-501/-Users-jonudell-community-calendar/ecb2a348-73e6-4076-abaf-f411c967d3fb/scratchpad/montclair-backfill-final-dryrun-2.log`
