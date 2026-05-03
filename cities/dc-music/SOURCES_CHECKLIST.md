# DC Music — Sources Checklist

Scope: District of Columbia proper (state = DC). Suburbs excluded.
Topic: live music — performance + recurring music programs.
Run: 2026-05-02, branch `judell/dc-music-discovery`.

## Seed venues — per-venue probe results

Tactics order: (1) ICS standard paths, (2) platform inspection, (3) ticketing platform, (4) JSON-LD harvest, (5) Songkick venue page.

| Venue | URL | Platform / signals | Strategy | Candidate feed | Status |
|---|---|---|---|---|---|
| 9:30 Club | https://www.930.com | WordPress + Ticketmaster (I.M.P.) | Songkick | `/venues/922-930-club` | working (scraper) |
| The Anthem | https://theanthemdc.com | WordPress + Ticketmaster (I.M.P.) | Songkick | `/venues/3552789-anthem` | working (scraper) |
| Lincoln Theatre | https://thelincolndc.com | WordPress + Ticketmaster (I.M.P.) | Songkick | `/venues/2826-lincoln-theatre` | working (scraper) |
| Black Cat | https://blackcatdc.com | Etix; site returns 406 to curl | Songkick | `/venues/1038-black-cat` | working (scraper) |
| DC9 | https://dc9.club | WordPress + DICE + Eventbrite | Songkick | `/venues/20843-dc9-nightclub` | working (scraper) |
| Songbyrd | https://www.songbyrddc.com | WordPress + DICE; Cloudflare 403 to curl | Songkick | `/venues/4420812-songbyrd-music-house` | working (scraper) |
| Pearl Street Warehouse | https://www.pearlstreetwarehouse.com | curl times out | Songkick | `/venues/3637839-pearl-street-warehouse` | working (scraper) |
| Union Stage | https://www.unionstage.com | curl times out | Songkick | `/venues/3623159-union-stage` | working (scraper) |
| The Atlantis | https://www.theatlantis.com | WordPress + Ticketmaster (I.M.P.) | Songkick | `/venues/4498657-atlantis` | working (scraper) |
| The Hamilton | https://thehamiltondc.com | Custom (Clyde's) | Songkick | `/venues/1611908-hamilton-live` | working (scraper) |
| Howard Theatre | https://thehowardtheatre.com | Unknown | Songkick | `/venues/74872-howard-theatre` | working (scraper) |
| 6th & I Synagogue | https://www.sixthandi.org | WordPress (Tribe) | direct ICS | `https://www.sixthandi.org/?ical=1` | working (30 events confirmed) |
| Kennedy Center | https://www.kennedy-center.org | Custom; 403 to curl | Songkick (partial) | `/venues/30332-john-f-kennedy-center-for-the-performing-arts` | working (scraper, music-only subset) |
| Blues Alley | https://www.bluesalley.com | Wix | Songkick | `/venues/10881-blues-alley` | working (scraper) |
| Echostage | https://www.echostage.com | WordPress + Ticketmaster | Songkick | `/venues/1864683-echostage` | working (scraper) |
| Bossa Bistro | https://bossadc.com | WordPress | Songkick | `/venues/633661-bossa-bistro-and-lounge` | working (scraper) |
| Phillips Collection | https://www.phillipscollection.org | Drupal | needs scraper | — | pending — Drupal events; check `/events/feed/json` |
| Smithsonian American Art | https://americanart.si.edu | Drupal | needs scraper | — | pending — Drupal "Take Five!" jazz series |
| National Gallery of Art | https://www.nga.gov | Custom; 403 to curl | needs scraper | — | pending — Sunday concerts series |
| Folger Shakespeare Library | https://www.folger.edu | Custom | needs scraper | — | pending — Folger Consort early-music |
| Library of Congress | https://www.loc.gov | Custom | needs scraper | — | pending — Concerts in the Coolidge series |
| Twins Jazz Lounge | (status unknown) | — | skip | — | non-starter — venue closed (per pre-2024 reports) |

### Methodology notes

- ICS curl probe (pass 1, root paths): `?ical=1`, `?mec-ical-feed=1`, `/events/feed/ical/`, `/calendar.ics`, `/events.ics`, `/feed/ical/`. Single hit: 6th & I.
- ICS curl probe (pass 2, `/events/?ical=1`): all 200-responses returned HTML, not ICS.
- Songkick search via WebFetch (curl returns 406 even with browser headers; LLM-mediated fetch worked).
- Songkick is the AGENTS.md-endorsed strategy for music venues with bot protection or ticketing-platform indirection (see Strategy 4). Scraper at `scrapers/songkick.py` extracts JSON-LD MusicEvent in a single fetch per venue.
- Per AGENTS.md: Bandsintown is **not viable** (Cloudflare-blocked, no public venue endpoint).

## Yelp / directory expansion — long-tail venues

**Yelp itself: blocked.** All curl and WebFetch attempts to Yelp returned
403 (Cloudflare + JS challenge). The runbook's Yelp-search step is
unworkable as written.

**Substitute used: `dcmusic.live/venues`** — DC's curated music-venue
directory listing ~135 venues across DC + suburbs. Acted as the analogue
of `northbaylivemusic.com/venues` (cited in AGENTS.md Strategy 2).

| Venue (new from directory) | DC proper? | Strategy attempted | Status |
|---|---|---|---|
| Warner Theatre | yes | Songkick `/venues/647-warner-theatre` | working (24 upcoming) |
| DAR Constitution Hall | yes | Songkick `/venues/1095-dar-constitution-hall` | marginal (6 upcoming) |
| Capital One Arena | yes | Songkick `/venues/3640349-capital-one-arena` | working (13 upcoming) |
| Lisner Auditorium (GW) | yes | Songkick `/venues/4628961-...` | stale (1 upcoming) — university programming |
| Atlas Performing Arts Center | yes | Songkick `/venues/678891-...` (0); site uses **Tessitura** (closed CRM) | stale; no public endpoint |
| Pie Shop (H Street) | yes | Songkick `/venues/3998914-pie-shop` | working (16 upcoming) |
| Comet Ping Pong | yes | Songkick `/venues/148048-comet-ping-pong` | marginal (6 upcoming) |
| Madam's Organ (Adams Morgan, blues) | yes | Songkick `/venues/267016-...` | stale (0); local programming, no Songkick |
| Rhizome DC (Takoma, DIY) | yes | Songkick `/venues/3342239-rhizome-dc` | marginal (6 upcoming) |
| Takoma Station Tavern (jazz) | yes | Songkick `/venues/2509689-...` | stale (0); local jazz |
| JoJo Restaurant and Bar (U Street, jazz) | yes | Songkick `/venues/4201654-...` | stale (0); local jazz |
| Bossa Bistro (Adams Morgan) | yes | Songkick `/venues/633661-...` | stale (0); local programming |
| Mr. Henry's (Capitol Hill, jazz) | yes | not on Songkick | needs custom scraper (weekly Capitol Hill Jazz Jam Wed 8-11pm) |
| Hill Center | yes | not on Songkick | needs site-specific scraper |
| Alexandria suburbs (Birchmere, Lighthorse, etc.) | no | — | excluded (out of scope) |
| Bethesda / Strathmore venues | no | — | excluded (out of scope) |
| Wolf Trap venues | no | — | excluded (Vienna VA) |

(See pass-2 verification details in `STRATEGIES_REVIEW.md`.)

## Aggregators (city-level)

Searches across the 13 aggregator categories (see runbook's "Aggregator
discovery — city-agnostic template" section). Probed 2026-05-02.

### General music aggregators
| Source | URL | Platform | Status |
|---|---|---|---|
| **dc.events/concerts/** | https://dc.events/concerts/ | WordPress + custom; 25 MusicEvent JSON-LD per page; **viable** | ✅ add as scraper |
| dcmusic.live | https://dcmusic.live/venues | Static directory, no event feed | used for venue discovery only |
| Bandsintown DC | https://www.bandsintown.com/c/washington-dc | Cloudflare 403 | ❌ not viable (per AGENTS.md known-limitations) |
| Songkick metro | https://www.songkick.com/metro-areas/1409-us-washington | No iCal subscription on metro page | ❌ per-venue Songkick is the only path |
| **Eventbrite DC music** | https://www.eventbrite.com/d/dc--washington/music--events/ | existing `scrapers/eventbrite.py` works against the search URL | ✅ ~8 events at long-tail venues (BERHTA, Decades DC, Embassy of France, etc.) |
| **Ticketmaster Discovery API** | per-venue via `--venue-id` | existing `scrapers/ticketmaster.py`; needs `TICKETMASTER_API_KEY` env var | ⚠️ duplicates Songkick at most DC venues; **Kennedy Center** is the unique win (5 NSO concerts; venue ID `ZFr9jZak17`). API serves mojibaked text — artist names look ugly |

### Local press
| Source | URL | Platform | Status |
|---|---|---|---|
| Washington City Paper events | https://washingtoncitypaper.com/events/ | Newspack; uses `newspack_lst_event` post type; `/wp-json/duet/events-list` returns `Basic Authorization not set` | ⚠️ basic-auth gated; the public listing page would need HTML scraping |
| WAMU events | https://wamu.org/events/ | Custom WP `/wp/v2/wamu_event` post type, returns 3 events | ⚠️ mostly talk-show events, not music |
| DCist topic/music | https://dcist.com/topic/music/ | Listing of music articles, no calendar | ❌ articles only |

### Genre societies
| Source | URL | Platform | Status |
|---|---|---|---|
| CapitalBop (jazz) | https://www.capitalbop.com/dcjazzcalendar/ | Custom JS calendar (Webpack bundle `calendar-CJks_du0.js`); HTML has no events | ⚠️ scrapeable only via JS-rendering or by reverse-engineering the bundle's data source |
| DCjazz.com | https://dcjazz.com | Newsletter promotional site | ❌ no public calendar |
| Potomac River Jazz Club | https://prjc.org | unchecked | pending |
| FSGW (folk) | https://fsgw.org/calendar | Custom HTML; no Tribe / wp-json / iCal / iframe | ❌ would need custom HTML scraper |
| WFMA folk events | https://wfma.net/DCEVENTS.htm | Static HTML page | ❌ would need custom scraper |
| Cathedral Choral Society | https://cathedralchoralsociety.org | unchecked | pending — single-org |
| Washington Chorus | unchecked | unchecked | pending — single-org |
| Washington Classical Review | unchecked | unchecked | pending |
| FMMC | https://fmmc.org | WordPress, no Tribe, no `?ical=1` | ❌ no public feed |

### Universities
- GW music school: pending (Lisner Auditorium covered partially via Songkick, 1 upcoming)
- Howard, Catholic, American, Georgetown, UDC: not investigated this run

### Library
- DCPL (Communico): `dclibrary.libnet.info/feeds/events` returns RSS but it's empty (1 placeholder item). Communico API discovery deferred.

### Church / sacred
- National Cathedral: `?ical=1` and other paths return 404
- Westminster Presbyterian (Friday jazz): connection failed (DNS/routing)
- 6th & I Synagogue: already in seed list (working ICS)

### Cultural institutes / embassies
- The Embassy Series: Wix site, JS-rendered events, no JSON-LD on the events page

### Open mic / jam aggregators
- Mr. Henry's Capitol Hill Jazz Jam (weekly Wed) — needs venue scraper
- DMV Open Mic Events (Facebook group) — not programmatically accessible
- openmikes.org / FireMics — not investigated (national platforms)

### Festival / presenter
- Washington Performing Arts: pending — covers Strathmore, Lisner, Songbyrd
- DC Jazz Festival: `?ical=1` returned HTML, not investigated further

### Community groups / school district / forums
- DCPS music programs: not investigated
- r/washingtondc threads: not investigated (manual scrape only)

## Non-starters

- **Twins Jazz Lounge** — venue listed in seed but reported closed in earlier sources. No current site/calendar.
- **Bandsintown** — platform-level non-starter per AGENTS.md (Cloudflare 403, no venue API endpoint).
- **Songkick metro feed** — `/metro-areas/1409-us-washington` no longer exposes an iCal subscription link (the runbook hint about metro 24426 is stale; per-venue scraper is the path).
