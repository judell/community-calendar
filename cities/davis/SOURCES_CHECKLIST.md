# Davis Calendar Source Checklist

Prioritized list of event sources for the Davis community calendar.

## Currently Implemented

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| UC Davis AggieLife | CampusGroups ICS | ~606 | Student org events via `aggielife.ucdavis.edu` |
| UC Davis Library | Localist ICS | ~118 | `events.library.ucdavis.edu/calendar/1.ics` |
| Davis Downtown | Tribe ICS | ~5 | WordPress Events Calendar plugin |
| UC Davis Athletics | Scraper | ~309 | Sidearm sports schedule feed |
| UC Davis Arts | Scraper | ~2 current | Monthly ICS feeds, normalized malformed all-day dates on 2026-08-06 |
| Yolo County Library | Scraper | ~104 | LibCal RSS filtered to Davis branches |
| UU Davis | Scraper | ~11 future / 2300+ raw | Google Calendar aggregation; dead sub-calendar removed 2026-08-06 |
| The Dirt | Tribe ICS | ~19 | Davis & Yolo arts/culture magazine |
| Visit Davis | Tribe ICS | ~14 | Official tourism events |
| Visit Yolo | Tribe ICS | ~30 | County-wide tourism |
| Putah Creek Council | Tribe ICS | ~5 | Environmental org |
| Hate-Free Together | Tribe ICS | ~12 | Community and social justice events |
| Davis Bike Club | Google Calendar ICS | ~107 | Cycling rides and events |
| Indivisible Yolo | Mobilize scraper | ~110 | `mobilize.py` civic and political organizing |
| ~~Davis Chamber~~ | ~~Scraper~~ | ~16 former | Removed 2026-08-06: `web.davischamber.com` no longer resolves locally or in GitHub Actions |
| ~~Mondavi Center~~ | ~~Scraper~~ | — | Removed 2026-08-06: site now returns 403 Forbidden to scraper requests upstream and locally |
| ~~Eventbrite~~ | ~~Scraper~~ | — | Retired 2026-02-15: scraper broken, no public feeds |

## Meetup Groups

Discovered 2025-02-08. Found 29 groups, 10 with active events.

### Added

| Group | Events | Category | Notes |
|-------|--------|----------|-------|
| mosaics | 10 | Cultural | Lunar New Year, language classes |
| intercultural-mosaics | 10 | Cultural | Davis-based cultural events |
| yolo-county-board-game-gathering | 10 | Social | Weekly Game Night at Blue Note (Woodland) |
| pence-adult-art-programs | 3 | Arts | Artist talks and workshops at Pence Gallery |
| art-in-action | 2 | Arts | Davis art events |
| mindful-embodied-spirituality | 10 | Wellness | Yoga and conscious conversations |
| winters-shut-up-and-write-meetup-group | 1 | Writing | Nearby Winters |

### Online-only / Not Added

- `mosaics-zoom` — Zoom language classes
- `womens-sci-fi-fantasy-book-club-online` — online book club
- `PlayYourCourt-Davis-Tennis` — may be commercial

## Discovery Run: 2026-02-08

### Tribe ICS Feeds Added 2026-03-07

All five use standard `?ical=1` export.

| Source | URL | Events | Notes |
|--------|-----|--------|-------|
| The Dirt | `thedirt.online/events/?ical=1` | ~19 | Davis and Yolo arts/culture magazine |
| Visit Davis | `visitdavis.org/events/?ical=1` | ~14 | Official tourism events |
| Visit Yolo | `visityolo.com/event/?ical=1` | ~30 | County-wide tourism, some overlap with Visit Davis |
| Putah Creek Council | `putahcreekcouncil.org/events/?ical=1` | ~5 | Environmental org, outdoor events |
| Hate-Free Together | `hatefreetogether.org/events/?ical=1` | ~12 | Community and social justice events |

### Highest-Value Uncaptured Source

| Source | Platform | Status | Notes |
|--------|----------|--------|-------|
| **UC Davis Events (events.ucdavis.edu)** | Localist | BLOCKED | Cloudflare 403. Would add a large campus-wide event layer beyond AggieLife student-org events |

## Easy Wins

Machine-readable feeds ready to use if they become relevant.

| Source | URL | Feed Type | Priority | Notes |
|--------|-----|-----------|----------|-------|
| Pence Gallery | `pencegallery.org/exhibitions-events` | RSS | High | RSS feed exists but was empty when checked |
| UU Church Davis | `uudavis.org/calendar` | Google Calendar | High | Embedded Google Calendar already harvested |
| Davis Farmers Market | `davisfarmersmarket.org` | Unknown | Medium | May have hidden ICS, but no usable feed found so far |

### UU Davis Embedded Calendar IDs

Working IDs currently used by the scraper:

```text
uudavis@gmail.com
l7ct33327vaeffd8iu8ij0hjdg@group.calendar.google.com
da9geoarq2p3o4ukb8vqseat8g@group.calendar.google.com
```

Removed from the scraper on 2026-08-06 because it returned `404`:

```text
0p5ed7hbg4p7b4atf3lgjmgic@group.calendar.google.com
```

## Structured HTML / Higher-Effort Sources

### Higher Priority

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| Manetti Shrem Museum | `manettishremmuseum.ucdavis.edu/events` | Custom | Medium | Art exhibitions and events |
| UC Davis Athletics | `ucdavisaggies.com/calendar` | Sidearm | Medium | Already implemented |
| Davis Chamber | `web.davischamber.com/events` | MemberClicks | Removed 2026-08-06 | Upstream host no longer resolves, so unfixable for now |

### Medium Priority

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| Davis Food Co-op | `davisfood.coop/events` | Custom | Low | Classes and tastings |
| Sophia's Thai Kitchen | `sophiastkitchen.com/events` | Unknown | Low | Live music venue |
| Woodstock's Pizza | `woodstocksdavis.com/events` | Unknown | Low | Music nights |
| UC Davis Extension | `extension.ucdavis.edu/events` | Custom | Medium | Workshops and continuing ed |
| UC Davis Main Events | `ucdavis.edu/events` | Drupal | Medium | Campus-wide aggregator |

### Lower Priority

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| Hattie Weber Museum | `hattiewebermuseum.org/events` | Unknown | Low | Small local history |
| Davis Community Church | `dccpres.org/events` | Unknown | Low | Community events |
| Armadillo Music | `armadillomusic.com/pages/events` | Unknown | Low | Music event links |

## Schools And Government

| Source | URL | Platform | Effort | Notes |
|--------|-----|----------|--------|-------|
| DJUSD Calendar | `djusd.net/about/calendar` | SharpSchool | High | District calendar, complex platform |
| Davis Senior High | `dshs.djusd.net/activities` | SharpSchool | High | Sports and performances |
| Da Vinci Charter | `davincicharter.org/calendar` | Unknown | Medium | May have Google Calendar backend |
| Davis Senior Center | `cityofdavis.org/.../senior-services` | Blocked | High | CDN blocks requests |
| City of Davis | `cityofdavis.org/city-hall/city-calendar` | Blocked | N/A | Akamai access denied |

## Recreation And Clubs

| Source | URL | Type | Notes |
|--------|-----|------|-------|
| Davis Bike Club | `davisbikeclub.org/rides-events` | HTML | Timeout issues in some checks, but public Google Calendar feed works |
| Whole Earth Festival | `wholeearthfestival.org` | Seasonal | Annual event, check when active |

## Non-Starters / Dead Ends

| Source | Reason |
|--------|--------|
| Davis Community Network (`dcn.org`) | DNS fails, defunct |
| DAWN (Davis Area Women's Network) | DNS fails, defunct |
| KDVS Radio | Next.js site, no calendar feed |
| UC Davis Arboretum | No ICS feed |
| Davis Farmers Market | No export; schedule covered elsewhere |
| Davis Enterprise | TownNews platform, no ICS |
| Davis Patch | JS-rendered, no ICS |
| Yolo County Library master feed | LibCal only exposes event-by-event ICS; scraper required |
| DJUSD feeds | SharpSchool, no usable feed |
| LUGOD (Linux Users Group) | One event from 2019, inactive |
| Tockify / Help Me Grow Yolo | No Davis events, all Woodland/West Sac |
| Meetup: `davis-activity-partners` | Zero events, inactive |
| Meetup: `tuleyome-home-place-adventures` | Invalid feed signature |
| Tree Davis | No calendar feed (Elementor, no Tribe) |
| Valley Clean Energy | Tribe page exists but `?ical=1` returns HTML |
| The Davis Community (`thedaviscommunity.org`) | Actually Wilmington, NC |
| Davis Arts Center | No feed found |
| DMTC (Musical Theatre) | Google Calendar embed but no public ICS URL |
| Manetti Shrem Museum | Cloudflare 403 block |
| LUGOD ICS feed | Timeout, likely dead |
| Davis CAN | Squarespace, per-event ICS only |
| International House Davis | WP Events Plugin ICS, but only 2020 events |
| Poetry in Davis | Mod_Security blocks `?ical=1` |
| Davis Yoga Collective | No ICS feed |
| Davis Day Hikers (Meetup) | Only one event, barely active |
| Faith Community Church | ChurchCenter, 404 on ICS |
| Davis Community Church | No ICS feed |
| Islamic Center of Davis | No ICS feed |
| Town Planner Davis | No ICS feed |
| Mondavi Center | Removed 2026-08-06: site returns 403 to scraper requests upstream and locally |
| Davis Chamber | Removed 2026-08-06: `web.davischamber.com` no longer resolves locally or in GitHub Actions |

## Implementation Roadmap

### Phase 1

1. `UU Davis` Google Calendar extraction
2. `Pence Gallery` blocked: RSS empty, My Calendar API disabled, likely needs HTML scraper

### Phase 2

3. `Mondavi Center` removed on 2026-08-06 due to 403s
4. `Manetti Shrem Museum` blocked by Cloudflare Turnstile and currently shows no events
5. `Davis Chamber` removed on 2026-08-06 because the upstream host no longer resolves

### Phase 3

6. `UC Davis Athletics` implemented via Sidearm
7. `Davis Food Co-op` blocked by captcha redirect

### Phase 4

8. `Sophia's Thai Kitchen` has no structured event calendar
9. `Woodstock's Pizza` "events" page is just weekly deals, not real event listings

### Phase 5

10. `DJUSD` has export affordances but no subscribable feed URL, so it would need scraping or manual refresh

## Recently Investigated

### UC Davis Main Events (`ucdavis.edu/events`)

- Status: no RSS or ICS found
- Platform: Drupal 10 (SiteFarm theme)
- Checked common Drupal feed paths such as `/events/rss`, `/events/feed`, `/events.xml`; they returned HTML or `404`
- No `?_format=rss` support observed
- Would need an HTML scraper

### Davis Enterprise (`davisenterprise.com/events`)

- Status: RSS exists but is rate-limited
- Feed URL: `https://www.davisenterprise.com/search/?f=rss&t=article&c=events&l=50&s=start_time&sd=desc`
- Platform: TownNews / BLOX CMS
- Uses Evvnt for event display
- Feed returned "Too Many Requests" during checks

### Explorit Science Center (`explorit.org`)

- Status: Wix site, no standard feeds
- Events page: `https://www.explorit.org/about-3`
- Home page said programming was paused when checked
- Would require a more expensive dynamic scraper if it becomes relevant

## Notes

- `Visit Davis` and `Visit Yolo` overlap; both use The Events Calendar
- `events.ucdavis.edu` would be the biggest win if Cloudflare access can be resolved
- The 2026-08-06 Davis cleanup fixed `UC Davis Arts`, removed the dead UU Davis sub-calendar, and retired the broken Davis Chamber source
