# Bloomington Calendar Source Checklist

Prioritized list of potential event sources for the Bloomington, IN community calendar.

## Currently Implemented (76 sources)

### University — IU LiveWhale (17 feeds)

| Source | Group ID | Events | Notes |
|--------|----------|--------|-------|
| IU Jacobs School of Music | 56 | ~514 | |
| IU Auditorium | 378 | ~23 | |
| Eskenazi Museum of Art | 234 | ~74 | |
| IU Cinema | 81 | ~19 | |
| IU La Casa Latino Cultural Center | 59 | ~109 | |
| IU Maurer School of Law | 64 | ~80 | |
| IU Kelley School of Business | 343 | ~48 | |
| IU Arts & Humanities Institute | 130 | ~183 | |
| IU Bloomington Libraries | 261 | ~436 | |
| IU Theatre & Dance | 218 | ~20 | |
| IU Asian Culture Center | 314 | ~26 | |
| IU First Nations Center | 275 | ~14 | |
| IU LGBTQ+ Culture Center | 237 | ~4 | |
| IU Black Film Center & Archive | 221 | ~9 | |
| IU Neal-Marshall Black Culture Center | 235 | — | Seasonal |
| IU Hamilton Lugar School | 135 | — | Global & International Studies |
| IU Eskenazi School of Art | 11 | ~94 | Exhibitions, lectures, MFA shows |

Feed URL pattern: `https://events.iu.edu/live/ical/events/group_id/{id}`
Docs: https://documentation.events.iu.edu/feed-and-linked-calendars/ical-feed.html

### University — Other IU Platforms (2 feeds)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| IU Moving Image Archive | LibCal `cid=5914` | ~151 | |
| IU Scholars' Commons | LibCal `cid=1228` | ~26 | |

### City & Civic (4 feeds)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| City of Bloomington | Google Calendar | ~374 | |
| City Boards & Commissions | Google Calendar | — | |
| City Department Events | Google Calendar | — | |
| Parks and Recreation | Google Calendar | ~1615 | Concerts, fitness, nature, family events |
| Bloomington Farmers Market | Google Calendar | ~307 | |

### Music & Performing Arts (7 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| The Bluebird | Songkick | ~9 | `songkick.py` venue 78904 |
| Blockhouse Bar | Songkick | ~2 | `songkick.py` venue 3607354 |
| Buskirk-Chumley Theater | Scraper | ~32 | `buskirk_chumley.py` |
| The Bishop | Scraper | ~4 | `the_bishop.py` (SSL verify=False, cert expired 2026-03) |
| The Comedy Attic | Scraper | ~32 | `comedy_attic.py` |
| Constellation Stage & Screen | Scraper | ~45 | Spektrix API — `constellation.py` |
| Brown County Playhouse | ICS | ~12 | WordPress Events Calendar |

### Arts & Culture (6 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Bloomington Arts | ICS | — | Tockify API feed |
| FAR Center for Contemporary Arts | Scraper | ~4 | `far_center.py` — Craft CMS |
| Cicada Cinema | Scraper | ~6 | Shopify products API — `cicada_cinema.py` |
| Pottery House Studio | Scraper | ~40 | Squarespace — `squarespace.py` workshops |
| Bloomington Old-Time Music & Dance | Google Calendar | — | |

### Literary (4 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Writers Guild at Bloomington | Scraper | ~7 | `writers_guild.py` — Sugar Calendar |
| Morgenstern Books | Eventbrite scraper | ~9 | Author events, book clubs |
| Redbud Books | Google Calendar | ~348 | Book clubs, author talks, film, community events |
| Nerd Nite Bloomington | Eventbrite scraper | ~1 | Quarterly science talks at The Bishop |

### Community & Family (8 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Monroe County Public Library | Scraper | ~483 | `library_intercept.py --location bloomington` |
| Boys & Girls Club | ICS | — | WordPress Events Calendar |
| WonderLab Museum | ICS | ~30+ | WordPress ICS — Cloudflare blocks HTML but not ICS |
| First United Church | ICS | ~50+ | WordPress ICS — community hub (DSA, Al-Anon, scouts) |
| Bloomington Community Band | ICS | ~20 | WordPress Events Calendar |
| Bloominglabs Makerspace | Google Calendar | ~10+ | |
| Habitat for Humanity Monroe County | Scraper | ~4 | `habitat.py` — fundraisers, 5K, volunteer events |
| NAMI Greater Bloomington | Scraper | ~31 | `nami_bloomington.py` — Tribe Events API; support groups at library |
| Bloomington Spinners & Weavers Guild | ICS | — | |

### Nature & Outdoors (6 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Sassafras Audubon Society | Scraper | ~31 | Squarespace — `sassafras_audubon.py` |
| Monroe County Master Gardeners | Scraper | ~62 | Squarespace — `master_gardeners.py` |
| Sycamore Land Trust | Scraper | ~131 | WordPress — `sycamore_land_trust.py` |
| McCormick's Creek State Park | Localist scraper | ~44 | `localist.py` — events.in.gov venue 35217665860404 (13 mi) |
| Brown County State Park | Localist scraper | ~13 | `localist.py` — events.in.gov venue 35217662417669 (17 mi) |
| Knobstone Hiking Trail Meetup | ICS | ~10 | Meetup group — regional hiking |

### Interest Groups & Civic (5 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Bloomington Atheists Meetup | ICS | ~10 | Meetup group |
| Bloomington Bicycle Club | Google Calendar | ~5023 | Cycling rides, weekly events |
| Bloomington Velo Club | Google Calendar | — | |
| Hoosier Fly Fishers | ICS | — | |
| Indivisible Central Indiana | Scraper | ~21 | `mobilize.py` — civic/political organizing |

### Food & Beverage (5 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Cardinal Spirits | Scraper | ~5 | Squarespace — `cardinal_spirits.py` |
| The Tap | Eventbrite scraper | — | Live music, craft beer events |
| Martinsville Arts Council | Eventbrite scraper | ~6 | Community theater in Martinsville (20 mi) |
| Story Inn | Eventbrite scraper | — | Seasonal: wine fairs, comedy, music in Story (17 mi) |
| Hard Truth Distilling Co. | ICS | ~15 | TEC feed; Nashville, IN (16 mi) |
| Upland Brewing | ICS | — | WordPress Events Calendar — dormant, populates seasonally |
| People's Market | Scraper | ~10 | Squarespace — `peoples_market.py` |

### Aggregators (10 sources)

These curate or aggregate events from multiple venues:

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| WFHB Community Calendar | Scraper | ~349 | `wfhb_calendar.py` — ai1ec; covers Orbit Room, library events, and many venues not otherwise scrapable |
| BloomingtonOnline: Events | Google Calendar | ~224 | Community events |
| BloomingtonOnline: Food & Drink | Google Calendar | ~133 | Restaurant/brewery specials |
| BloomingtonOnline: Shopping | Google Calendar | ~18 | Markets, deals |
| Let's Go! Bloomington | Google Calendar | — | Indie venues, shows, art openings |
| BloomingtonArts.Today | Scraper | ~115 | Hand-curated arts calendar; 88% overlap with authoritative feeds |
| Brown County Events | ICS | ~94 | browncounty.com CVB — aggregates Nashville/Brown County venues |
| B-Square Bulletin (4 feeds) | Google Calendar | ~9162 | Government, misc civic, Critical Mass, BPTC meetings (mostly historical, future-filtered) |
| IU beINvolved Student Orgs | ICS | ~16900 | CampusLabs — all student org events campus-wide |

### Ticketmaster Venues (8 sources)

| Source | Venue ID | Events | Notes |
|--------|----------|--------|-------|
| IU Musical Arts Center | KovZpaoDke | ~15 | Opera, ballet, orchestral |
| IU Cinema | KovZpZAI11nA | ~31 | Film screenings |
| Brown County Music Center | KovZ917AOr1 | ~27 | Nashville, IN (17 mi) |
| IU Memorial Stadium | KovZpZAFdInA | ~4 | Football, concerts |
| Ruth N Halls Theatre | KovZpZAdE6aA | ~8 | Theatre, dance |
| Bill Armstrong Stadium | KovZpaoDQe | ~5 | Soccer, events |
| Wells Metz Theatre | KovZpZAF7JFA | ~4 | Theatre |
| Simon Skjodt Assembly Hall | KovZpZAFdItA | ~2 | Basketball, concerts |

### Other (3 sources)

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Lotus Festival | ICS | ~7 | WordPress Events Calendar |
| Indiana State Events | ICS | — | `events.in.gov` |
| Utilities Service Board | Google Calendar | — | Board meetings |

---

## Dead Ends & Non-Starters

### Blocked / No Feed

| Source | Platform | Reason |
|--------|----------|--------|
| Visit Bloomington | Simpleview CMS | No public API |
| Winter Farmers' Market | Wix | No ICS export |
| Gallery Walk Bloomington | Wix | No feed; recurring first Friday 5-8pm |
| BARA (runners) | Wix | No ICS export |
| Bloomington PRIDE | Squarespace | No ICS export |
| Bloomington Brewing Co | Squarespace | No ICS export |
| Bloomington Yoga Collective | Squarespace + MindBody | Class schedules only |
| Vibe Yoga Studio | Squarespace | Class schedules only |
| Bloomington Volunteer Network | Galaxy Digital | No feed export |
| ~~NAMI Greater Bloomington~~ | ~~The Events Calendar~~ | RESOLVED: Tribe Events REST API works (2026-03) |
| SIREN Solar | Tribe Events Calendar | ICS broken, API returns 0 events — dead calendar |
| Pillar Arts | WordPress + TEC | ICS export broken; calendar appears inactive |
| Monroe County Gov | Indiana state platform | No ICS export |
| MCCSC School Calendar | ParentSquare | Old URL 404 |

### No Calendar / Social Media Only

| Source | Reason |
|--------|--------|
| Juniper Art Gallery | Shopify, no calendar feed; some events covered by WFHB |
| Backspace Gallery | Square site, no events page; some events covered by WFHB |
| Windfall Dancers | WordPress, class schedules as plain text |
| Time & Tide Tattoo | Flash events on Instagram/Facebook only |
| Indiana Dance Company | Class schedules only |
| MotionArts Dance Academy | Class schedules only |
| Yoga Mala | Google Calendar page is 404 |

### Derivative / Duplicate

| Source | Reason |
|--------|--------|
| Bandsintown Bloomington | Derivative, duplicate-heavy |
| Limestone Post Magazine | CitySpark-powered aggregator |
| Herald-Times Events | Derivative aggregator |
| Indiana Daily Student Events | No ICS feed; derivative |

### Inactive / Suspended

| Source | Reason |
|--------|--------|
| WCLS 97.7 | Site suspended |
| Indiana Public Media | Brightspot CMS, no ICS/RSS for events |
| The Back Door (Tockify) | ICS export disabled on their plan |
| Chamber of Commerce Atlas | No ICS feed |
| Bloomington Board Games Meetup | 403 private |
| Bloomington Remote Workers Meetup | Dormant |

### Low Priority

| Source | Reason |
|--------|--------|
| UU Church of Bloomington | Planning Center (no public API); events mostly internal |
| Friends Meeting | Squarespace; calendar behind member-only page |
| Neighborhood Associations | Sites appear inactive/minimal events |
| Bloomingtonian | Community blog, low volume |
| NUVO | Regional, derivative |
| Do317 | Indy-centric |

---

## Platform Scrapers (Reusable)

| Platform | File | Used By (Bloomington) | Notes |
|----------|------|-----------------------|-------|
| Squarespace | `lib/squarespace.py` | Cardinal Spirits, Sassafras Audubon, Master Gardeners, People's Market | JSON API at `?format=json` |
| All-in-One Event Calendar (ai1ec) | `lib/ai1ec.py` | WFHB | WordPress plugin; HTML agenda view |
| Sugar Calendar Lite | `lib/sugar_calendar.py` | Writers Guild | WordPress plugin; list + detail pages |
| Songkick | `lib/songkick.py` | Bluebird, Blockhouse | Venue event pages |
| Eventbrite | `scrapers/eventbrite.py` | Morgenstern Books, Nerd Nite | Organizer page → JSON-LD |
| Mobilize.us | `scrapers/mobilize.py` | Indivisible | Organizer event pages |
| The Events Calendar (Tribe) | `lib/tribe_events.py` | NAMI | WordPress plugin REST API; bypasses WAF-blocked ICS |
| Localist | `scrapers/localist.py` | McCormick's Creek SP, Brown County SP | events.in.gov JSON API; filter by venue_id |
| JSON-LD | `lib/jsonld.py` | (used by Eventbrite) | Schema.org Event extraction |

---

## Discovery Run Log

### 2026-02-08: Initial Discovery
- BloomingtonOnline Google Calendars (3 feeds)
- B-Square Bulletin Google Calendars (4 feeds)
- Parks and Recreation Google Calendar
- IU LiveWhale feeds (3 initial, expanded to 17)
- Meetup groups (2 active of 5 probed)

### 2026-02-17: Topical Search
- Bloomington Farmers Market (Google Calendar)
- Searched all curator-guide topics; most independent venues use Squarespace/Wix (no ICS)

### 2026-02-18: Sports & Outdoor
- Bloomington Bicycle Club (Google Calendar, ~5023 events)

### 2026-03-02: Scraper Buildout (51 sources)
- WonderLab, First United Church, Community Band, Brown County Playhouse, Upland (ICS feeds)
- Cardinal Spirits, Sassafras Audubon, Master Gardeners, People's Market (Squarespace scrapers)
- Sycamore Land Trust, Constellation, Cicada Cinema, Indivisible, Morgenstern Books (custom scrapers)
- Bloominglabs, Let's Go! Bloomington, City Boards & Commissions (Google Calendars)
- Lotus Festival (ICS)

### 2026-03-28: Current Session (59 sources)
- **WFHB Community Calendar** (~349) — ai1ec scraper; aggregator covering many venues. New platform: `lib/ai1ec.py`
- **Writers Guild at Bloomington** (~7) — Sugar Calendar scraper. New platform: `lib/sugar_calendar.py`
- **Nerd Nite Bloomington** (~1) — Eventbrite organizer 95199764993
- **IU Eskenazi School of Art** (~94) — LiveWhale `group_id/11`
- **FAR Center for Contemporary Arts** (~4) — Craft CMS scraper
- **Redbud Books** (~348) — Google Calendar
- **Habitat for Humanity Monroe County** (~4) — WordPress scraper
- **The Bishop** — SSL fix (`verify=False`)
- **Oblique strategy**: WFHB covers Bishop Orbit Room events, library-hosted events, and venues with no own calendar

---

## Notes

### Timezone
Bloomington, IN uses `America/Indiana/Indianapolis` (Eastern, no DST changes since 2006).

### Probe Commands
```bash
# Check for hidden ICS/RSS
curl -sL "<URL>" | grep -i -E "(ical|\.ics|webcal|calendar\.google|rss|xml|feed)"

# Check ICS feed validity
curl -sL "<URL>" | head -5  # Should start with BEGIN:VCALENDAR

# Discover IU LiveWhale group_id from page source
curl -sL "https://events.iu.edu/{group}/" | grep -o '"group_id":"[0-9]*"'
```

### Key Observations
- Most independent arts/culture venues in Bloomington use Squarespace or Wix (no ICS)
- WFHB is the best "oblique strategy" — curated community aggregator covering venues that don't have their own calendars
- BloomingtonOnline calendars capture most community events
- IU LiveWhale feeds capture most university arts/culture events
- Yoga/wellness/fitness is a coverage gap — all studios use MindBody/Squarespace class schedules
- Volunteerism is a coverage gap — Volunteer Network (Galaxy Digital) has no feed export
