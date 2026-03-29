# Bloomington Calendar Source Checklist

Prioritized list of potential event sources for the Bloomington, IN community calendar.

## Currently Implemented

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Monroe County Public Library | Scraper | — | `library_intercept.py --location bloomington` |
| The Bluebird | Songkick | ~9 | `songkick.py` venue 78904 |
| Blockhouse Bar | Songkick | ~2 | `songkick.py` venue 3607354 |
| Boys & Girls Club | ICS | — | `bgcbloomington.org` WordPress Events Calendar |
| City of Bloomington | ICS | ~374 | Google Calendar feed |
| City Boards & Commissions | ICS | — | Google Calendar feed (added 2026-03) |
| Bloomington Arts | ICS | — | Tockify API feed |
| IU Jacobs School of Music | ICS | ~514 | LiveWhale `group_id/56` |
| IU Auditorium | ICS | ~23 | LiveWhale `group_id/378` |
| Eskenazi Museum of Art | ICS | ~74 | LiveWhale `group_id/234` |
| IU Cinema | ICS | ~19 | LiveWhale `group_id/81` (added 2026-03) |
| IU La Casa Latino Cultural Center | ICS | ~109 | LiveWhale `group_id/59` (added 2026-03) |
| IU Maurer School of Law | ICS | ~80 | LiveWhale `group_id/64` (added 2026-03) |
| IU Kelley School of Business | ICS | ~48 | LiveWhale `group_id/343` (added 2026-03) |
| IU Arts & Humanities Institute | ICS | ~183 | LiveWhale `group_id/130` (added 2026-03) |
| IU Bloomington Libraries | ICS | ~436 | LiveWhale `group_id/261` (added 2026-03) |
| IU Theatre & Dance | ICS | ~20 | LiveWhale `group_id/218` (added 2026-03) |
| IU Asian Culture Center | ICS | ~26 | LiveWhale `group_id/314` (added 2026-03) |
| IU First Nations Center | ICS | ~14 | LiveWhale `group_id/275` (added 2026-03) |
| IU LGBTQ+ Culture Center | ICS | ~4 | LiveWhale `group_id/237` (added 2026-03) |
| IU Black Film Center & Archive | ICS | ~9 | LiveWhale `group_id/221` (added 2026-03) |
| IU Neal-Marshall Black Culture Center | ICS | — | LiveWhale `group_id/235` (seasonal, added 2026-03) |
| IU Hamilton Lugar School | ICS | — | LiveWhale `group_id/135` (Global & International Studies, added 2026-03) |
| IU Moving Image Archive | ICS | ~151 | LibCal `cid=5914` (added 2026-03) |
| IU Scholars' Commons | ICS | ~26 | LibCal `cid=1228` (added 2026-03) |
| IU beINvolved Student Orgs | ICS | ~16900 | CampusLabs `iub.campuslabs.com` (added 2026-03) |
| B-Square: Government | ICS | ~8887 | Google Calendar (mostly historical, future-filtered by combine_ics) |
| B-Square: Misc Civic Events | ICS | ~252 | Google Calendar |
| B-Square: Critical Mass | ICS | ~8 | Google Calendar (monthly group bike ride) |
| B-Square: BPTC Public Meetings | ICS | ~15 | Google Calendar (transit board meetings) |
| The Comedy Attic | Scraper | ~32 | `comedy_attic.py` |
| The Bishop | Scraper | ~4 | `the_bishop.py` (SSL verify=False, cert expired 2026-03) |
| BloomingtonOnline: Events | ICS | ~224 | Google Calendar - community events |
| BloomingtonOnline: Food & Drink | ICS | ~133 | Google Calendar - restaurant/brewery specials |
| BloomingtonOnline: Shopping | ICS | ~18 | Google Calendar - markets, deals |
| Parks and Recreation | ICS | ~1615 | Google Calendar via city website |
| Knobstone Hiking Trail Meetup | ICS | ~10 | Meetup group - regional hiking |
| Bloomington Atheists Meetup | ICS | ~10 | Meetup group - local social/discussion |
| ~~Bloomington Board Games Meetup~~ | ICS | — | Removed: 403 private (2026-03) |
| ~~Bloomington Remote Workers Meetup~~ | ICS | — | Removed: dormant (2026-03) |
| Bloomington Farmers Market | ICS | ~307 | Google Calendar via city website |
| Bloomington Bicycle Club | ICS | ~5023 | Google Calendar - cycling rides, weekly events |
| WonderLab Museum | ICS | ~30+ | WordPress ICS `?ical=1` — Cloudflare blocks HTML but not ICS! (added 2026-03) |
| First United Church | ICS | ~50+ | WordPress ICS — rich community hub (DSA, Al-Anon, scouts, etc.) (added 2026-03) |
| Bloomington Community Band | ICS | ~20 | WordPress Events Calendar ICS (added 2026-03) |
| Brown County Playhouse | ICS | ~12 | WordPress Events Calendar ICS (added 2026-03) |
| Upland Brewing | ICS | — | WordPress Events Calendar ICS — dormant, populates seasonally (added 2026-03) |
| Bloominglabs Makerspace | ICS | ~10+ | Google Calendar (added 2026-03) |
| Cardinal Spirits | Scraper | ~5 | Squarespace scraper (added 2026-03) |
| Sassafras Audubon Society | Scraper | ~31 | Squarespace scraper (added 2026-03) |
| Monroe County Master Gardeners | Scraper | ~62 | Squarespace scraper (added 2026-03) |
| Sycamore Land Trust | Scraper | ~131 | Custom WordPress scraper (added 2026-03) |
| Constellation Stage & Screen | Scraper | ~45 | Spektrix API scraper (added 2026-03) |
| Cicada Cinema | Scraper | ~6 | Shopify products API scraper (added 2026-03) |
| People's Market | Scraper | ~10 | Squarespace scraper |
| Lotus Festival | ICS | ~7 | WordPress Events Calendar ICS |
| Indivisible Central Indiana | Mobilize.us scraper | ~21 | `mobilize.py` — civic/political organizing (added 2026-03) |
| Let's Go! Bloomington | ICS | — | Google Calendar aggregator — indie venues, shows, art openings (added 2026-03) |
| Morgenstern Books | Eventbrite scraper | ~9 | Author events, book clubs via Eventbrite organizer page (added 2026-03) |
| WFHB Community Calendar | Scraper | ~349 | `wfhb_calendar.py` — ai1ec (All-in-One Event Calendar) HTML scraper; curated community events (added 2026-03) |
| Nerd Nite Bloomington | Eventbrite scraper | ~1 | `eventbrite.py` organizer 95199764993 — quarterly at The Bishop (added 2026-03) |
| Writers Guild at Bloomington | Scraper | ~7 | `writers_guild.py` — Sugar Calendar scraper; prose, poetry, spoken word (added 2026-03) |
| IU Eskenazi School of Art | ICS | ~94 | LiveWhale `group_id/11` — exhibitions, lectures, MFA shows (added 2026-03) |
| FAR Center for Contemporary Arts | Scraper | ~4 | `far_center.py` — Craft CMS scraper; gallery openings, film, workshops (added 2026-03) |

---

## Tier 1: ICS Feeds — Probed

### IU LiveWhale System

Feed URL pattern: `https://events.iu.edu/live/ical/events/group_id/{id}`
Docs: https://documentation.events.iu.edu/feed-and-linked-calendars/ical-feed.html

| Source | Group ID | Status | Notes |
|--------|----------|--------|-------|
| **Jacobs School of Music** | 56 | DONE | ~514 events |
| **IU Auditorium** | 378 | DONE | ~23 events |
| **Eskenazi Museum of Art** | 234 | DONE | ~74 events |
| **IU Cinema** | 81 | DONE | ~19 events (added 2026-03) |
| **La Casa Latino Cultural Center** | 59 | DONE | ~109 events (added 2026-03) |
| **Maurer School of Law** | 64 | DONE | ~80 events (added 2026-03) |
| **Kelley School of Business** | 343 | DONE | ~48 events (added 2026-03) |
| **College Arts + Humanities Institute** | 130 | DONE | ~183 events (added 2026-03) |
| **IU Bloomington Libraries** | 261 | DONE | ~436 events (added 2026-03) |
| **IU Theatre & Dance** | 218 | DONE | ~20 events (added 2026-03) |
| **Asian Culture Center** | 314 | DONE | ~26 events (added 2026-03) |
| **First Nations Center** | 275 | DONE | ~14 events (added 2026-03) |
| **LGBTQ+ Culture Center** | 237 | DONE | ~4 events (added 2026-03) |
| **Black Film Center & Archive** | 221 | DONE | ~9 events (added 2026-03) |
| **Neal-Marshall Black Culture Center** | 235 | DONE | Seasonal (added 2026-03) |
| **Hamilton Lugar School** | 135 | DONE | Global & International Studies (added 2026-03) |

### Government / Civic ICS

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Monroe County Gov** | `co.monroe.in.us/egov/apps/events/calendar.egov?view=ical` | BLOCKED | Indiana state platform, no ICS export found |
| **MCCSC School Calendar** | `mccsc.edu/site/handlers/icalfeed.ashx?MIID=1` | BLOCKED | 404 — URL dead, site migrated to ParentSquare |
| **SIREN Solar** | `sirensolar.org/events/?ical=1` | BLOCKED | Returns HTML not ICS; Tribe Events Calendar plugin but ICS export broken |

### Additional Google Calendars (B-Square Bulletin)

| Source | Calendar Name | Status | Events | Notes |
|--------|---------------|--------|--------|-------|
| **Government** | `bloomington.in.gov_35a6..` | DONE | ~8887 | Aggregation of all gov activity |
| **Misc Civic Events** | `4dj0guhji98..` | DONE | ~252 | |
| **Critical Mass Bloomington** | `2gd73d7gc4..` | DONE | ~8 | Monthly group ride |
| **BPTC Public Meetings** | `c_02o6fd3er..` | DONE | ~15 | Transit board |

---

## Tier 2: Scrapeable HTML (Known Patterns)

### Music / Venues / Performing Arts

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Buskirk-Chumley Theater** | `buskirkchumley.org/events/` | DONE | `buskirk_chumley.py` scraper (~38 events) |
| **The Bishop** | `thebishopbar.com/events` | DONE | `the_bishop.py` scraper |
| **IU Auditorium (public site)** | `iuauditorium.com/events` | SKIP | Covered by LiveWhale feed |

### Comedy / Talk / Nightlife

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Comedy Attic** | `comedyattic.com/events` | DONE | `comedy_attic.py` scraper |

### Museums / Arts / Lectures

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Eskenazi Museum (public)** | `artmuseum.indiana.edu/news-events/calendar/` | SKIP | Covered by LiveWhale feed |
| **Eskenazi School** | `events.iu.edu/soaadiub/` | DONE | LiveWhale `group_id/11` (~94 events) |

### Family / Kids / Science

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **WonderLab Museum** | `wonderlab.org/events/?ical=1` | ✅ DONE | Cloudflare blocks HTML pages but ICS export works! |

### Libraries

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Monroe County Public Library** | `monroecounty.librarycalendar.com/` | PENDING | May have hidden feed; already have library_intercept |

### Community Media

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **WFHB Community Calendar** | `wfhb.org/calendar/` | DONE | `wfhb_calendar.py` — ai1ec HTML scraper (~349 events) |

### Visit Bloomington

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Visit Bloomington** | `visitbloomington.com/events/` | BLOCKED | Simpleview CMS - no public API; would need HTML scraping |

---

## Tier 3: Lower Priority / Seasonal / Discovery

### Markets / Food

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Winter Farmers' Market** | `bloomingtonwinterfarmersmarket.com/` | PENDING | Seasonal |
| **Community Farmers' Market** | `bloomington.in.gov/farmers-market` | PENDING | City site |
| **People's Market** | `peoplesmarketbtown.org/gatherings` | DONE | Squarespace scraper (~10 events) |

### Festivals

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Lotus Festival** | `lotusfest.org/events/?ical=1` | DONE | ICS feed (~7 events) |

### Newspapers / Journalism

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Herald-Times** | `heraldtimesonline.com/things-to-do/events/` | PENDING | Derivative |
| **Indiana Daily Student** | `idsnews.com/events` | PENDING | Derivative |
| **Bloomingtonian** | `bloomingtonian.com/calendar/` | PENDING | Community blog |

### Neighborhoods / Grassroots

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Near West Side NA** | `nwsbloomington.org/events` | PENDING | Neighborhood assoc |
| **Prospect Hill NA** | `prospecthillna.org/events` | PENDING | Neighborhood assoc |
| **Elm Heights NA** | `elmheightsbloomington.org/calendar` | PENDING | Neighborhood assoc |

### Religious / Interfaith

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **UU Church of Bloomington** | `uubloomington.org/` | LOW PRIORITY | Uses Planning Center/Church Center (no public API); events mostly internal church activities |
| **Friends Meeting** | `bloomingtonfriendsmeeting.org/` | DEAD END | Squarespace; calendar behind member-only page, no public feed |

### Alt-Weeklies / Regional

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **NUVO** | `nuvo.newsnirvana.com/event/` | PENDING | Regional, derivative |
| **Do317** | `do317.com` | PENDING | Indy-centric |

---

## Discovery Run: 2026-02-08

### New Google Calendar Feeds (via BloomingtonOnline.com)

bloomingtononline.com embeds a master Google Calendar with multiple source calendars:

| Source | Events | Status | Notes |
|--------|--------|--------|-------|
| **Events** | ~224 | ✅ IMPLEMENTED | Community events, film screenings, workshops |
| **Shopping & Deals** | ~18 | ✅ IMPLEMENTED | Farmers' market, vintage market, store demos |
| **Food & Drink Specials** | ~133 | ✅ IMPLEMENTED | Restaurant/brewery specials |
| **Cool Family Events** | ~6 | NOT FOUND | Calendar no longer on site |
| **Music** | ~467 | SKIP | Heavy overlap with IU Jacobs LiveWhale feed |
| **IU Events (import)** | ~457 | SKIP | Duplicate of IU LiveWhale |
| **Ivy Tech** | ~1169 | SKIP | Statewide academic calendar, not community events |

### City of Bloomington Parks and Recreation

| Source | Events | Status | Notes |
|--------|--------|--------|-------|
| **Parks and Recreation** | ~1615 | ✅ IMPLEMENTED | Concerts, fitness, nature, family events. Different from existing USB calendar |

**Note:** The existing `bloomington.in.gov_1b95au4d2ueudldosb024fimp0` is actually "Utilities Service Board" (board meetings). The Parks & Rec calendar is the community-relevant one.

### IU LiveWhale All-Events Feed

| Source | Events | Status | Notes |
|--------|--------|--------|-------|
| **IU All Events** | ~614 | NOT IMPLEMENTED | Would subsume individual IU feeds; kept individual feeds for attribution |

### Meetup Groups (New)

| Group | Events | Status | Notes |
|-------|--------|--------|-------|
| Knobstone Hiking Trail Assoc | 10 | ✅ IMPLEMENTED | Southern Indiana hiking |
| Bloomington Atheists | 10 | ✅ IMPLEMENTED | Local social/discussion group |
| Bloomington Board Games | 0 | BLOCKED | Meetup disabled ICS for this group |
| GDG Bloomington | 0 | INACTIVE | Feed works but no events |
| Fun 50+ Active Singles | 0 | INACTIVE | Feed works but no events |

### Dead Ends (2026-02-08)

| Source | Reason |
|--------|--------|
| The Back Door (Tockify) | ICS export disabled on their plan |
| ~~WFHB Community Calendar~~ | ~~Mod_Security blocks ICS export~~ — RESOLVED: HTML scraper bypasses WAF with browser UA (2026-03) |
| Indiana Public Media | Brightspot CMS, no ICS/RSS for events |
| WCLS 97.7 | Site suspended |
| IDS Events Calendar | No ICS feed |
| Chamber of Commerce Atlas | No ICS feed |
| Pillar Arts | WordPress + The Events Calendar but ICS export broken (returns HTML), calendar appears inactive |

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Bandsintown Bloomington | Derivative, duplicate-heavy |
| MCCSC School Calendar | 404 — site migrated to ParentSquare |
| Monroe County Gov ICS | Indiana state platform, no ICS export |
| SIREN Solar ICS | Tribe Events Calendar ICS export broken (returns HTML) |

---

## Implementation Roadmap

### Phase 1: ICS Feed Integration
- [x] IU LiveWhale feeds (Jacobs, Auditorium, Eskenazi)
- [x] B-Square Bulletin Google Calendars (4 feeds)
- [~] Monroe County government ICS — BLOCKED: no ICS export
- [~] MCCSC school calendar ICS — BLOCKED: 404
- [~] SIREN Solar ICS — BLOCKED: returns HTML

### Phase 2: High-Value HTML Scrapers
- [ ] Buskirk-Chumley Theater
- [ ] The Bishop
- [ ] Comedy Attic
- [ ] WonderLab Museum
- [x] WFHB Community Calendar (ai1ec HTML scraper)

### Phase 3: Community / Civic
- [~] UU Church of Bloomington — LOW PRIORITY: mostly internal events
- [~] Neighborhood associations — Sites appear inactive/down
- [~] Visit Bloomington — BLOCKED: Simpleview CMS, no API

### Phase 4: Topic-Based Discovery (Meetup Groups)
Discovered via topic search - all have ICS feeds at `https://www.meetup.com/{urlname}/events/ical/`

| Group | URL Name | Events | Notes |
|-------|----------|--------|-------|
| Bloomington Atheists | `Bloomington-Atheists-and-Rationally-Awesome-People` | ~10 | ✅ ADDED - Local social/discussion group |
| Knobstone Hiking Trail Assoc | `knobstone-hiking-trail-association-of-indiana-meetup` | ~10 | Based in Martinsville (~20mi) - regional |

---

## Notes

### IU LiveWhale Feed Discovery
Docs: https://documentation.events.iu.edu/feed-and-linked-calendars/ical-feed.html

Working pattern: `https://events.iu.edu/live/ical/events/group_id/{id}`

Group IDs discovered by scraping page source for `group_id` in the LiveWhale JS config:
- Jacobs School of Music: 56
- IU Auditorium: 378
- Eskenazi Museum of Art: 234

The documented pattern `https://events.iu.edu/{group}/calendar.ics` does NOT work (returns HTML).

### Probe Commands
```bash
# Check for hidden ICS/RSS
curl -sL "<URL>" | grep -i -E "(ical|\.ics|webcal|calendar\.google|rss|xml|feed)"

# Check ICS feed validity
curl -sL "<URL>" | head -5  # Should start with BEGIN:VCALENDAR

# Discover IU LiveWhale group_id from page source
curl -sL "https://events.iu.edu/{group}/" | grep -o '"group_id":"[0-9]*"'
```

### Timezone
Bloomington, IN uses `America/Indiana/Indianapolis` (Eastern, no DST changes since 2006).

---

## Phase 2 Topical Search Results: 2026-02-17

### Sources Found and Added

| Source | Events | Status | Notes |
|--------|--------|--------|-------|
| **Bloomington Farmers Market** | ~307 | ✅ ADDED | Google Calendar via city website |

### Sources Evaluated - Not Added

| Source | Reason |
|--------|--------|
| Limestone Post Magazine | CitySpark-powered (derivative aggregator) |
| Bloomington Brewing Co | Squarespace site, no ICS export |
| Indiana Brewers Guild | Statewide feed, only 3 events |
| Bloomington Volunteer Network | Custom platform, no ICS export |
| LGBTQ+ Culture Center IU | Covered by IU All Events feed |
| I Run, You Run Meetup | Actually in Arlington, VA (not Bloomington) |
| Bloomington RUN Meetup | ICS export disabled |

### Meetup Groups - ICS Works but 0 Events

These groups have working ICS feeds but no upcoming events as of 2026-02-17:

- Bloomington Bitcoin Meetup
- Bloomington Pickleball Warehouse
- Bloomington Chess Study Group
- Bloomington Dance Meetup Group
- Creative Hearts Club (Artists)
- AWS Cloud Club at IU
- Fun 50+ Active Singles
- Bloomington Listening Meetup

### Categories Covered by Existing Sources

| Category | Coverage |
|----------|----------|
| Music | IU Jacobs, Bluebird, Bishop, BloomingtonOnline Music |
| Theater/Comedy | IU Auditorium, Comedy Attic |
| Arts | Bloomington Arts (Tockify), Eskenazi Museum |
| Outdoors | Knobstone Hiking Meetup, Parks & Rec |
| Community Events | BloomingtonOnline Events, B-Square calendars |
| Food & Drink | BloomingtonOnline Food & Drink, Farmers Market |
| Civic | City of Bloomington, B-Square Government |
| LGBTQ+ | Covered by IU All Events |
| Atheist/Skeptic | Bloomington Atheists Meetup |

---

## Phase 3: Custom Scrapers — IN PROGRESS

**Status as of 2026-02-17:** Phase 3 started.

### Scrapers Completed

| Source | URL | Events | Notes |
|--------|-----|--------|-------|
| Buskirk-Chumley Theater | `buskirkchumley.org/events/` | ~38 | `buskirk_chumley.py` - uses curl UA to bypass WAF |
| The Comedy Attic | `comedyattic.com/events` | ~30 | `comedy_attic.py` |
| The Bishop | `thebishopbar.com/events` | ~4 | `the_bishop.py` |
| People's Market | `peoplesmarketbtown.org/gatherings` | ~10 | Squarespace scraper |
| Lotus Festival | `lotusfest.org/events/?ical=1` | ~7 | ICS feed (discovered has ical) |

### Blocked / Cannot Scrape

| Source | URL | Reason |
|--------|-----|--------|
| WonderLab Museum | `wonderlab.org/events/` | Cloudflare challenge |
| ~~WFHB Community Calendar~~ | `wfhb.org/calendar/` | ~~mod_security blocks~~ RESOLVED: ai1ec HTML scraper with browser UA (2026-03) |
| Visit Bloomington | `visitbloomington.com/events/` | Simpleview CMS, no API |
| Winter Farmers' Market | `bloomingtonwinterfarmersmarket.com/` | Wix site, no scraping |

### Lower-Priority / May Not Need Scrapers

| Source | Notes |
|--------|-------|
| Herald-Times Events | Derivative aggregator |
| Neighborhood Associations | Sites appear inactive/minimal events |

---

## Discovery Run: 2026-02-18

### New Sources Found

| Source | Events | Status | Notes |
|--------|--------|--------|-------|
| **Bloomington Bicycle Club** | ~5023 | ✅ ADDED | Google Calendar - cycling rides, weekly events |

### Sources Evaluated - Not Added

| Source | Reason |
|--------|--------|
| BARA (Bloomington Area Runners) | Wix site, no ICS feed |
| Bloomington Yoga Collective | Squarespace, no ICS export |
| Bloomington Brewing Co | Squarespace, no ICS export |
| MaxPreps Bloomington North | Only 4 events (low volume) |
| MaxPreps Bloomington South | Only 2 events (low volume) |

### Meetup Groups Re-Verified

| Group | Events | Status |
|-------|--------|--------|
| Bloomington Atheists | 10 | ✅ Already implemented |
| Knobstone Hiking Trail | 10 | ✅ Already implemented |
| All other Bloomington Meetups | 0 | Inactive or ICS disabled |

---

### Current Coverage Summary

**56 sources implemented** (expanded from 51 on 2026-03-28) covering:
- University events (IU LiveWhale × 15, LibCal × 2, CampusLabs × 1)
- City/civic (Parks & Rec, Farmers Market, B-Square × 4, City Gov, Boards & Commissions)
- Arts/entertainment (Bloomington Arts, Comedy Attic, Bishop, Bluebird, Blockhouse, Brown County Playhouse, Cardinal Spirits, Constellation, Cicada Cinema)
- Community (BloomingtonOnline × 3, Library, Boys & Girls Club, First United Church, WonderLab, Community Band, Bloominglabs, WFHB)
- Literary (Writers Guild, Morgenstern Books, Nerd Nite)
- Interest groups (4 Meetup groups, Indivisible, Let's Go! Bloomington)
- Beverages (Upland Brewing, Cardinal Spirits)

**Estimated unique future events:** ~5,500+

### Phase 2 Topical Search Results: 2026-02-18

Searched across all curator-guide topics: music, theater, comedy, dance, film, art, crafts, literature, poetry, book clubs, writing, history, genealogy, philosophy, talks, hiking, walking, running, cycling, gardening, birding, conservation, yoga, fitness, mindfulness, wellness, beer, wine, food, cooking, farmers markets, trivia, board games, pets, wildlife, sustainability, kids, families, seniors, caregivers, newcomers, faith, LGBTQ+, cultural heritage, volunteering, mutual aid, civic engagement, tech, digital skills, careers.

#### Sources Evaluated - Not Added

| Source | Platform | Reason |
|--------|----------|--------|
| Limestone Post Magazine | CitySpark | Derivative aggregator |
| FAR Center for Arts | Craft CMS | No ICS export, would need scraper |
| Juniper Art Gallery | Custom | No calendar feed |
| Gallery Walk Bloomington | Wix | No ICS export |
| Bloomington PRIDE | Squarespace | No ICS export |
| Bloomington Volunteer Network | Custom | No ICS export |
| BARA (runners) | Wix | No ICS export |
| Bloomington Yoga Collective | Squarespace | No ICS export |
| Bloomington Brewing Co | Squarespace | No ICS export |
| Indiana Dance Company | Custom | Class schedules only |
| MotionArts Dance Academy | Custom | Class schedules only |
| Windfall Dancers | WordPress | No events feed |

#### Notes

- Most independent arts/culture venues in Bloomington use Squarespace or Wix (no ICS)
- Many sources are derivative (aggregate from existing sources)
- IU LiveWhale feeds already capture most university arts/culture events
- BloomingtonOnline calendars capture most community events
- Eskenazi Museum (IU) already covered via LiveWhale

---

## Discovery Run: 2026-03-28

### New Sources Added

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| **WFHB Community Calendar** | ai1ec scraper | ~349 | Curated community events — music, theater, trivia, workshops. Covers Orbit Room (Bishop downstairs) events not on Bishop's own site. New platform base: `lib/ai1ec.py` |
| **Nerd Nite Bloomington** | Eventbrite scraper | ~1 | Quarterly science talks at The Bishop. Organizer ID 95199764993 |
| **Writers Guild at Bloomington** | Sugar Calendar scraper | ~7 | Prose readings, poetry open mic, spoken word series at Morgenstern Books, Juniper Art Gallery, Backspace Gallery. New platform base: `lib/sugar_calendar.py` |

### Fixes

| Source | Fix |
|--------|-----|
| **The Bishop** | SSL cert expired; added `verify=False` to restore 4 events |

### Sources Evaluated — Not Added

| Source | Reason |
|--------|--------|
| Windfall Dancers | WordPress, no events feed — class schedules as plain text |
| Nerd Nite website | WordPress blog, no feed — covered via Eventbrite organizer page |
| Time & Tide Tattoo | Flash events announced only on Instagram/Facebook — not scrapable |

### Oblique Strategy Wins

- **WFHB covers Bishop Bar's Orbit Room** events (trivia, pinball league, songwriter showcases) that aren't on the Bishop's own website
- **WFHB covers library-hosted events** like We're Crankie Festival that aren't (yet) on the library's calendar
- **Earth Day at Switchyard Park** already covered by Parks & Rec Google Calendar feed

### New Platform Scrapers Created

| Platform | File | Used By | Notes |
|----------|------|---------|-------|
| All-in-One Event Calendar (ai1ec) | `lib/ai1ec.py` | WFHB | WordPress plugin; HTML agenda view with browser UA bypasses WAF |
| Sugar Calendar Lite | `lib/sugar_calendar.py` | Writers Guild | WordPress plugin; list page + detail page enrichment for locations |

### Remaining Pending (Tier 2/3)

| Source | Status | Notes |
|--------|--------|-------|
| ~~Eskenazi School of Art~~ | DONE | LiveWhale `group_id/11` (2026-03-28) |
| ~~FAR Center for Arts~~ | DONE | Craft CMS scraper (2026-03-28) |
| Friends Meeting | DEAD END | Squarespace, calendar behind member-only page |
| Winter Farmers' Market | BLOCKED | Wix, no scraping |
| Neighborhood Associations | LOW PRIORITY | Sites appear inactive |
| Visit Bloomington | BLOCKED | Simpleview CMS, no API |
