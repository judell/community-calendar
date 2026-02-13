# Petaluma Calendar Source Checklist

## Currently Implemented

| Source | Type | Events | Status |
|--------|------|--------|--------|
| Petaluma Downtown Association | Tockify ICS | 71 | ✅ Ready |
| Aqus Community | MembershipWorks ICS | 87 | ✅ Ready |
| Petaluma Regional Library | Scraper | 155 | ✅ Ready |
| Petaluma Chamber of Commerce | GrowthZone Scraper | 80 | ✅ Ready |
| Mystic Theatre | Scraper | 12 | ✅ Ready |
| Eventbrite Petaluma | Scraper | 14 | ✅ Ready |
| Petaluma High School Athletics | MaxPreps Scraper | 9 | ✅ Ready |
| Casa Grande High School Athletics | MaxPreps Scraper | 8 | ✅ Ready |
| Meetup: Mindful Petaluma | ICS | 10 | ✅ Ready |
| Meetup: Candlelight Yoga | ICS | 10 | ✅ Ready |
| Meetup: Rebel Craft Collective | ICS | 6 | ✅ Ready |
| Meetup: Sonoma-Marin Brat Pack | ICS | 2 | ✅ Ready |
| Meetup: Figure Drawing | ICS | 1 | ✅ Ready |
| Meetup: Petaluma Salon | ICS | 1 | ✅ Ready |
| Meetup: Book & Brew Club | ICS | 1 | ✅ Ready |
| Meetup: Active 20-30 | ICS | 2 | ✅ Ready |

**Total: ~430+ unique events**

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

### Major Discovery: Petaluma Chamber of Commerce (GrowthZone API)

- **URL:** `https://business.petalumachamber.us/api/events`
- **Format:** XML API (GrowthZone platform)
- **Events:** 262 events!
- **Content:** Business events, CPR classes, community events, Butter & Egg Days, Antique Faire
- **Status:** API available - needs XML-to-ICS scraper
- **Key events:**
  - Butter & Egg Days Parade & Festival 2026 (major local festival)
  - Petaluma Spring Antique Faire
  - Petaluma Business Connections (recurring)
  - Petaluma Chamber Women in Business (recurring)
  - Various CPR/First Aid classes

### Phoenix Theater (Wix - needs scraper)

- **URL:** thephoenixtheater.com
- **Platform:** Wix
- **Events:** ~8 events visible
- **Content:** Punk shows, wrestling, classical orchestra - diverse alternative venue
- **Status:** Would need custom Wix scraper (site-specific CSS classes)
- **Sample events:**
  - Squid Pisser, Right to Remain, Death Certificate, Dread (Feb 13)
  - Mugslug, Shooting Losers, A.B.P. and the Spites, POOCH (Feb 20)
  - Phoenix Pro Wrestling (Mar 20)
  - Young People's Chamber Orchestra (Mar 6)

### Sonoma-Marin Fairgrounds

- **URL:** sonoma-marinfair.org/calendar
- **Platform:** WordPress + The Events Calendar Pro
- **Status:** iCal endpoint returns HTML (disabled?)
- **Note:** May have events but feed not working

### Already Covered Elsewhere

| Venue | Status | Notes |
|-------|--------|-------|
| Mystic Theatre | ✅ Scraped | mystic_theatre.py scraper |
| Lagunitas Brewing | ✅ Via Eventbrite | Events appear in Eventbrite scrape |
| Hotel Petaluma | Skip | Just event space rentals, no calendar |

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

*All identified venues have been scraped or have ICS feeds.*

### ICS Feeds Discovered (2026-02-12)

| Venue | Feed URL | Events | Notes |
|-------|----------|--------|-------|
| **Aqus Community** | `https://api.membershipworks.com/v2/events?_op=ics&org=15499` | **87** | Live music, community dinners, salsa, comedy - all at aqus.com venues |

---

## Schools Discovery (2026-02-12)

### MaxPreps - High School Athletics
- **Petaluma High School (Trojans):** https://www.maxpreps.com/ca/petaluma/petaluma-trojans/events/
- **Casa Grande High School (Gauchos):** https://www.maxpreps.com/ca/petaluma/casa-grande-gauchos/events/
- **Data format:** JSON-LD SportsEvent schema embedded in page
- **Content:** Basketball, soccer, baseball, volleyball, etc.
- **Status:** Scrapeable - structured data available

### Petaluma City Schools (K-8)
- **URL:** petalumacityschools.org
- **Status:** Has school tour dates but no general event calendar found

### TODO
- [ ] Build MaxPreps scraper for both high schools
- [ ] Check SRJC Petaluma campus events
- [ ] Youth sports leagues (Little League, AYSO, etc.)

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
