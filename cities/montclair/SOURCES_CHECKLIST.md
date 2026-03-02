# Montclair NJ Sources Checklist

## Currently Implemented (18 sources, ~1106 events)

| Source | Type | Events | Status |
|--------|------|--------|--------|
| Montclair State University | CampusLabs ICS | 817 | ✅ Ready |
| Montclair Public Library | LibCal ICS | 161 | ✅ Ready |
| Montclair Foundation / Van Vleck | WordPress ICS | 30 | ✅ Ready |
| Lackawanna Station | Squarespace scraper | 27 | ✅ Ready |
| Montclair Local News | WordPress ICS | 24 | ✅ Ready |
| North Essex Chamber of Commerce | GrowthZone scraper | 12 | ✅ Ready |
| Montclair Brewery | Eventbrite scraper | 10 | ✅ Ready |
| West African Drumming NJ | Meetup ICS | 10 | ✅ Ready |
| South Mountain Conservancy | Meetup ICS | 6 | ✅ Ready |
| Montclair Book Center | Eventbrite scraper | 5 | ✅ Ready |
| Wharton Arts | WordPress ICS | 4 | ✅ Ready |
| Montclair High School Athletics | MaxPreps scraper | 2 | ✅ Ready |
| Metrotrails Hiking | Meetup ICS | 2 | ✅ Ready |
| Exploring Montclair | Meetup ICS | 1 | ✅ Ready |
| Montclair GameNights | Meetup ICS | 1 | ✅ Ready |
| NJ Code & Coffee | Meetup ICS | 1 | ✅ Ready |
| Essex County Parks | JSON API scraper | 90 | ✅ Ready |
| PEAK Performances at MSU | WordPress ICS | 1 | ✅ Ready |

## Key Aggregators (benchmark competitors)
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

## Discovered - Needs Scraper
| Source | URL | Platform | Notes |
|--------|-----|----------|-------|
| Wellmont Theater | wellmonttheater.com/upcoming-shows/ | WordPress (ShowDog bot protection) | Major venue; also on Ticketmaster, Bandsintown, AXS |
| Montclair Film | montclairfilm.org/all-event/ | WordPress/Elementor/JetEngine | Runs Clairidge & Bellevue theaters |
| Montclair Art Museum | montclairartmuseum.org/events | Cloudflare protected | |
| Studio Montclair | studiomontclair.org/event-calendar/ | WordPress/Tribe Events | Mod_Security blocks ICS requests |
| ~~Montclair Brewery~~ | ~~montclairbrewery.com/events~~ | ~~Wix~~ | **Implemented** via Eventbrite organizer scraper (10 events) |
| ~~Montclair Book Center~~ | ~~montclairbookcenter.com/events.php~~ | ~~Custom PHP~~ | **Implemented** via Eventbrite organizer scraper (5 events) |
| Watchung Booksellers | watchungbooksellers.com/events | Bookmanager platform | Author events |

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

## Potential Additional Sources
- [ ] Montclair Brewery via Eventbrite API/scraper (13 events)
- [ ] Montclair Book Center via Eventbrite (5 events)
- [ ] Montclair Kimberley Academy (MaxPreps - private school athletics)
- [ ] Montclair YMCA (montclairymca.org - class schedules, special events)
- [ ] Fred Astaire Dance (fredastaire.com/upper-montclair/calendar/ - has discrete events)
- [ ] Montclair Farmers' Market (static recurring: Saturdays 8am-2pm, Walnut St)
- [ ] Congregation Shomrei Emunah, Bnai Keshet, Temple Ner Tamid (check for calendar pages)
- [ ] First Congregational Church (fccmontclair.org)
- [ ] Unitarian Universalist of Montclair (uumontclair.org)
- [ ] MSU College of the Arts (montclair.edu/arts/events-at-the-college/)
- [ ] MSU Campus Recreation special events
- [ ] Montclair Community Farms
