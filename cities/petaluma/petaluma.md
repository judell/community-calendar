# Petaluma, CA - City Discovery Progress

**Started:** 2025-02-12  
**Last Updated:** 2026-02-14  
**Status:** ✅ DEPLOYED

## Current Status: ~435+ events from 27 sources

### Implemented Sources (all in CI)

| Source | Events | Type | Status |
|--------|--------|------|--------|
| Petaluma Regional Library | 155 | Scraper (`library_intercept.py`) | ✅ |
| Aqus Community | 87 | ICS Feed (MembershipWorks) | ✅ |
| Petaluma Chamber of Commerce | 80 | Scraper (`growthzone.py`) | ✅ |
| Petaluma Downtown Association | 46 | Tockify ICS | ✅ |
| SRJC Petaluma Campus | 17 | Scraper (`srjc_petaluma.py`) | ✅ |
| Eventbrite Petaluma | 14 | Scraper (`eventbrite_scraper.py`) | ✅ |
| Phoenix Theater | 13 | Scraper (`phoenix_theater.py`) | ✅ |
| Mystic Theatre | 12 | Scraper (`mystic_theatre.py`) | ✅ |
| Petaluma High Athletics | 9 | Scraper (`maxpreps.py`) | ✅ |
| Casa Grande High Athletics | 8 | Scraper (`maxpreps.py`) | ✅ |
| Mercury Theater | 12 | Scraper (`mercury_theater.py`) | ✅ |
| Adobe Road Winery | 8 | Scraper (`adobe_road.py`) | ✅ |
| HenHouse Brewing | 2-3 | Scraper (`henhouse.py`) | ✅ |
| Meetup: Mindful Petaluma | 10 | ICS Feed | ✅ |
| Meetup: Candlelight Yoga | 10 | ICS Feed | ✅ |
| Meetup: Sonoma County Outdoors | ~10 | ICS Feed | ✅ |
| Meetup: North Bay Contra Dance | ~10 | ICS Feed | ✅ |
| Meetup: Meditate with a Monk | ~10 | ICS Feed | ✅ |
| Meetup: Sonoma County Boomers | ~7 | ICS Feed | ✅ |
| Meetup: Rebel Craft Collective | 6 | ICS Feed | ✅ |
| Meetup: Go Wild Hikers | ~3 | ICS Feed | ✅ |
| Meetup: Sonoma-Marin Brat Pack | 2 | ICS Feed | ✅ |
| Meetup: Petaluma Active 20-30 | 2 | ICS Feed | ✅ |
| Meetup: Petaluma Figure Drawing | 1 | ICS Feed | ✅ |
| Meetup: Petaluma Salon | 1 | ICS Feed | ✅ |
| Meetup: Petaluma Book & Brew | 1 | ICS Feed | ✅ |

### Future Sources (No Scraper Yet)

| Source | Events | Platform | Notes |
|--------|--------|----------|-------|
| Lagunitas Taproom | Recurring | WordPress + Eventbrite | Trivia Wed, Music Bingo Thu; may overlap with Eventbrite scrape |
| Village Network | ~30+ | Unknown | Senior activities |

---

## Scrapers Created

### 1. Mystic Theatre (`scrapers/mystic_theatre.py`)
- **Platform:** WordPress + SeeTickets widget
- **Technique:** Parse HTML with BeautifulSoup, extract structured CSS classes
- **Data:** Title, date, show/doors times, venue, genre, ages, price, ticket URL
- **Screenshot:** `cities/petaluma/screenshots/phoenix-theater.png`

### 2. MaxPreps (`scrapers/maxpreps.py`) - GENERIC
- **Platform:** MaxPreps high school athletics
- **Technique:** Extract JSON-LD structured data (schema.org HighSchool)
- **Usage:** `--school petaluma-trojans` or `--url` for any school
- **Known schools:** Petaluma, Casa Grande, Santa Rosa, Davis, Bloomington
- **Screenshot:** `cities/petaluma/screenshots/maxpreps-petaluma-high.png`

### 3. GrowthZone (`scrapers/growthzone.py`) - GENERIC
- **Platform:** Chamber of Commerce sites (GrowthZone/ChamberMaster)
- **Technique:** Parse XML API at `/api/events`
- **Usage:** `--site petalumachamber` or `--url` for any GrowthZone site
- **Screenshot:** `cities/petaluma/screenshots/chamber-events-360.png`

---

## ICS Feeds Discovered

| Source | Feed URL | Events |
|--------|----------|--------|
| Petaluma Downtown | `https://tockify.com/api/feeds/ics/pdaevents` | 46 |
| Aqus Community | `https://api.membershipworks.com/v2/events?_op=ics&org=15499` | 87 |
| Meetup: Mindful Petaluma | `meetup.com/mindfulnesspetaluma/events/ical/` | 10 |
| Meetup: Rebel Craft | `meetup.com/the-rebel-craft-collective/events/ical/` | 6 |
| Meetup: Candlelight Yoga | `meetup.com/meetup-group-bwkyqavs/events/ical/` | 10 |
| Meetup: Figure Drawing | `meetup.com/petaluma-figure-drawing-meetup-group/events/ical/` | 1 |
| Meetup: Brat Pack | `meetup.com/sonoma-marin-brat-pack/events/ical/` | 2 |

---

## Key Discoveries & Techniques

### MembershipWorks ICS Feeds
Aqus Community uses MembershipWorks for their calendar. The ICS feed URL pattern:
```
https://api.membershipworks.com/v2/events?_op=ics&org={ORG_ID}
```
Look for "Subscribe" buttons on MembershipWorks calendars to find the org ID.

### GrowthZone/ChamberMaster API
Chamber of Commerce sites often use GrowthZone which has an XML API:
```
https://business.{chamber}.us/api/events
```
Returns structured XML with EventDisplay elements.

### MaxPreps JSON-LD
High school athletics pages embed JSON-LD with schema.org HighSchool type:
```javascript
<script type="application/ld+json">
{"@type": "HighSchool", "event": [...]}
</script>
```

### SeeTickets Widgets
Venues using SeeTickets (like Mystic Theatre) have well-structured HTML:
- `.title a` - event title
- `.date` - date string
- `.see-showtime`, `.see-doortime` - times
- `.genre`, `.ages`, `.price` - metadata

---

## Additional Sources Discovered (Feb 2026 Survey)

### Priority 1: Meetup ICS Feeds (Easy Wins)
| Source | URL | Events | Notes |
|--------|-----|--------|-------|
| Sonoma County Outdoors | `meetup.com/sonoma-county-outdoors/events/ical/` | ~10 | Hiking/walking, weekly in Petaluma |
| North Bay Contra Dance | `meetup.com/north-bay-contra-dance/events/ical/` | ~10 | Includes Petaluma dances |
| Sonoma County Boomers | `meetup.com/sonoma-county-boomers/events/ical/` | ~7 | Social events, some in Petaluma |
| Go Wild Hikers | `meetup.com/sonoma-county-go-wild-hikers/events/ical/` | ~3 | Hiking |
| Meditate with a Monk | `meetup.com/meditate-with-a-monk-in-sonoma-county/events/ical/` | ~10 | Penngrove/Petaluma area |
| Petaluma Book Club | `meetup.com/petaluma-book-and-brew-club/events/ical/` | ~1 | Monthly |

### Priority 2: Venues with Structured Calendars
| Source | URL | Events | Status | Notes |
|--------|-----|--------|--------|-------|
| HenHouse Brewing | henhousebrewing.com/events/ | 2-3 | ✅ `henhouse.py` | Trivia Thursdays, paint nights |
| Phoenix Theater | thephoenixtheater.com/ | 13 | ✅ `phoenix_theater.py` | Via Eventbrite search |
| Lagunitas Taproom | lagunitas.com/taproom/petaluma/ | Recurring | 🔧 | Trivia Wed, Music Bingo Thu |
| Mercury Theater | mercurytheater.org/ | ~5 | 🔧 | New theater at old Cinnabar venue |
| Adobe Road Winery | adoberoadwines.com/calendar/ | ~5-10 | 🔧 | Wine events, live music |
| Cinnabar Theater | cinnabartheater.org/season-53/ | ~5 | 🔧 | Now at SSU |

### Priority 3: Community Organizations (Need Scrapers)
| Source | URL | Events | Notes |
|--------|-----|--------|-------|
| Village Network | villagenetworkofpetaluma.org/events/ | ~30+ | Senior activities, many weekly |
| Cool Petaluma | coolpetaluma.org/events | ~5-10 | Environmental/community |
| Petaluma Arts Center | petalumaartscenter.org/events/ | ~5 | Exhibitions, workshops |
| Petaluma Garden Club | petalumagardenclub.org/calendar/ | Monthly | 2nd Monday meetings |
| Calvary Chapel | calvarypetaluma.org/events | ~5-10 | Church events |
| UU Petaluma | uupetaluma.org | Weekly | Sunday services |

### Priority 4: Dance & Fitness
| Source | URL | Events | Notes |
|--------|-----|--------|-------|
| Jasmine Worrell Swing | jasmineworrelldance.com/petaluma-swing-dance/ | Weekly | Thursdays at Hermann Sons |
| Fred Astaire Petaluma | fredastaire.com/petaluma/calendar/ | Ongoing | Dance classes |
| Bike Petaluma | bikepetaluma.org/about/events/ | 2/month | First Friday, Second Saturday rides |

### Lower Priority / Aggregators
| Source | URL | Notes |
|--------|-----|-------|
| Visit Petaluma | visitpetaluma.com/find-events/ | Aggregator, may have unique events |
| Petaluma Argus-Courier | petalumanews.com/events/ | Community calendar, aggregated |
| ACE Farmers Markets | ilovefarmersmarkets.org | 3 Petaluma markets (recurring) |

### Non-Starters
| Source | Reason |
|--------|--------|
| City of Petaluma | Cloudflare protection |
| Petaluma Running Club | Facebook group only |
| Petaluma Wildlife Museum | School tours/private events |
| Mindful-Monday Meetup | Virtual conference calls |

---

## Screenshots

See `cities/petaluma/screenshots/`:
- `chamber-events-360.png` - Chamber of Commerce (262 events)
- `chamber-calendar-view.png` - Chamber calendar view
- `phoenix-theater.png` - Phoenix Theater (Wix)
- `maxpreps-petaluma-high.png` - Petaluma High athletics
- `maxpreps-casa-grande.png` - Casa Grande High athletics
