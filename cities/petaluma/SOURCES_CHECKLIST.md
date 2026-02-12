# Petaluma Calendar Source Checklist

## Currently Implemented

*None yet - city in discovery phase*

---

## Recommended Sources

### Live ICS Feeds (Ready to Add)

| Source | URL | Events | Notes |
|--------|-----|--------|-------|
| Petaluma Downtown Association | `https://tockify.com/api/feeds/ics/pdaevents` | 71 | Downtown events, festivals, live music |

### Meetup Groups (Ready to Add)

| Group | ICS URL | Events | Notes |
|-------|---------|--------|-------|
| mindfulnesspetaluma | `meetup.com/mindfulnesspetaluma/events/ical/` | 10 | Meditation/mindfulness events |
| the-rebel-craft-collective | `meetup.com/the-rebel-craft-collective/events/ical/` | 6 | Happy Hour Crafts |
| meetup-group-bwkyqavs | `meetup.com/meetup-group-bwkyqavs/events/ical/` | 10 | Candlelight Yoga @ Hotel Petaluma |
| petaluma-figure-drawing-meetup-group | `meetup.com/petaluma-figure-drawing-meetup-group/events/ical/` | 1 | Figure Drawing at Suite G Studio |
| sonoma-marin-brat-pack | `meetup.com/sonoma-marin-brat-pack/events/ical/` | 2 | Social events |

### Scraped Sources (Ready to Add)

| Source | Method | Notes |
|--------|--------|-------|
| Eventbrite Petaluma | `eventbrite_scraper.py --location ca--petaluma` | 14 events found |

---

## Eventbrite Discovery (2025-02-12)

**Command:** `python scrapers/eventbrite_scraper.py --location ca--petaluma --months 2`

**Results:** 14 local events from 20 scraped

**Key Venues Found:**
- Lagunitas Brewing Company (Mardi Gras Party, Album Release)
- Della Fattoria Downtown Café (Valentine's Day Album Release)
- Petaluma Veterans Building (Rotary Crab Feed)
- Brooks Note Winery (multiple events, also on Downtown calendar)

---

## Meetup Groups Discovery (2025-02-12)

Searched: `meetup.com/find/?location=us--ca--Petaluma&source=GROUPS`

**Found:** 73 groups within 18 miles

**Petaluma-based groups with events (10 total):**

| Group | Events | Category | Location Verified |
|-------|--------|----------|-------------------|
| mindfulnesspetaluma | 10 | Wellness | ✅ Petaluma |
| meetup-group-bwkyqavs | 10 | Wellness | ✅ Petaluma |
| the-rebel-craft-collective | 6 | Arts/Crafts | ✅ Petaluma |
| sonoma-marin-brat-pack | 2 | Social | ✅ Petaluma |
| petaluma-figure-drawing-meetup-group | 1 | Arts | ✅ Petaluma |
| Mindful-Monday | 10 | Wellness | ✅ Petaluma (virtual?) |
| petaluma-salon | 1 | Books | ✅ Petaluma |
| petaluma-book-and-brew-club | 1 | Books | ✅ Petaluma |
| petaluma-active-20-30 | 2 | Professional | ✅ Petaluma |
| aligned-profitable-business-growth-for-women | 1 | Professional | ✅ Petaluma |

**Nearby groups (not Petaluma-based):**
- Meditate-with-a-Monk-in-Sonoma-County (Penngrove) - 10 events
- Alternative-Healing-Exploration (Cotati) - 10 events
- Hidden-Backroads-Adventures (Santa Rosa) - 10 events
- Several Marin/Novato groups

---

## Potential Additional Sources

### Venues to Investigate

| Venue | URL | Status | Notes |
|-------|-----|--------|-------|
| Mystic Theatre | mystictheatre.com | No feed | WordPress/SeeTickets, concerts & comedy |
| Petaluma Arts Center | petalumaartscenter.org | No feed | Squarespace, exhibitions & events |
| Lagunitas Brewing | lagunitas.com | Age gate | Events on Eventbrite |
| Hotel Petaluma | | | Hosts yoga meetup, may have own calendar |

### City/Government

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| City of Petaluma | cityofpetaluma.org | Cloudflare | Cannot scrape directly |
| Petaluma Parks & Rec | | | May have separate calendar |

---

## Additional Discoveries (2025-02-12)

### Petaluma Wildlife Museum (Tockify)
- **URL:** `https://tockify.com/api/feeds/ics/petaluma.wildlife.musuem`
- **Events:** 81 events
- **Content:** Mostly school tours, birthday parties, Open Houses
- **Recommendation:** Skip - not public community events

### Petaluma Historical Library & Museum
- **URL:** petalumamuseum.com/events/calendar-of-events
- **Status:** No discoverable feed
- **Content:** Concerts, guest speakers (ticketed events)
- **Recommendation:** Would need scraper

### Petaluma Wetlands Alliance
- **URL:** petalumawetlands.org
- **Content:** Regular nature walks (4th Saturday, 2nd Saturday)
- **Status:** Divi WordPress, no calendar feed
- **Recommendation:** Manual tracking or custom scraper

---

## Non-Starters

| Source | Reason |
|--------|--------|
| City of Petaluma website | Cloudflare protection |
| Petaluma Arts Center | Squarespace, no easy feed |
| Various Marin-based Meetup groups | Too far from Petaluma |
| Mindful-Monday Meetup | Virtual conference calls, not local |
| Petaluma Wildlife Museum | School tours/private events, not public |
| Mystic Theatre | Scrapeable (SeeTickets widget) - 40+ events, worth building scraper |

### Venues Worth Scraping

| Venue | Platform | Events | Notes |
|-------|----------|--------|-------|
| Mystic Theatre | SeeTickets/WordPress | 40+ | Concerts, comedy, tribute acts. Structured HTML data. |
| Aqus Cafe | WordPress/Salient | ~10+ | Community dinners, live music. Has Subscribe button. |

---

## Overlap with Santa Rosa

Petaluma is part of Sonoma County, which has significant overlap with Santa Rosa sources:

1. **Sonoma County Library** - Already scraped, includes Petaluma branch (245+ Petaluma mentions!)
2. **Regional Meetup groups** - Some serve both cities (e.g., shutupandwritewinecountry)
3. **Eventbrite Sonoma County** - May include Petaluma events

**Decision:** Create dedicated Petaluma city with focused local sources.

**Note:** The library_intercept.py scraper for Santa Rosa already captures Petaluma Regional Library events. For Petaluma city, we could either:
- Re-run the same scraper (events are already mixed)
- Filter the Santa Rosa output for Petaluma locations
- Create a separate Petaluma library configuration (probably overkill)
