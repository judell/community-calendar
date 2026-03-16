# Montclair NJ Sources Checklist

## Currently Implemented (47 sources)

| Source | Type | Events | Status |
|--------|------|--------|--------|
| Montclair State University | CampusLabs ICS | 817 | ✅ Ready |
| MSU Red Hawks Athletics | Sidearm ICS | 176 | ✅ Ready |
| Montclair Public Library | LibCal ICS | 161 | ✅ Ready |
| Montclair Film | JSON-LD scraper | 128 | ✅ Ready |
| Essex County Parks | JSON API scraper | 90 | ✅ Ready |
| Congregation Shomrei Emunah | TeamUp ICS | 80 | ✅ Ready |
| Montclair Foundation / Van Vleck | WordPress ICS | 30 | ✅ Ready |
| MHA of Essex and Morris | WordPress ICS | 30 | ✅ Ready |
| Union Congregational Church | WordPress ICS | 30 | ✅ Ready |
| Temple Ner Tamid | WordPress ICS | 30 | ✅ Ready |
| Lackawanna Station | Squarespace scraper | 27 | ✅ Ready |
| Montclair Local News | WordPress ICS | 24 | ✅ Ready |
| North Essex Chamber of Commerce | GrowthZone scraper | 12 | ✅ Ready |
| Montclair Brewery | Eventbrite scraper | 10 | ✅ Ready |
| West African Drumming NJ | Meetup ICS | 10 | ✅ Ready |
| Let's Walk!! | Meetup ICS | 10 | ✅ Ready |
| The Mindful Stream | Meetup ICS | 10 | ✅ Ready (virtual) |
| NJ Bowling, Volleyball, Tennis & More | Meetup ICS | 8 | ✅ Ready |
| Northeast Earth Coalition | WordPress ICS | 8 | ✅ Ready |
| South Mountain Conservancy | Meetup ICS | 6 | ✅ Ready |
| Montclair Book Center | Eventbrite scraper | 5 | ✅ Ready |
| Wellmont Theater | Songkick JSON-LD scraper | 4 | ✅ Ready |
| Wharton Arts | WordPress ICS | 4 | ✅ Ready |
| Montclair High School Athletics | MaxPreps scraper | 2 | ✅ Ready |
| Metrotrails Hiking | Meetup ICS | 2 | ✅ Ready |
| Loopwell | Eventbrite scraper | 1 | ✅ Ready |
| EverWalk NJ | Meetup ICS | 1 | ✅ Ready |
| Studio Montclair | WP REST API scraper | 1 | ✅ Ready |
| Exploring Montclair | Meetup ICS | 1 | ✅ Ready |
| Montclair GameNights | Meetup ICS | 1 | ✅ Ready |
| NJ Code & Coffee | Meetup ICS | 1 | ✅ Ready |
| PEAK Performances at MSU | WordPress ICS | 1 | ✅ Ready |
| First Congregational Church | Google Calendar ICS | * | ✅ Ready |
| UU Congregation of Montclair | Google Calendar ICS | * | ✅ Ready |
| Montclair Kimberley Academy | MaxPreps scraper | * | ✅ Ready |
| Watchung Booksellers | Eventbrite scraper | 0 | ✅ Ready (no upcoming events) |
| League of Women Voters Montclair | Meetup ICS | 0 | ✅ Ready (events on ClubExpress) |
| Turtle Back Zoo | WP REST API scraper | 42 | ✅ Ready |
| NJ Audubon | WordPress ICS | 30 | ✅ Ready |
| The Raptor Trust | Squarespace per-event ICS | 4 | ✅ Ready |
| Bicycle Touring Club of NJ | Meetup ICS | 0 | ✅ Ready (seasonal) |
| Indivisible One NJ | Mobilize.us scraper | 3 | ✅ Ready — `mobilize.py` civic/political organizing (added 2026-03) |
| Board Gamers of Greater Nutley | Meetup ICS | 10 | ✅ Ready (added 2026-03-15) |
| Board Game Night at Verona Inn | Meetup ICS | 6 | ✅ Ready (added 2026-03-15) |
| WordPress Montclair | Meetup ICS | 10 | ✅ Ready (added 2026-03-15) |
| Cloud Data Driven | Meetup ICS | 4 | ✅ Ready (added 2026-03-15) |
| Trivia AD | Eventbrite scraper | 121 | ✅ Ready (added 2026-03-15) |
| Montclair History Center | Squarespace scraper | 13 | ✅ Ready (added 2026-03-15) |

\* Google Calendar feeds include historical events; pipeline filters to future only.

## Key Aggregators (potential allies)
| Aggregator | URL | Notes |
|------------|-----|-------|
| Experience Montclair / Montclair Center | experiencemontclair.org | Vibemap platform, no public API, submission-driven |
| Patch Montclair | patch.com/new-jersey/montclair/calendar | Proprietary, best scraping target of the three |
| TAPinto Montclair | tapinto.net/towns/montclair/events | Proprietary, returns 403 on fetch |
| The Montclair Girl | themontclairgirl.com | Editorial roundup ("75+ events this weekend"), not structured |
| Eventbrite | eventbrite.com | Many local organizers use it; platform-level source |

## Meetup Groups - Tested, No Current Events
| Group | Slug | Notes |
|--------|------|-------|
| Montclair Entrepreneurs | montclair-entrepreneurs | 0 events (2026-03-01) |
| Living Mindfully | Say-Yes-To-Your-Life-Montclair | 0 events (2026-03-01) |
| WordPress Montclair | wordpress-montclair-meetup | ✅ Added (10 events) |

## Needs Scraper — Probably Expensive / Brittle
| Source | URL | Platform | Notes |
|--------|-----|----------|-------|
| Montclair Art Museum | montclairartmuseum.org/events | Cloudflare + Incapsula | Dead end for scraping; needs direct outreach |

## Non-Starters
| Source | Reason |
|--------|--------|
| Township of Montclair (Legistar) | Legistar API returns "ConnectionString not set up" |
| Township of Montclair (website) | CivicPlus/CivicLive, returns 403 on all API probes and direct page fetches |
| Township Recreation | CommunityPass registration platform, no feed |
| Lifelong Montclair (seniors) | SchedulesPlus, no feed |
| MSU main calendar (Trumba) | ICS download returns 410 Gone (deprecated by admin) |
| MSU LibCal | Calendar IDs not publicly exposed, subscription feed locked |
| Vibemap / Experience Montclair | Closed commercial SaaS, no public API |
| Out Montclair | WordPress/Tribe Events, empty feed (0 events) |
| Churches (Planning Center) | No public API; Redeemer Montclair & Montclair Community Church both use it |
| Trumpets Jazz Club | Closed September 2021, building sold |
| Out & Active NJ (Meetup) | 404 — group not found (2026-03-15) |
| Montclair D&D (Meetup) | 404 — group not found (2026-03-15) |
| NJ Linux User Group (Meetup) | 404 — group not found (2026-03-15) |
| WineStyles Montclair (Eventbrite) | No organizer page on Eventbrite (2026-03-15) |
| MC Hotel (Eventbrite) | Venue only, no organizer page (2026-03-15) |
| Montclair Comedy Festival (Eventbrite) | No dedicated organizer; small comedy orgs have 1 event each (2026-03-15) |
| Pride Center of NJ | Duda platform, stale events (last Oct 2025), no structured feed (2026-03-15) |

## Potential Additional Sources — Community/Civic
- [ ] Montclair YMCA (montclairymca.org - class schedules, special events)
- [ ] Montclair Farmers' Market (Squarespace, seasonal Saturdays at Walnut St)
- [ ] Montclair Community Farms (Squarespace, kids programs)
- [x] Montclair History Center — ✅ Added via Squarespace scraper (13 events, 2026-03-15)
- [ ] Montclair Culinary Academy (Squarespace, cooking classes)

## Potential Additional Sources — Faith
- [ ] Bnai Keshet (site returns 406, no feed found)
- [ ] Outpost in the Burbs (Wix + ThunderTix, no feed; concerts at FCC)

## Potential Additional Sources — Long-Tail Music Venues
Most are Facebook/Instagram-only; listed here for future reference if platforms open up.
- [ ] Outpost in the Burbs (Wix + Thundertix, no feed; ~monthly folk/singer-songwriter concerts)
- [ ] DLV Lounge (Facebook-only; jazz Wed-Sat since 1972)
- [ ] The Meatlocker (Instagram @meatlockershows; DIY punk/metal, shows most nights)
- [ ] Just Jake's (Wix; live music Fri-Sat)
- [ ] Tierney's Tavern (live music Fri-Sat; Bandsintown 403)
