# Davis, CA Calendar Source Checklist

## Currently Implemented

### Scraped Sources
| Source | Scraper | Events | Notes |
|--------|---------|--------|-------|
| UC Davis AggieLife | CampusGroups ICS | ~606 | Student org events |
| UC Davis Library | Localist ICS | ~118 | Library events |
| Davis Downtown | tribe_events ICS | — | Downtown events |
| Mondavi Center | Scraper | — | Performing arts |
| UC Davis Athletics | Scraper | — | Sports events |
| UC Davis Arts | Scraper | — | Arts events |
| Yolo County Library | Scraper | — | Library events |
| UU Davis | Scraper | — | Unitarian Universalist |
| Davis Chamber | Scraper | — | Chamber of commerce |
| ~~Eventbrite~~ | ~~Scraper~~ | — | Retired 2026-02-15: scraper broken, no public feeds |
| The Dirt | tribe_events ICS | ~19 | Davis & Yolo arts/culture magazine |
| Visit Davis | tribe_events ICS | ~14 | Official tourism events |
| Visit Yolo | tribe_events ICS | ~30 | County-wide tourism |
| Putah Creek Council | tribe_events ICS | ~5 | Environmental org |
| Hate-Free Together | tribe_events ICS | ~12 | Community/social justice |
| Davis Bike Club | Google Calendar ICS | ~107 | Cycling rides & events |

### Meetup Groups (Discovered 2025-02-08)
| Group | Events | Notes |
|-------|--------|-------|
| mosaics | — | Community arts |
| intercultural-mosaics | — | Cultural exchange |
| yolo-county-board-game-gathering | — | Board games |
| pence-adult-art-programs | — | Art classes |
| art-in-action | — | Art workshops |
| mindful-embodied-spirituality | — | Meditation/spirituality |
| winters-shut-up-and-write-meetup-group | — | Writing group |

---

## Discovery Run: 2026-02-08

### tribe_events ICS Feeds (Added 2026-03-07)

All 5 use standard `?ical=1` export — added to workflow as curl downloads:

| Source | URL | Events | Notes |
|--------|-----|--------|-------|
| The Dirt | `thedirt.online/events/?ical=1` | ~19 | Davis & Yolo County arts/culture magazine |
| Visit Davis | `visitdavis.org/events/?ical=1` | ~14 | Official tourism events |
| Visit Yolo | `visityolo.com/event/?ical=1` | ~30 | County-wide tourism (some overlap with Visit Davis) |
| Putah Creek Council | `putahcreekcouncil.org/events/?ical=1` | ~5 | Environmental org, outdoor events |
| Hate-Free Together | `hatefreetogether.org/events/?ical=1` | ~12 | Community/social justice events |

### Highest-Value Uncaptured Source

| Source | Platform | Status | Notes |
|--------|----------|--------|-------|
| **UC Davis Events (events.ucdavis.edu)** | Localist | BLOCKED | Cloudflare 403. Would have hundreds of campus events complementing AggieLife student org events |

### Dead Ends (2026-02-08)

| Source | Reason |
|--------|--------|
| Davis Community Network (dcn.org) | DNS fails, defunct |
| DAWN (Davis Area Women's Network) | DNS fails, defunct |
| KDVS Radio | Next.js site, no calendar feed |
| UC Davis Arboretum | No ICS feed |
| Davis Farmers Market | No export (listed on Visit Davis instead) |
| Davis Enterprise | TownNews platform, no ICS |
| Davis Patch | JS-rendered, no ICS |
| Yolo County Library | LibCal, individual event ICS only, no master feed |
| DJUSD (Davis schools) | SharpSchool, no feed |
| LUGOD (Linux Users Group) | 1 event from 2019, inactive |
| Tockify / Help Me Grow Yolo | No Davis events (all Woodland/West Sac) |
| Meetup: davis-activity-partners | 0 events, inactive |
| Meetup: tuleyome-home-place-adventures | Invalid feed signature |
| Tree Davis | No calendar feed (Elementor, no tribe_events) |
| Valley Clean Energy | tribe_events but ?ical=1 returns HTML |
| The Davis Community (thedaviscommunity.org) | Actually Wilmington, NC — wrong city |
| Davis Arts Center | No feed found |
| DMTC (Musical Theatre) | Google Calendar embed, no public ICS URL |
| Manetti Shrem Museum | Cloudflare 403 block |
| LUGOD ICS feed | Timeout, likely dead |
| Davis CAN | Squarespace, per-event ICS only |
| International House Davis | wp-events-plugin ICS but only 2020 events, stale |
| Poetry in Davis | Mod_Security blocks ?ical=1 |
| Davis Yoga Collective | No ICS feed |
| Davis Day Hikers (Meetup) | Only 1 event, barely active |
| Faith Community Church | churchcenter.com, 404 on ICS |
| Davis Community Church | No ICS feed |
| Islamic Center of Davis | No ICS feed |
| Town Planner Davis | No ICS feed |

---

## Notes

- Visit Davis and Visit Yolo have overlap; both use The Events Calendar
- events.ucdavis.edu would be the biggest win if Cloudflare access can be resolved
- All new feeds are WordPress tribe_events with native ICS export
