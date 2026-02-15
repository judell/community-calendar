# Raleigh-Durham (Research Triangle) Calendar Source Checklist

## Currently Implemented (34 sources)

### Universities
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| UNC Chapel Hill | Localist ICS | ~461 | All campus events |
| NC State University | Localist ICS | ~1,297 | All campus events |
| Duke University | Localist ICS | ~40 | All campus events |

### Museums & Cultural Resources
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| NC Dept. of Natural & Cultural Resources | Localist ICS | ~1,537 | Aggregates NC Museum of Art, History, Natural Sciences, Historic Sites — statewide |
| Ackland Art Museum | WordPress Tribe ICS | ~30 | Chapel Hill, UNC campus |
| Nasher Museum of Art | WordPress Tribe ICS | ~30 | Duke campus |
| NC Botanical Garden | WordPress Tribe ICS | ~13 | Chapel Hill, UNC |

### Community Organizations
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Triangle Land Conservancy | WordPress Tribe ICS | ~21 | Conservation hikes, volunteer days |
| Durham Central Park | WordPress Tribe ICS | ~8 | Farmers market, community events |

### Libraries
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Durham County Library | LibCal ICS | ~500 | Programs, workshops, kids events |

### Government
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| City of Durham | CivicPlus ICS | ~0 | Community calendar; currently empty, may populate seasonally |
| Wake County | Legistar scraper | 1 | Board of Commissioners, Planning Board, etc. |
| Town of Chapel Hill | Legistar scraper | 0 | Town Council, boards — meetings posted as scheduled |
| Durham County | Legistar scraper | 0 | Board of County Commissioners — meetings posted as scheduled |

### Cycling & Active Transportation
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Bike Durham Events | Google Calendar ICS | ~101 | Advocacy meetings, community rides |
| Triangle Cycling | Google Calendar ICS | ~1,925 | Cycling events across the Triangle |

### Breweries & Taprooms
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Gizmo Brew Works Durham | Google Calendar ICS | ~128 | Live music, trivia, beer releases |

### Meetup Groups — Tech (11 groups)
| Group | Events | Category |
|-------|--------|----------|
| Triangle Python Users (TriPython) | 0 | Python |
| PyData Triangle | 0 | Data science |
| Research Triangle Analysts | 0 | Data/analytics |
| Triangle AI Meetup | 1 | AI/ML |
| Triangle Developers | 0 | General dev |
| All Things Open RTP | 0 | Open source |
| Triangle TechBreakfast | 0 | Tech networking |
| Future of Data Triangle | 0 | Data engineering |
| Blacks in Tech RDU | 0 | Diversity in tech |
| Downtown Techies Durham | 0 | Tech social |
| Raleigh WordPress Meetup | 0 | WordPress |

### Meetup Groups — Social/Outdoors (6 groups)
| Group | Events | Category |
|-------|--------|----------|
| Triangle Hiking and Outdoors | 3 | Hiking |
| Durham Geeks | 0 | Geek social |
| Durham Board Games | 0 | Board games |
| CHAD (Chapel Hill and Durham Fun) | 10 | Social activities |
| Discover Durham Together | 0 | Social/exploration |
| ChickTech RDU | 0 | Women in tech |

---

## Scraper Candidates (no ICS feed, would need scraping)

| Source | URL | Platform | Notes |
|--------|-----|----------|-------|
| Durham Chamber of Commerce | members.durhamchamber.org/api/events | GrowthZone Hub XML API | ~8 events; needs growthzone.py scraper |
| Wake Forest Chamber | chambermaster.wakeforestchamber.org/api/events | GrowthZone Hub XML API | ~102 events; needs growthzone.py scraper |
| Apex Chamber | business.apexchamber.com/api/events | GrowthZone Hub XML API | ~132 events; needs growthzone.py scraper |
| DPAC | dpacnc.com/events/all | Custom/Ticketmaster | Major performing arts center |
| Carolina Theatre (Durham) | carolinatheatre.org/events/ | WordPress + Agile Ticketing | Film, music, comedy |
| Cat's Cradle / Motorco / Lincoln Theatre | catscradle.com/events/ | WordPress + ETIX | Major indie music venues |
| The Pour House (Raleigh) | pourhouseraleigh.com | Squarespace-like | Music venue |
| Haw River Ballroom | hawriverballroom.com/calendar | Squarespace | Music venue — candidate for squarespace.py scraper |
| Carolina Performing Arts (UNC) | carolinaperformingarts.org/calendar/ | WordPress + Ticketmaster | Memorial Hall performances |
| Duke Performances | arts.duke.edu/events/ | WordPress (FacetWP) | Duke arts events |
| NC Museum of Art | ncartmuseum.org/events-and-exhibitions/ | WordPress (MEC) | No public ICS from MEC |
| NC Museum of History | ncmuseumofhistory.org/events | Drupal | No ICS feed |
| Raleigh Little Theatre | raleighlittletheatre.org/shows-and-events/ | WordPress + Salesforce | Community theatre |
| Durham Arts Council | durhamarts.org/dac-art-events/ | WordPress (custom) | Arts events and grants |
| American Tobacco Campus | americantobacco.co/events/ | WordPress (Events Manager) | No ICS exposed |
| INDY Week Calendar | calendar.indyweek.com | Custom | Alt-weekly community calendar |
| Triangle on the Cheap | triangleonthecheap.com/events/ | WordPress (custom) | Free/cheap event aggregator |
| Sarah P. Duke Gardens | gardens.duke.edu/calendar/ | WordPress (Tribe?) | May have ICS — needs testing |

---

## Non-Starters

| Source | Reason |
|--------|--------|
| City of Raleigh (raleighnc.gov/events) | Drupal, no ICS feeds |
| Raleigh Legistar API | raleigh.legistar.com web UI exists but API returns "LegistarConnectionString not set up" — uses Granicus backend |
| PNC Arena | Custom + Ticketmaster, no public feeds |
| Red Hat Amphitheater | Custom, no feeds |
| NC Museum of Natural Sciences ICS | Returns valid ICS structure but 0 events |
| Quail Ridge Books | Custom bookstore platform, no feeds |
| Eno River Association | WordPress Simple Calendar plugin, no ICS export |
| Raleigh Chamber | Atlas SPA (web.raleighchamber.org), no server-side API |
| Cary Chamber | Atlas SPA (web.carychamber.com), no server-side API |
| Chapel Hill-Carrboro Chamber | GrowthZone MicroNet CMS, no XML API endpoint |
| Triangle on the Cheap ICS | `?ical=1` returns HTML, not ICS — Tribe Events export disabled |
| Downtown Cary | Mod_Security blocks automated requests |
| Durham Convention Center | Mod_Security blocks automated requests |
| LiveWhale feeds | No LiveWhale instances found in NC |
| MembershipWorks | No MembershipWorks orgs found in RDU area |

---

## Research Log

### 2026-02-15: Initial research + feed discovery

**Discovery methods used:**
- Web search for Triangle-area Localist, WordPress Tribe, Tockify, LibCal platforms
- Direct `?ical=1` probing on venue/org sites
- Meetup group discovery across tech, social, outdoors categories
- Localist university calendar testing (UNC, Duke, NC State)
- CivicPlus iCalendar testing for City of Durham

**Key finds:**
- **NC State** Localist calendar: ~1,297 events — biggest university source
- **DNCR** Localist calendar: ~1,537 events — aggregates multiple state museums
- **Durham County Library** LibCal: ~500 events
- **UNC Chapel Hill** Localist: ~461 events
- **Ackland Art Museum** and **Nasher Museum**: 30 events each via WordPress Tribe
- No Tockify calendars found for the Triangle area
- **17 Meetup groups** across tech and social categories

**Total: 28 sources, ~3,900+ events**

### 2026-02-15: Legistar government sources
- Tested Legistar WebAPI for Triangle governments
- **Working**: `wake` (Wake County), `chapelhill` (Town of Chapel Hill), `durhamcounty` (Durham County)
- **Broken**: `raleigh` — web UI exists at raleigh.legistar.com but API returns "LegistarConnectionString setting is not set up in InSite for client: raleigh" (uses Granicus, not Legistar API)
- Fixed legistar.py scraper to use curl subprocess (avoids Python urllib encoding `$` as `%24`)
- **Total: 31 sources**

### 2026-02-15: Phase 1 platform searches (continued)
- **Google Calendar embeds**: Checked 20+ Triangle-area organizations for embedded Google Calendars. Found 3 usable community feeds: Bike Durham Events (101 events), Triangle Cycling (1,925 events), Gizmo Brew Works Durham (128 events). Also found UNC CS and Raleigh Charter HS calendars — skipped as too niche.
- **GrowthZone/Chamber of Commerce**: Surveyed 6 area chambers. Three have usable XML APIs at `/api/events` (Durham, Wake Forest, Apex) returning `ArrayOfEventDisplay` XML. Three are dead ends: Raleigh and Cary use Atlas SPA, Chapel Hill uses MicroNet CMS. None offer bulk ICS feeds — all need a growthzone.py scraper.
- **LiveWhale**: Zero hits in NC. Platform not used in this region.
- **MembershipWorks**: Zero hits in RDU area.
- **Community calendars/BIDs**: Triangle on the Cheap has Tribe Events but `?ical=1` returns HTML. Downtown Durham uses Tribe Events via Elementor (no ICS). Downtown Cary and Durham Convention Center blocked by Mod_Security.
- **Total: 34 sources** (+3 Google Calendar feeds)

---

## Topical Searches

Track progress on topical searches to find long-tail community sources.

### Not Yet Done

- Food & drink (breweries, farmers markets, food trucks) — **partial**: Gizmo Brew Works added; others TBD
- Music venues (Cat's Cradle, Motorco, Lincoln Theatre, Pour House — all need scrapers)
- Performing arts (DPAC, Carolina Performing Arts, PlayMakers)
- Faith / spiritual
- Seniors
- Literary (readings, poetry — Quail Ridge Books, Flyleaf Books, Letters Bookshop)
- LGBTQ+ community
- Kids / family (libraries, museums, parks)
- Science / research (Duke, UNC, NIEHS, RTI, EPA)
- Outdoor recreation (Eno River, Falls Lake, Umstead State Park, American Tobacco Trail)
- Government / public affairs — Legistar done (wake, chapelhill, durhamcounty); Raleigh API broken
- Volunteering / mutual aid
- Sports / fitness (running clubs, cycling groups) — **partial**: Bike Durham + Triangle Cycling added
