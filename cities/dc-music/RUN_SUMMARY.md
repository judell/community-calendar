# DC Music Discovery — Run Summary

**Run date:** 2026-05-02
**Branch:** `judell/dc-music-discovery`
**Runbook:** `~/.agents/scout/projects/dc-music-discovery.md`
**Mode:** Unattended (skip-permissions, auto)

## Outcome

**26 candidate feeds** written to `pending_feeds.txt`, all DC proper:

- 1 direct ICS feed (curl-and-done): 6th & I Synagogue
- 25 Songkick scraper invocations (per-venue JSON-LD MusicEvent)

The Songkick scraper at `scrapers/songkick.py` exists and matches the documented
calling convention. Each `# cmd:` entry is ready for `add_scraper.py` to wire
into the workflow.

## Breakdown by tactic

| Tactic | Hits | Notes |
|---|---|---|
| ICS curl-and-done (`?ical=1` etc.) | 1 | 6th & I Synagogue, 30 events confirmed |
| Songkick venue page (JSON-LD) | 25 | 15 from seed list + 10 long-tail |
| JSON-LD harvest (custom) | 0 | Not needed; Songkick covers music venues |
| Yelp directory pass | 0 | Yelp blocked (403); used dcmusic.live instead |
| Aggregator iCal | 0 | All city-level aggregator feeds blocked or stale |
| Topical search | 0 | Not pursued — directory pass covered the gap |

## Sources of evidence

- **dcmusic.live/venues** — DC's curated music venue directory (~135 listings).
  This is the DC analogue of `northbaylivemusic.com/venues` (cited in
  AGENTS.md Strategy 2). No machine-readable feed itself, but excellent for
  long-tail venue discovery.
- **Songkick** — primary source for music-venue event data per AGENTS.md
  Strategy 4 ("Artist-sourced data"). All 25 venue lookups via WebFetch
  (curl returns 406 even with browser headers — appears to require JS or
  TLS fingerprint matching).
- **DuckDuckGo** — directory lookup that surfaced dcmusic.live.

## Venues that need a scraper (no curl-and-done feed found)

These DC seed venues have music programming but no public ICS and aren't on
Songkick. Each would need a site-specific scraper:

- **Phillips Collection** — Sunday Concerts series (Drupal site)
- **Smithsonian American Art Museum** — "Take Five!" jazz series (Drupal)
- **National Gallery of Art** — Sunday concerts (custom CMS, 403 to curl)
- **Folger Shakespeare Library** — Folger Consort early music
- **Library of Congress** — Concerts in the Coolidge series

Lower-priority pending: National Cathedral (organ + choral), DC Public
Library (Communico platform — found `/feeds/events` RSS but it's empty;
needs investigation of the actual Communico API).

## Notable misses / runbook hints that were stale

- **Songkick metro 24426** (the runbook hint for a Washington DC city-level
  ICS subscription): the metro page is now `/metro-areas/1409-us-washington`
  and no longer offers an iCal subscription link. Per-venue scraper is the
  only Songkick path now.
- **Resident Advisor `/events.xml?city=dc`**: returns 404. The page form
  `/events/us/washingtondc` is 403-blocked.
- **DICE `?city=washington-dc` JSON API**: 404; old hint stale.
- **Yelp**: 403 to all WebFetch and curl, including with browser headers.
  `dcmusic.live/venues` was a much better long-tail source anyway.
- **Bandsintown**: as AGENTS.md "Known Platform Limitations" predicted, 403
  Cloudflare. Not viable.

## What got skipped (out of unattended scope)

- DC Jazz Festival (https://dcjazzfest.org) — `?ical=1` returned HTML, not ICS
- Hirshhorn Museum, National Cathedral, Westminster Presbyterian (Friday
  jazz vespers), Hill Center — would each need site-specific investigation
- 50+ additional small DC venues from dcmusic.live (restaurants/bars with
  occasional music) — diminishing returns; Songkick was checked for the
  highest-priority subset and most aren't listed there

## Stop conditions met

- [x] `cities/dc-music/pending_feeds.txt` — 26 entries, ready for review
- [x] `cities/dc-music/SOURCES_CHECKLIST.md` — populated with venue-by-venue outcomes
- [x] `cities/dc-music/city.conf` — DC proper geo-filter
- [x] `cities/dc-music/RUN_SUMMARY.md` — this file
- [x] No push to remote
- [x] No commits to `main`
- [x] No deploys, no Supabase mutations
- [x] No new scrapers written (existing `scrapers/songkick.py` covers all 25 Songkick entries)

## What a human reviewer should look at before merging

1. **Double-check Kennedy Center on Songkick** — entry covers Songkick-listed
   ticketed concerts only. The Millennium Stage's free daily program isn't
   on Songkick and would need a separate scraper. Decide whether partial
   coverage is acceptable.
2. **Decide on the "needs scraper" venues** — Phillips Collection, SAAM,
   NGA, Folger, LOC. These are prestige venues but may not have enough
   music programming volume to justify per-site scrapers. A single
   Smithsonian-wide approach might cover SAAM + Hirshhorn + NGA at once
   if their events go through a common platform.
3. **Verify Songkick coverage quality** — spot-check a few of the long-tail
   venues (Comet Ping Pong, JoJo) by running `scrapers/songkick.py --test`
   to confirm they actually have upcoming events listed. Some smaller
   venues may have stale Songkick pages.
4. **Cloudflare-protected venues retry**: Songbyrd, Pearl Street, Union
   Stage all had curl issues. They're now covered via Songkick — but if
   Songkick coverage turns out thin for any of them, falling back to
   their ticketing platform (DICE for Songbyrd/Pearl Street, See Tickets
   for some others) would be the next move.
