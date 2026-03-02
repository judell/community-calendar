# Montclair NJ Sources Checklist

## Currently Implemented (22 sources, ~1240 events)

| Source | Type | Events | Status |
|--------|------|--------|--------|
| Montclair State University | CampusLabs ICS | 817 | ✅ Ready |
| Montclair Public Library | LibCal ICS | 161 | ✅ Ready |
| Montclair Film | JSON-LD scraper | 128 | ✅ Ready |
| Essex County Parks | JSON API scraper | 90 | ✅ Ready |
| Montclair Foundation / Van Vleck | WordPress ICS | 30 | ✅ Ready |
| Lackawanna Station | Squarespace scraper | 27 | ✅ Ready |
| Montclair Local News | WordPress ICS | 24 | ✅ Ready |
| North Essex Chamber of Commerce | GrowthZone scraper | 12 | ✅ Ready |
| Montclair Brewery | Eventbrite scraper | 10 | ✅ Ready |
| West African Drumming NJ | Meetup ICS | 10 | ✅ Ready |
| South Mountain Conservancy | Meetup ICS | 6 | ✅ Ready |
| Montclair Book Center | Eventbrite scraper | 5 | ✅ Ready |
| Wellmont Theater | Songkick JSON-LD scraper | 4 | ✅ Ready |
| Wharton Arts | WordPress ICS | 4 | ✅ Ready |
| Montclair High School Athletics | MaxPreps scraper | 2 | ✅ Ready |
| Metrotrails Hiking | Meetup ICS | 2 | ✅ Ready |
| Studio Montclair | WP REST API scraper | 1 | ✅ Ready |
| Exploring Montclair | Meetup ICS | 1 | ✅ Ready |
| Montclair GameNights | Meetup ICS | 1 | ✅ Ready |
| NJ Code & Coffee | Meetup ICS | 1 | ✅ Ready |
| PEAK Performances at MSU | WordPress ICS | 1 | ✅ Ready |
| Watchung Booksellers | Eventbrite scraper | 0 | ✅ Ready (no upcoming events) |

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
| WordPress Montclair | wordpress-montclair-meetup | Not tested |

## Needs Scraper — Probably Expensive / Brittle
| Source | URL | Platform | Notes |
|--------|-----|----------|-------|
| Montclair Art Museum | montclairartmuseum.org/events | Cloudflare protected | |

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

## Potential Additional Sources — Community/Civic
- [ ] Montclair YMCA (montclairymca.org - class schedules, special events)
- [ ] Montclair Farmers' Market (static recurring: Saturdays 8am-2pm, Walnut St)
- [ ] Montclair Community Farms
- [ ] Montclair Kimberley Academy (MaxPreps - private school athletics)

## Potential Additional Sources — Faith
- [ ] Congregation Shomrei Emunah, Bnai Keshet, Temple Ner Tamid (check for calendar pages)
- [ ] First Congregational Church (fccmontclair.org) — also hosts Outpost in the Burbs concerts
- [ ] Unitarian Universalist of Montclair (uumontclair.org)

## Potential Additional Sources — Long-Tail Music Venues
Most are Facebook/Instagram-only; listed here for future reference if platforms open up.
- [ ] Outpost in the Burbs (Wix + Thundertix, no feed; ~monthly folk/singer-songwriter concerts)
- [ ] DLV Lounge (Facebook-only; jazz Wed-Sat since 1972)
- [ ] The Meatlocker (Instagram @meatlockershows; DIY punk/metal, shows most nights)
- [ ] Just Jake's (Wix; live music Fri-Sat)
- [ ] Tierney's Tavern (live music Fri-Sat; Bandsintown 403)
