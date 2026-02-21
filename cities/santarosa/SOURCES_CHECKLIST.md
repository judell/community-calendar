# Santa Rosa / Sonoma County Calendar Source Checklist

## Currently Implemented

### Live ICS Feeds
| Source | URL | Notes |
|--------|-----|-------|
| Arlene Francis Theater | Google Calendar | Events at local theater |
| Luther Burbank Center | `lutherburbankcenter.org/events/?ical=1` | Major performing arts venue |
| Schulz Museum | `schulzmuseum.org/events/?ical=1` | Charles Schulz museum events |
| Sonoma.com | `sonoma.com/events/?ical=1` | Regional tourism/events |
| GoLocal Coop | `golocal.coop` Tribe Events | Local business coop |
| Sonoma County AA | `sonomacountyaa.org/events/?ical=1` | Recovery community |
| DSA Sonoma County | Google Calendar | Political org |
| Sonoma Community Center | `sonomacommunitycenter.org/events/?ical=1` | Tribe Events; tai chi, dancing, printmaking, bluegrass, sewing (30 events) |
| Santa Rosa Symphony | `srsymphony.org/events/?ical=1` | Tribe Events; concerts and youth ensembles |

### Scraped Sources
| Source | Scraper | Notes |
|--------|---------|-------|
| Monroe County Library (Sonoma) | `library_intercept.py` | Library events |
| North Bay Bohemian | `cityspark/bohemian.py` | Alt-weekly events calendar |
| Press Democrat | `cityspark/pressdemocrat.py` | Newspaper events |
| Sonoma County Parks | `sonoma_parks.py` | Regional parks |
| California Theatre | `cal_theatre.py` | Historic theater |
| Copperfield's Books | `copperfields.py` | Bookstore events |
| Sonoma County Gov | `sonoma_county_gov.py` | Government meetings |
| Cafe Frida | Scraper | Music venue |
| SRCC | `srcc.py` | Santa Rosa Chamber? |
| Museum of Sonoma County | ICS | Local museum |

### City of Santa Rosa Calendars
Multiple ICS feeds from `srcity.org`:
- Main Calendar
- City Offices Closed
- Recreation and Parks
- Events

---

## Meetup Groups (Discovered 2025-02-08)

Ran Meetup discovery playbook. Found 66 groups, 33 with active events.

### Recommended High-Value Groups (Ready to Add)

| Group | ICS URL | Events | Category | Notes |
|-------|---------|--------|----------|-------|
| sonoma-county-go-wild-hikers | `meetup.com/sonoma-county-go-wild-hikers/events/ical/` | 3 | Outdoor | Local hiking group - "Islands in the Sky", "Lake Sonoma Hike" |
| shutupandwritewinecountry | `meetup.com/shutupandwritewinecountry/events/ical/` | 10 | Arts | Writing meetups in Petaluma/Sebastopol |
| scottish-country-dancing | `meetup.com/scottish-country-dancing/events/ical/` | 10 | Dance | Weekly classes at Monroe Hall |
| sonoma-county-womens-wine-club | `meetup.com/sonoma-county-womens-wine-club/events/ical/` | 9 | Social/Wine | Wine club + social events |
| santa-rosa-toastmasters-public-speaking-meetup-group | `meetup.com/santa-rosa-toastmasters-public-speaking-meetup-group/events/ical/` | 10 | Professional | Weekly meetings |
| nataraja-school-of-traditional-yoga | `meetup.com/nataraja-school-of-traditional-yoga/events/ical/` | 7 | Wellness | Yoga/pranayama classes |
| santa-rosa-womens-creativity-collective | `meetup.com/santa-rosa-womens-creativity-collective/events/ical/` | 6 | Arts | Creative workshops at The Arthaus |
| sonoma-county-boomers | `meetup.com/sonoma-county-boomers/events/ical/` | 6 | Social | Social events for boomers |

**EXCLUDED** (events are international destinations, not local):
- ~~The-International-Wanderers~~ - Travel trips to Patagonia, Ireland, Alaska, etc.
- ~~culturelovers~~ - International travel to Thailand, Egypt, Japan, etc.

### Other Active Groups (Lower Priority)

| Group | Events | Notes |
|-------|--------|-------|
| Hidden-Backroads-Adventures | 10 | Speed dating / social events |
| PlayYourCourt-Santa-Rosa-Tennis | 10 | Tennis - may be commercial |
| apa-pool-league | 10 | Pool league |
| real-estate-investor-community-santa-rosa | 10 | Real estate networking |
| Alternative-Healing-Exploration | 10 | Healing workshops |
| northern-california-plant-medicine-community | 10 | Plant medicine events |
| the-unstruck-drum-center-for-shamanism-healing | 8 | Shamanism events |
| sarogn | 7 | Unknown category |
| the-santa-rosa-spiritual-experiences-group | 6 | Spiritual events |
| north-bay-social-group-20s-and-30s | 3 | Young adult social |
| bce-before-christian-era | 3 | Historical interest |
| entheogens-in-sonoma | 3 | Entheogens |
| Woodworking-Workshops-for-Women | 2 | Woodworking |
| lets-go-golden-girls | 2 | Women's social |
| full-circle-studio | 2 | Studio events |

### Groups with No Current Events
The following groups exist but had no upcoming events at time of discovery:
ai-northbay, ambgroup, bootstrapped-af-podcast-mastermind-group, happy-over-50, 
kayaking-sonoma-beyond, ladieswithnobabies, localbitcoin-meetup, north-bay-adventures, 
north-bay-hikers-born-1990-2000, santa-rosa-30s-40s-50s-meet-and-hangout-group, 
senior-walkabouters, sonoma-county-millennials, sonoma-county-shenanigans, 
Sonoma-County-Photography-Group, Sonoma-County-Wanderers, womens-wellness-meetup-group

---

## Eventbrite (Retired 2026-02-15)

Retired: Eventbrite scraper stopped producing results (HTML scraping broke). No public feeds available.

---

## Potential Additional Sources

### Venues to Investigate
| Source | URL | Status |
|--------|-----|--------|
| Raven Performing Arts Theater | `raventheater.org` | PENDING |
| 6th Street Playhouse | `6thstreetplayhouse.com` | PENDING |
| Glaser Center | `glasercenter.com` | PENDING |
| Wells Fargo Center | ? | PENDING |

### Organizations
| Source | URL | Status |
|--------|-----|--------|
| Sonoma County Farm Trails | `farmtrails.org` | PENDING |
| Sonoma Land Trust | `sonomalandtrust.org` | PENDING |
| LandPaths | `landpaths.org` | PENDING - outdoor events |

### Colleges
| Source | URL | Status |
|--------|-----|--------|
| Santa Rosa Junior College | `calendar.santarosa.edu/live/ical/events` | ✅ ADDED (LiveWhale, 114 events) |
| Sonoma State University | `sonoma.edu/events` | PENDING |

---

## Tockify Calendars (Discovered 2026-02-08)

| Source | ICS URL | Events | Notes |
|--------|---------|--------|-------|
| Rileystreet Art Supply | `tockify.com/api/feeds/ics/rileystreet.art.com` | 561 | Multi-location art supply store, events tagged by location |

## Additional Meetup Groups (Discovered 2026-02-08)

| Group | ICS URL | Events | Notes |
|-------|---------|--------|-------|
| amorc-santa-rosa-pronaos | `meetup.com/amorc-santa-rosa-pronaos/events/ical/` | 10 | Monthly Mystical Seekers Series |
| sarogn (Game Night) | `meetup.com/sarogn/events/ical/` | 7 | 3rd Saturday board/card games |

## CitySpark / Shared Upstream (Discovered 2026-02-08)

The Bohemian, Press Democrat, and NorCal Public Media calendars all use **CitySpark** as their upstream platform. ~58% of events overlap between Bohemian and Press Democrat. NorCal Public Media (acct #6164) would mostly duplicate existing coverage.

| Publisher | CitySpark Slug | PPID | Geo Radius |
|-----------|---------------|------|------------|
| Bohemian | `Bohemian` | 9093 | 30mi |
| Press Democrat | `SRPressDemocrat` | 8662 | 40mi |
| NorCal Public Media | `norcalpublicmedia` | 6164 | unknown |

## Non-Starters (Investigated 2026-02-08)

| Source | Platform | Why |
|--------|----------|-----|
| Cal Theatre (caltheatre.com) | Wix | No calendar export |
| Downtown Santa Rosa (downtownsantarosa.org) | Unknown | No discoverable feed |
| Santa Rosa Metro Chamber | Unknown | No discoverable feed |
| Sonoma Valley Events (sonomavalleyevents.com) | GatherBoard | RSS page says "Coming Soon" |
| Bandsintown | Proprietary | 403, no public feed |
| Visit Santa Rosa (visitsantarosa.com) | Simpleview | Tourism site, no public feed |
| Brew Coffee and Beer (brewcoffeeandbeer.com) | WordPress (All-in-One Event Calendar) | ICS feed exists but empty; site directs to Facebook for events |
| Happy over 50 Meetup | Meetup | 0 events |
| NorCal Public Media | CitySpark | Would mostly duplicate Bohemian + Press Democrat |

---

## Notes

- Santa Rosa is the largest city in Sonoma County (Wine Country)
- Many events are wine/food related
- Strong outdoor recreation community (hiking, biking)
- Arts scene centered around downtown Santa Rosa

## Direct Scraper Sources (Added 2026-02-13)

### Sebastopol Center for the Arts (SebArts)
| Field | Value |
|-------|-------|
| URL | https://www.sebarts.org/classes-and-events |
| Platform | Squarespace |
| Scraper | `scrapers/sebarts.py` |
| Output | `cities/santarosa/sebarts.ics` |
| Events Found | 29 (as of 2026-02-13) |

**Note:** SebArts events were already appearing via the Bohemian (CitySpark) feed, but this direct scraper provides:
- Faster updates (no dependency on Bohemian's crawl schedule)
- All events (not just those Bohemian editors select)
- More reliable event details

### Sebastopol Documentary Film Festival
| Field | Value |
|-------|-------|
| URL | https://www.sebastopolfilm.org/ |
| Platform | Squarespace (static pages) |
| Status | No dedicated events feed needed |

**Note:** SDFF events appear on SebArts calendar (they're hosted there). For example:
- SDFF 2026 Launch Party (Feb 20, 2026) shows on SebArts as "SDFF Program LAUNCH/ Q&A"
- Festival dates: April 9-12, 2026

The film festival doesn't maintain its own events feed - it's more of a promotional site. Their events are listed through SebArts and may also appear in Bohemian/Press Democrat coverage.

## City of Santa Rosa Legistar (Added 2026-02-14)

| Field | Value |
|-------|-------|
| URL | https://santa-rosa.legistar.com/Calendar.aspx |
| API | `https://webapi.legistar.com/v1/santa-rosa/events` |
| Platform | Legistar (Granicus) |
| Script | `scrapers/legistar.py --client santa-rosa` |
| Output | `cities/santarosa/legistar.ics` |

**Note:** The Legistar WebAPI provides structured JSON data for all city government meetings - City Council, Planning Commission, Board of Public Utilities, Design Review Board, and many other boards and commissions. This replaces the stale srcity.org ICS feeds which were not being updated.

**Coverage:** Future meetings only (events are added to Legistar as they're scheduled, typically a few weeks/months ahead). Historical meetings remain in Legistar but are filtered out.

**Cancelled meetings:** The script automatically skips events with `EventAgendaStatusName: "Cancelled"`.
