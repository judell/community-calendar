# Bloomington Calendar Source Checklist

Prioritized list of potential event sources for the Bloomington, IN community calendar.

## Currently Implemented

| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Monroe County Public Library | Scraper | — | `library_intercept.py --location bloomington` |
| The Bluebird | ICS (static) | — | `bluebird.ics` |
| Boys & Girls Club | ICS | — | `bgcbloomington.org` WordPress Events Calendar |
| City of Bloomington | ICS | ~374 | Google Calendar feed |
| Bloomington Arts | ICS | — | Tockify API feed |
| IU Jacobs School of Music | ICS | ~514 | LiveWhale `group_id/56` |
| IU Auditorium | ICS | ~23 | LiveWhale `group_id/378` |
| Eskenazi Museum of Art | ICS | ~74 | LiveWhale `group_id/234` |
| B-Square: Government | ICS | ~8887 | Google Calendar (mostly historical, future-filtered by combine_ics) |
| B-Square: Misc Civic Events | ICS | ~252 | Google Calendar |
| B-Square: Critical Mass | ICS | ~8 | Google Calendar (monthly group bike ride) |
| B-Square: BPTC Public Meetings | ICS | ~15 | Google Calendar (transit board meetings) |
| The Comedy Attic | Scraper | ~32 | `comedy_attic.py` |
| The Bishop | Scraper | ~4 | `the_bishop.py` |
| BloomingtonOnline: Events | ICS | ~224 | Google Calendar - community events |
| BloomingtonOnline: Food & Drink | ICS | ~133 | Google Calendar - restaurant/brewery specials |
| BloomingtonOnline: Shopping | ICS | ~18 | Google Calendar - markets, deals |
| Parks and Recreation | ICS | ~1615 | Google Calendar via city website |
| Knobstone Hiking Trail Meetup | ICS | ~10 | Meetup group - regional hiking |
| Bloomington Atheists Meetup | ICS | ~10 | Meetup group - local social/discussion |
| Bloomington Farmers Market | ICS | ~307 | Google Calendar via city website |
| Bloomington Bicycle Club | ICS | ~5023 | Google Calendar - cycling rides, weekly events |

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
| **Eskenazi School** | `eskenazi.indiana.edu/events/` | PENDING | HTML scrape |

### Family / Kids / Science

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **WonderLab Museum** | `wonderlab.org/events/` | BLOCKED | Behind Cloudflare challenge |

### Libraries

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Monroe County Public Library** | `monroecounty.librarycalendar.com/` | PENDING | May have hidden feed; already have library_intercept |

### Community Media

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **WFHB Community Calendar** | `wfhb.org/calendar/` | BLOCKED | Site blocks scrapers |

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
| **Friends Meeting** | `bloomingtonfriendsmeeting.org/calendar` | PENDING | |

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
| WFHB Community Calendar | Mod_Security blocks ICS export |
| Indiana Public Media | Brightspot CMS, no ICS/RSS for events |
| WCLS 97.7 | Site suspended |
| IDS Events Calendar | No ICS feed |
| Chamber of Commerce Atlas | No ICS feed |

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
- [ ] WFHB Community Calendar (JSON endpoint)

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
| WFHB Community Calendar | `wfhb.org/calendar/` | mod_security blocks |
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

**27 sources implemented** covering:
- University events (IU LiveWhale × 3)
- City/civic (Parks & Rec, Farmers Market, B-Square × 4, City Gov)
- Arts/entertainment (Bloomington Arts, Comedy Attic, Bishop, Bluebird)
- Community (BloomingtonOnline × 3, Library, Boys & Girls Club)
- Interest groups (2 Meetup groups)

**Estimated unique future events:** ~1,700+
