# Petaluma Calendar Source Checklist

## Currently Implemented (all in CI)

| Source | Type | Events | Status |
|--------|------|--------|--------|
| Petaluma Downtown Association | Tockify ICS | 71 | ✅ In CI |
| Aqus Community | MembershipWorks ICS | 87 | ✅ In CI |
| Petaluma Regional Library | Scraper | 155 | ✅ In CI |
| Petaluma Chamber of Commerce | GrowthZone Scraper | 80 | ✅ In CI |
| Mystic Theatre | Scraper | 12 | ✅ In CI |
| Eventbrite Petaluma | Scraper | 14 | ✅ In CI |
| Petaluma High School Athletics | MaxPreps Scraper | 9 | ✅ In CI |
| Casa Grande High School Athletics | MaxPreps Scraper | 8 | ✅ In CI |
| SRJC Petaluma Campus | LiveWhale Scraper | 17 | ✅ In CI |
| HenHouse Brewing Petaluma | Scraper | 2-3 | ✅ In CI |
| Phoenix Theater | Eventbrite Scraper | 13 | ✅ In CI |
| Meetup: Mindful Petaluma | ICS | 10 | ✅ In CI |
| Meetup: Candlelight Yoga | ICS | 10 | ✅ In CI |
| Meetup: Rebel Craft Collective | ICS | 6 | ✅ In CI |
| Meetup: Sonoma-Marin Brat Pack | ICS | 2 | ✅ In CI |
| Meetup: Figure Drawing | ICS | 1 | ✅ In CI |
| Meetup: Petaluma Salon | ICS | 1 | ✅ In CI |
| Meetup: Book & Brew Club | ICS | 1 | ✅ In CI |
| Meetup: Active 20-30 | ICS | 2 | ✅ In CI |
| Meetup: Sonoma County Outdoors | ICS | ~10 | ✅ In CI |
| Meetup: North Bay Contra Dance | ICS | ~10 | ✅ In CI |
| Meetup: Sonoma County Boomers | ICS | ~7 | ✅ In CI |
| Meetup: Go Wild Hikers | ICS | ~3 | ✅ In CI |
| Meetup: Meditate with a Monk | ICS | ~10 | ✅ In CI |
| Mercury Theater | Squarespace JSON Scraper | 12 | ✅ In CI |
| Adobe Road Winery | JSON-LD Scraper | 8 | ✅ In CI |
| The Big Easy | WordPress iCal | ~30 | ✅ In CI |
| Meetup: North Bay Adventure Club | ICS | ~10 | ✅ In CI |
| Meetup: North Bay Tails and Trails | ICS | ~5 | ✅ In CI |
| Meetup: North Bay 50+ Nature and Outdoors | ICS | ~10 | ✅ In CI |
| Meetup: Senior Walkabouters (SWAG) | ICS | ~5 | ✅ In CI |
| Meetup: Sonoma County Wanderers | ICS | ~10 | ✅ In CI |
| Meetup: Mindfull Hikes | ICS | ~5 | ✅ In CI |
| Meetup: Four Corners Hiking & Beer | ICS | ~5 | ✅ In CI |

**Total: ~515+ events (before deduplication)**

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

**Nearby groups (not Petaluma-based but relevant):**
- Meditate-with-a-Monk-in-Sonoma-County (Penngrove) - 10 events
- Alternative-Healing-Exploration (Cotati) - 10 events
- Hidden-Backroads-Adventures (Santa Rosa) - 10 events
- Several Marin/Novato groups

### Additional Meetup Groups Discovered (2026-02-14)

Topical search found more regional groups with Petaluma events:

| Group | ICS URL | Events | Notes |
|-------|---------|--------|-------|
| sonoma-county-outdoors | `meetup.com/sonoma-county-outdoors/events/ical/` | ~10 | Hiking/walking, weekly in Petaluma |
| north-bay-contra-dance | `meetup.com/north-bay-contra-dance/events/ical/` | ~10 | Includes Petaluma dances |
| sonoma-county-boomers | `meetup.com/sonoma-county-boomers/events/ical/` | ~7 | Social events, some in Petaluma |
| sonoma-county-go-wild-hikers | `meetup.com/sonoma-county-go-wild-hikers/events/ical/` | ~3 | Hiking |
| meditate-with-a-monk-in-sonoma-county | `meetup.com/meditate-with-a-monk-in-sonoma-county/events/ical/` | ~10 | Penngrove area |

**Status:** ✅ All added to CI (2026-02-14)

### Hiking & Outdoors Meetup Groups Discovered (2026-02-14)

Topical search for hiking, outdoors, dogs, seniors + Petaluma found more groups:

| Group | ICS URL | Events | Notes |
|-------|---------|--------|-------|
| northbayhiking | `meetup.com/northbayhiking/events/ical/` | ~10 | Hiking, backpacking, kayaking |
| north-bay-tails-and-trails | `meetup.com/north-bay-tails-and-trails/events/ical/` | ~5 | Dog-friendly hikes, Sonoma County |
| meetup-group-qXYJpXNx | `meetup.com/meetup-group-qXYJpXNx/events/ical/` | ~10 | 50+ nature walks, 1,081 members |
| senior-walkabouters | `meetup.com/senior-walkabouters/events/ical/` | ~5 | Walking/hiking, Sonoma County parks |
| sonoma-county-wanderers | `meetup.com/sonoma-county-wanderers/events/ical/` | ~10 | Ages 45-70, 5-14 mile hikes |
| meetup-group-ohazunav | `meetup.com/meetup-group-ohazunav/events/ical/` | ~5 | Mindful/silent hiking, 690 members |
| Four-Corners-Hiking-Beer | `meetup.com/Four-Corners-Hiking-Beer/events/ical/` | ~5 | Hike then beer, rotates North Bay |

**Status:** ✅ All added to CI (2026-02-14)

### Topical Discovery: Venues & Orgs to Investigate (2026-02-14)

Comprehensive topical searches (music, hiking, cycling, birding, gardening, art/theater, food/wine, community/church/seniors) found many additional sources. Organized by scraping approach:

**Squarespace sites (can reuse Mercury Theater `?format=json` pattern):**
- Cinnabar Theater (cinnabartheater.org/shows/) - Full theater season
- WonderStump! (wonderstump.art/events) - Immersive art venue
- Polly Klaas Community Theater (pollyklaastheater.org/events/) - StorySlam, jazz
- Petaluma Arts Center (petalumaartscenter.org/events) - Monthly art exchange
- Brewsters Beer Garden (brewstersbeergarden.com/calendar1) - Live music, trivia
- Cool Petaluma (coolpetaluma.org/events) - Climate/sustainability events
- 350 Petaluma (350petaluma.org/events) - Monthly bike rides
- Brooks Note Winery (brooksnotewinery.com/event-calendar/) - Friday music
- Petaluma People Services (petalumapeople.org/events) - Senior programs
- Healthy Petaluma (healthypetaluma.org/calendar-of-events) - Health events

**Live music venues (need investigation):**
- ~~The Big Easy (bigeasypetaluma.com)~~ - **DONE** - WordPress iCal feed, ~30 events
- McNear's Saloon (mcnears.com/our-events/) - Comedy + live events
- Montagne Russe Winery (russewines.com/Events) - Weekly Saturday music
- Griffo Distillery (griffodistillery.com/pages/calendar) - Weekly Thursday jam

**WordPress/iCal sites (try `?ical=1` endpoint):**
- Petaluma Elks Lodge (elks901.org/calendar-of-events/) - Craft faires, dinners
- Petaluma Wetlands Alliance (petalumawetlands.org/calendar/) - Bird walks
- Petaluma Garden Club (petalumagardenclub.org/calendar/) - Monthly meetings
- Petaluma Bounty (petalumabounty.org/events-calendar/) - Farm volunteer hours

**Other platforms:**
- Rotary Club of Petaluma (ClubRunner - try portal.clubrunner.ca/10088/events/ical)
- Village Network of Petaluma (ClubExpress - check for iCal)
- Blue Zones Project Petaluma (Eventbrite - may already be captured)
- Sonoma County Regional Parks (parks.sonomacounty.ca.gov/play/calendar/hiking)
- Petaluma Cycling Club (Wild Apricot - no native ICS)
- Empire Runners Club (Wild Apricot - no native ICS)
- Petaluma River Park (petalumariverpark.org/calendar - weekly Tuesday walks)

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
- [x] Build MaxPreps scraper for both high schools ✅ Done
- [x] Check SRJC Petaluma campus events ✅ Done (17 events)
- [x] Youth sports leagues - **Not viable** (see below)

### Youth Sports Research (2026-02-14)

**Extensively Investigated:**

| Organization | URL | Platform | Status |
|-------------|-----|----------|--------|
| Petaluma National Little League | petalumanational.org | BlueSombrero/sSchedule | No public ICS |
| Petaluma American Little League | petalumaamerican.com | BlueSombrero/sSchedule | No public ICS |
| Petaluma Leghorns (Baseball) | petalumaleghorns.com | Custom site | Schedule page exists, no ICS |
| AYSO Region 26 | ayso26.org | Google Sites | Palo Alto, not Petaluma |
| Petaluma Youth Soccer | petalumasoccerclub.com | Not found | Domain doesn't resolve |
| Petaluma Girls Softball | petalumagirlssoftball.com | Error page | Site down |
| Petaluma Swim Team | petalumaswim.org | SeedProd (coming soon) | Not active |
| City of Petaluma Parks & Rec | cityofpetaluma.org | Cloudflare | Blocked |
| Petaluma RecDesk | petaluma.recdesk.com | RecDesk | Organization not found |

**Platforms checked:** GameChanger, TeamSnap, SportsEngine, LeagueApps, GotSport, TourneyMachine, ActiveNet, RecDesk

**Finding:** Youth sports organizations in Petaluma either:
1. Use member-only platforms without public calendar exports (Little League)
2. Have no functioning websites (soccer, softball, swim)
3. Are blocked by Cloudflare (city recreation)
4. Don't serve Petaluma specifically (AYSO)

**Conclusion:** Youth sports leagues are **not viable** for public calendar aggregation. The high school athletics via MaxPreps (Petaluma High + Casa Grande) already capture the public-facing school sports events that would be of general community interest.

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

---

## SRJC Petaluma Campus Discovery (2026-02-12)

**Source:** Santa Rosa Junior College LiveWhale Calendar
**URL:** `https://calendar.santarosa.edu/live/ical/events`
**Scraper:** `scrapers/srjc_petaluma.py`

**Method:** The SRJC calendar uses LiveWhale platform with a JSON API. The scraper fetches all events and filters for those containing "Petaluma" in the title or URL.

**Events Found:** 17 Petaluma-specific events including:
- Petaluma Cinema Series (weekly film screenings)
- Free Farmer's Market - Petaluma Campus
- Financial Aid Fun Fair - Petaluma Campus
- Sonoma State Rep appointments at Petaluma

**Notes:** 
- Full SRJC feed has 130+ events across all campuses
- Santa Rosa campus events are already covered in the Santa Rosa calendar

---

## Phoenix Theater Discovery (2026-02-12, updated 2026-02-14)

**Source:** Phoenix Theater (thephoenixtheater.com)
**Platform:** Wix (hard to scrape directly)
**Ticketing:** Eventbrite
**Events:** 13 events found

**Key Insight:** The Wix site was a nightmare (heavy JS, no static content). But searching Eventbrite for "phoenix theater petaluma" returns all events with clean JSON-LD structured data.

**Scraper:** `scrapers/phoenix_theater.py`
- Searches Eventbrite for Phoenix Theater Petaluma
- Filters results by venue address (201 Washington St)
- Extracts JSON-LD event data
- Outputs ICS format

**Sample events:**
- Phoenix Pro Wrestling (Mar 20)
- Agent Orange (May 9)
- Young People's Chamber Orchestra (Mar 28)
- Suicide Queen, Our Graves, Lust 4 Blood (Mar 6)

**Lesson learned:** When a venue's website is hard to scrape, check their ticketing platform (Eventbrite, SeeTickets, Dice, etc.) - the ticketing site often has much cleaner data.

---

## HenHouse Brewing Discovery (2026-02-14)

**Source:** HenHouse Brewing Petaluma (henhousebrewing.com/events/)
**Platform:** WordPress
**Events:** 2-3 Petaluma events (plus recurring trivia)

**Scraper:** `scrapers/henhouse.py`
- Parses WordPress events page
- Filters for Petaluma location only (they have 3 locations)
- Handles recurring events (Trivia Thursdays noted but not expanded)

**Events found:**
- Trivia Night - Petaluma (Every Thursday 6-8pm) - recurring
- artXcursion: Brushes + Brew (paint nights)
- Big Fried Chicken Cook-Off (Mar 1)

---

## Sonoma-Marin Fairgrounds (2026-02-12)

**Source:** sonoma-marinfair.org/calendar
**Platform:** WordPress + The Events Calendar (FullCalendar display)
**Status:** Calendar appears empty for Feb 2026

**Feed Attempt:** ICS endpoint at `?ical=1` returns HTML (disabled?)

**Recommendation:** Skip for now - check again closer to summer fair season (June-July).
