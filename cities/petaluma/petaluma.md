# Petaluma, CA - City Discovery Progress

**Started:** 2025-02-12  
**Last Updated:** 2026-02-12  
**Status:** ✅ READY TO DEPLOY

## Current Status: ~360+ events from 12 sources

### Implemented Sources

| Source | Events | Type | Status |
|--------|--------|------|--------|
| Petaluma Regional Library | 155 | Scraper (`library_intercept.py`) | ✅ |
| Aqus Community | 87 | ICS Feed (MembershipWorks) | ✅ |
| Petaluma Downtown Association | 46 | Tockify ICS | ✅ |
| Eventbrite Petaluma | 14 | Scraper | ✅ |
| Mystic Theatre | 12 | Scraper (`mystic_theatre.py`) | ✅ |
| Petaluma High Athletics | 9 | Scraper (`maxpreps.py`) | ✅ |
| Casa Grande High Athletics | 8 | Scraper (`maxpreps.py`) | ✅ |
| 5 Meetup groups | 29 | ICS Feeds | ✅ |

### Pending Sources (Scrapers Written)

| Source | Events | Type | Status |
|--------|--------|------|--------|
| Chamber of Commerce | 262 | GrowthZone API (`growthzone.py`) | 🔧 Needs testing |

### Future Sources (No Scraper Yet)

| Source | Events | Platform | Notes |
|--------|--------|----------|-------|
| Phoenix Theater | ~8 | Wix iframe | Complex - cross-origin |
| SRJC Petaluma | ? | Unknown | Not yet investigated |
| Youth Sports | ? | Various | Little League, AYSO, etc. |

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

## Non-Starters

| Source | Reason |
|--------|--------|
| City of Petaluma | Cloudflare protection |
| Petaluma Arts Center | Squarespace, no easy feed |
| Phoenix Theater | Wix with cross-origin iframe |
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
