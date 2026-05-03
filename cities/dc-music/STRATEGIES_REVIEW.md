# DC Music — Strategies Review

Pass-2 review after Jon flagged that the original run leaned too heavily on
Songkick. Tested the other AGENTS.md / runbook strategies on the seed venues.

## Strategy results

| Strategy | Result | Notes |
|---|---|---|
| ICS curl-and-done at `/?ical=1` etc. | 1/22 | 6th & I only |
| WP Tribe REST API (`/wp-json/tribe/events/v1/events`) | 0/9 | None of the WP-detected venues run Tribe Events Calendar |
| WP custom `events` namespace (`/wp-json/events`) | 4 venues | I.M.P. flagship (9:30, Anthem, Lincoln, Atlantis) — but list endpoint blocked by Cloudflare; per-event ICS endpoint requires event_id |
| WP `/wp/v2/events` standard post type | 1 venue (Echostage) | Returns 3 events; **date in JSON is publish date, not event date** — would need slug parsing or per-event page fetch |
| **DICE link harvest** | **76 events on Songbyrd alone** | Songbyrd events page contains 76 `link.dice.fm/<id>` links; each redirects to a DICE page with full `MusicEvent` JSON-LD (name, startDate, location with geo) |
| DICE per-venue page (`dice.fm/venue/<slug>`) | 0 | URL pattern doesn't resolve; venue ID unknown |
| Eventbrite per-event JSON-LD | ✅ works as-is via existing `scrapers/eventbrite.py` | Despite expecting an organizer URL, the scraper's `/e/` regex matches the DC music search page directly. Verified 2026-05-03: 8 events from non-seed venues (BERHTA, Decades DC, Embassy of France, etc.) |
| Etix per-venue | untested | Black Cat (only Etix venue) returns 406 to all curl variants |
| TicketWeb event pages | 506 (bot block) | Howard Theatre uses TicketWeb; not scrapeable without anti-bot work |
| Ticketmaster Discovery API | ✅ works with key | Runs against existing `scrapers/ticketmaster.py` once `TICKETMASTER_API_KEY` (or `TICKETMASTER_KEY`) is in `.env`. For DC: 337 music events across 21 venues citywide; **mostly duplicates Songkick** at I.M.P. flagship venues (e.g. 9:30 Club: TM 92 vs Songkick 84). Only clear win: Kennedy Center (TM venue `ZFr9jZak17`) — 5 NSO concerts vs Songkick's 0. **Caveat:** TM's API serves literal `?` characters where UTF-8 should be (data corruption upstream); artist names like "Ren??e Fleming???s" come through ugly. |
| Tessitura (Atlas Performing Arts) | no public endpoint | Closed CRM |
| Custom Webflow `/shows/<slug>-<date>` (Howard) | scrapeable but partial | 70 shows visible on home; date is just `dd-mmm` in slug |
| Songkick venue pages (revisited with verification) | 14 strong / 4 marginal / 8 stale | See verification table below |

## Songkick verification (post-hoc)

I verified each Songkick venue page by fetching it and counting upcoming
concerts. Coverage varies dramatically:

**Strong (≥10 upcoming):**
- 9:30 Club (84), The Atlantis (58), The Anthem (49), DC9 (37), The Hamilton (29),
  Howard Theatre (27), Black Cat (26), Union Stage (25), Warner Theatre (24),
  Lincoln Theatre (23), Pearl Street (17), Pie Shop (16), Echostage (13),
  Capital One Arena (13)

**Marginal (5–10 upcoming):**
- Blues Alley (9), Comet Ping Pong (6), Rhizome DC (6), DAR Constitution Hall (6)

**Stale or empty (0–2 upcoming, despite venue being active):**
- Songbyrd (2), Lisner Auditorium (1), Atlas Performing Arts (0),
  JoJo Restaurant (0), Madam's Organ (0), Takoma Station (0),
  Bossa Bistro (0), Kennedy Center (0)

**The pattern**: Songkick captures **touring artists** (artists push their tour
dates to Songkick). It is functionally dead for venues whose programming is
**locally booked** (jazz clubs, neighborhood bars, DIY spaces, university
auditoriums). For Songbyrd specifically — an actively booked indie venue —
Songkick has 2 events while their own DICE-ticketed calendar has 76.

## Revised recommendations for `pending_feeds.txt`

### Drop these Songkick entries (stale / 0–2 events)

- Songbyrd → use DICE harvest instead
- Madam's Organ, JoJo, Takoma Station, Bossa, Atlas, Lisner — leave for a
  later pass with a different strategy
- Kennedy Center → Songkick is empty; their public programming needs a
  site-specific scraper

### Add (or replace) with these

- **Songbyrd** → write a DICE-link-harvest scraper:
  - fetch `https://www.songbyrddc.com/events/`
  - extract all `https://link.dice.fm/<id>` URLs
  - follow each to the DICE event page
  - parse `MusicEvent` JSON-LD (name, startDate, location)
  - This pattern is reusable for any DICE-ticketed venue.
- **DC9** → keep Songkick (37 strong) AND add DICE harvest as a supplement
  for local-programming events; DC9's home page exposes both
  `/event/<slug>/` URLs and `link.dice.fm/<id>` links.

### Worth investigating but not done in this run

- **Etix venue page** for Black Cat — Etix has venue-level pages
  (`etix.com/ticket/v/<venue_id>`); need to find the venue_id and check
  for JSON-LD or RSS. Black Cat blocks curl outright (406) so this
  needs WebFetch.
- **Howard Theatre's /shows pattern** — 70 events on homepage with
  date-in-URL; scrapeable via Webflow listing pattern. Songkick's 27 is
  decent but a direct scraper would cover more local programming.
- **Custom WP `events` namespace** for I.M.P. venues — the namespace
  exists and exposes `/wp-json/events/event-data.ics?event_id=X`. If we
  could enumerate event IDs (via the post-type list endpoint when not
  Cloudflare-blocked, or via the homepage), we could pull per-event ICS.
  Songkick is currently good enough for these (49–84 events each), so
  defer.
- **Eventbrite organic events** — Eventbrite's DC music search has 19
  events that aren't tied to seed venues (BERHTA, Decades DC, embassies).
  Per-event JSON-LD is rich. A scraper for Eventbrite DC music search
  would catch these.

## Stale runbook hints (for the runbook itself)

- Songkick metro 24426 → no longer exists; metro is `1409-us-washington`
  and offers no iCal subscription
- Resident Advisor `/events.xml?city=dc` → 404
- DICE `?city=washington-dc` JSON API → 404
- Ticketmaster Discovery API "no auth" → wrong; needs API key
- WordPress Tribe REST API as the primary fallback → not applicable to DC
  music venues; none use Tribe Events Calendar

## Bottom line

Pass 1's pending_feeds.txt should be revised: **drop the 8 stale Songkick
entries** and **replace Songbyrd's Songkick entry with a DICE-harvest
scraper invocation** (after the scraper is written). Net of revisions, the
honest count of viable feeds from this run drops from 26 to ~17, but those
17 are verified.
