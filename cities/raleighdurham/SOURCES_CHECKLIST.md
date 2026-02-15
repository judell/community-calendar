# Raleigh-Durham (Research Triangle) Calendar Source Checklist

## Currently Implemented (28 sources)

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
| PNC Arena | Custom + Ticketmaster, no public feeds |
| Red Hat Amphitheater | Custom, no feeds |
| NC Museum of Natural Sciences ICS | Returns valid ICS structure but 0 events |
| Quail Ridge Books | Custom bookstore platform, no feeds |
| Eno River Association | WordPress Simple Calendar plugin, no ICS export |

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

---

## Topical Searches

Track progress on topical searches to find long-tail community sources.

### Not Yet Done

- Food & drink (breweries, farmers markets, food trucks)
- Music venues (Cat's Cradle, Motorco, Lincoln Theatre, Pour House — all need scrapers)
- Performing arts (DPAC, Carolina Performing Arts, PlayMakers)
- Faith / spiritual
- Seniors
- Literary (readings, poetry — Quail Ridge Books, Flyleaf Books, Letters Bookshop)
- LGBTQ+ community
- Kids / family (libraries, museums, parks)
- Science / research (Duke, UNC, NIEHS, RTI, EPA)
- Outdoor recreation (Eno River, Falls Lake, Umstead State Park, American Tobacco Trail)
- Government / public affairs (Town of Chapel Hill, Wake County, Durham County)
- Volunteering / mutual aid
- Sports / fitness (running clubs, cycling groups)
