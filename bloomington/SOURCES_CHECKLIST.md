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
| **Buskirk-Chumley Theater** | `buskirkchumley.org/events/` | BLOCKED | Site blocks scrapers (403); RSS feed limited to 3 items |
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
| **Visit Bloomington** | `visitbloomington.com/events/` | PENDING | Tourism aggregator |

---

## Tier 3: Lower Priority / Seasonal / Discovery

### Markets / Food

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Winter Farmers' Market** | `bloomingtonwinterfarmersmarket.com/` | PENDING | Seasonal |
| **Community Farmers' Market** | `bloomington.in.gov/farmers-market` | PENDING | City site |
| **People's Market** | `peoplesmarketbtown.org/gatherings` | PENDING | Has per-event ICS |

### Festivals

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **Lotus Festival** | `lotusfest.org/schedule/` | PENDING | Seasonal (fall) |

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
| **UU Church of Bloomington** | `uubloomington.org/events/` | PENDING | May have hidden GCal |
| **Friends Meeting** | `bloomingtonfriendsmeeting.org/calendar` | PENDING | |

### Alt-Weeklies / Regional

| Source | URL | Status | Notes |
|--------|-----|--------|-------|
| **NUVO** | `nuvo.newsnirvana.com/event/` | PENDING | Regional, derivative |
| **Do317** | `do317.com` | PENDING | Indy-centric |

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
- [ ] UU Church of Bloomington
- [ ] Neighborhood associations
- [ ] Visit Bloomington

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
