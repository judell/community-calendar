# Raleigh-Durham (Research Triangle) Calendar Source Checklist

## Currently Implemented (44 sources)

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
| Sarah P. Duke Gardens | WordPress Tribe ICS | ~30 | Duke campus |
| NC Museum of Natural Sciences | WordPress Tribe ICS | ~30 | Raleigh; campfire art, nature detectives, etc. |

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

### Chambers of Commerce (GrowthZone scraped)
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Durham Chamber of Commerce | GrowthZone scraper | ~5 | Annual meeting, orientations |
| Wake Forest Chamber | GrowthZone scraper | ~47 | Business events, networking |
| Apex Chamber | GrowthZone scraper | ~49 | Business events, mixers |

### Community & Civic
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Raleigh & Triangle Activities | Meetup ICS | ~10 | Newcomer/social group |
| Transitions LifeCare | WordPress Tribe ICS | ~7 | Caregiver support events |
| NC Wildlife Federation | WordPress Tribe ICS | ~22 | Statewide conservation; needs geo-filter |
| Code with the Carolinas | Meetup ICS | ~10 | Civic tech (Code for America brigade) |
| Resilient Durham NC | WordPress Tribe ICS | ~4 | Community resilience, wellness |
| SW Durham Rotary Club | Google Calendar ICS | ~628 | Speaker series, volunteer events, socials |

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
| ~~Durham Chamber~~ | ~~GrowthZone~~ | ~~Implemented~~ | Moved to Implemented |
| ~~Wake Forest Chamber~~ | ~~GrowthZone~~ | ~~Implemented~~ | Moved to Implemented |
| ~~Apex Chamber~~ | ~~GrowthZone~~ | ~~Implemented~~ | Moved to Implemented |
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
| Ponysaurus Brewing | ponysaurusbrewing.com/events | Squarespace | ~15-20 events/mo; `?format=json` scrapable |
| Fullsteam Brewery | fullsteam.ag/tavern/events | Craft CMS | Trivia, live music; no ICS |
| The Scrap Exchange | scrapexchange.org/tsecalendar | Squarespace | ~10 events/mo; `?format=json` scrapable |
| Museum of Life and Science | lifeandscience.org/explore/events/ | WordPress (Formidable Forms) | No Tribe ICS |
| NC Museum of Natural Sciences exhibits | naturalsciences.org/calendar/ | WordPress | Per-event iCal export only; main ICS already captured |
| Carolina Theatre (Durham) | carolinatheatre.org/events/ | WordPress (no Tribe) | Film, live performances; no ICS |
| Motorco Music Hall | motorcomusic.com/calendar/ | WordPress (Astra) | ~15-20 events/mo; no Tribe ICS |
| Cat's Cradle (Carrboro) | catscradle.com/events/ | WordPress | ~20-30 events/mo; no ICS |
| Boxyard RTP | boxyard.rtp.org/calendar/ | Custom | Per-event iCal export only |
| Durham Parks & Recreation | dprplaymore.org/Calendar.aspx | CivicEngage | May have iCal subscription |
| Durham Resistance Hub | durhamresistance.com/calendar | Squarespace | Aggregated activism calendar; `?format=json` possible |
| Durham People's Alliance | durhampa.org/calendar | NationBuilder | Progressive politics; NationBuilder API available |
| Ellerbee Creek Watershed | ellerbecreek.org | Squarespace | Conservation volunteer events |
| Keep Durham Beautiful | keepdurhambeautiful.org/events | Squarespace | Cleanups, volunteer workdays |
| Haw River Assembly | hawriver.org/events | Squarespace | Western Triangle conservation |
| ~~Sarah P. Duke Gardens~~ | ~~WordPress Tribe~~ | ~~Implemented~~ | Moved to Implemented |

---

## Non-Starters

| Source | Reason |
|--------|--------|
| City of Raleigh (raleighnc.gov/events) | Drupal, no ICS feeds |
| Raleigh Legistar API | raleigh.legistar.com web UI exists but API returns "LegistarConnectionString not set up" — uses Granicus backend |
| PNC Arena | Custom + Ticketmaster, no public feeds |
| Red Hat Amphitheater | Custom, no feeds |
| ~~NC Museum of Natural Sciences~~ | Now returns 30 events — moved to Implemented |
| Quail Ridge Books | Custom bookstore platform, no feeds |
| Eno River Association | WordPress Simple Calendar plugin embeds Google Calendar; underlying gcal ID unknown |
| Raleigh Chamber | Atlas SPA (web.raleighchamber.org), no server-side API |
| Cary Chamber | Atlas SPA (web.carychamber.com), no server-side API |
| Chapel Hill-Carrboro Chamber | GrowthZone MicroNet CMS, no XML API endpoint |
| Triangle on the Cheap ICS | `?ical=1` returns HTML, not ICS — Tribe Events export disabled |
| Downtown Cary | Mod_Security blocks automated requests |
| Durham Convention Center | Mod_Security blocks automated requests |
| LiveWhale feeds | No LiveWhale instances found in NC |
| MembershipWorks | No MembershipWorks orgs found in RDU area |
| Dementia Alliance NC | WordPress, `?ical=1` returns HTML |
| ACLU of NC | WordPress, no Tribe Events, `?ical=1` returns HTML |
| Emancipate NC | WordPress Divi, no Tribe Events |
| League of Women Voters ODC | MyLO platform, no ICS export |
| Activate Good / Triangle Do-Gooders | WordPress, Meetup ICS returns 403 |
| NC Native Plant Society | WordPress MEC, `?mec-ical-feed=1` returns HTML |
| Newcomers clubs (Raleigh/Cary/Chapel Hill) | Member-gated, no public calendars |
| Wake Audubon | WordPress + Google Calendar embed; gcal ID not yet extracted |
| New Hope Bird Alliance | WordPress + Google Calendar embed; gcal ID not yet extracted |

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

### 2026-02-15: Phase 2 topical searches + new feeds
- **Sarah P. Duke Gardens**: `gardens.duke.edu/calendar/?ical=1` — WordPress Tribe, 30 events. Added.
- **NC Museum of Natural Sciences**: `naturalsciences.org/calendar/events/?ical=1` — WordPress Tribe (ECP v5.9.0), 30 events. Previously listed as Non-Starter (was returning 0 events). Now working. Added.
- **GrowthZone chambers**: Ran growthzone.py scraper for Durham (5 events), Wake Forest (47), Apex (49). Added.
- **Topical searches completed**: Music, performing arts, food & drink, kids/family, science, outdoor recreation, faith, seniors, literary, LGBTQ+, volunteering, sports/fitness. Most categories yielded no ICS feeds — venues use WordPress without Tribe, Squarespace, or custom platforms.
- **Total: 38 sources, ~4,000+ events**

### 2026-02-15: Continued topical searches (outdoors, community, civic)
- **NC Wildlife Federation**: `ncwf.org/events/?ical=1` — WordPress Tribe (ECP v6.15.14), 22 events. Statewide, needs geo-filter. Added.
- **Transitions LifeCare**: `transitionslifecare.org/events/?ical=1` — WordPress Tribe (ECP v6.15.15), 7 events. Caregiver support. Added.
- **Resilient Durham NC**: `resilientdurhamnc.org/events/?ical=1` — WordPress Tribe (ECP v6.15.16), 4 events. Added.
- **SW Durham Rotary**: Google Calendar ICS, 628 events (speaker series, volunteer events, socials). Added.
- **Raleigh Triangle Activities Meetup**: 10 events. Newcomer/social group. Added.
- **Code with the Carolinas Meetup**: 10 events. Civic tech (Code for America). Added.
- **Meetup ICS feeds verified working** — agent reported 404s but manual testing confirms all returning 200 with valid ICS.
- **Google Calendar embeds found** at Wake Audubon, New Hope Bird Alliance, Eno River Assn — calendar IDs not yet extracted.
- **Total: 44 sources, ~4,700+ events**

---

## Topical Searches

Track progress on topical searches to find long-tail community sources.

### Completed

- Music venues — All top venues (Cat's Cradle, Motorco, Haw River Ballroom, Pour House, DPAC) tested; none have ICS feeds. All need scrapers.
- Performing arts — Carolina Performing Arts, PlayMakers, Raleigh Little Theatre, Duke Performances: no ICS. DPAC: Ticketmaster only.
- Food & drink — Gizmo Brew Works (Google Calendar, implemented). Ponysaurus + Fullsteam tested; Squarespace/Craft CMS, no ICS. Durham Food Hall `?ical=1` returns HTML.
- Kids / family — Museum of Life and Science (WordPress, no Tribe ICS). Marbles, Kidzu: no ICS. Scrap Exchange: Squarespace.
- Science / research — NIEHS, RTI: no public ICS. DNCR feed already covers state museums. NC Natural Sciences now implemented.
- Outdoor recreation — Eno River Assn: Google Calendar embedded but ID unknown. DNCR covers state parks. Triangle Land Conservancy already implemented. NC Wildlife Federation: ICS works, 22 events (statewide). Walking/hiking Meetup groups found but all are Meetup-only (no separate ICS). Birding: Wake Audubon and New Hope Bird Alliance both embed Google Calendars (IDs not yet extracted).
- Conservation — Ellerbee Creek, Keep Durham Beautiful, Haw River Assembly: all Squarespace, no ICS. NC Native Plant Society: WordPress MEC, feed returns HTML.
- Faith / spiritual — No ICS feeds found for Triangle-area faith orgs.
- Seniors — No dedicated senior event ICS feeds found. Transitions LifeCare (caregiver support): ICS works, 7 events.
- Literary — Quail Ridge Books, Flyleaf Books, Letters Bookshop: no ICS feeds. Poetry Meetup groups not found on Meetup.
- LGBTQ+ — LGBTQ Center of Durham: WordPress, `?ical=1` returns HTML.
- Volunteering / mutual aid — Hands On Triangle, Habitat Durham: no ICS feeds. Activate Good Meetup returns 403.
- Civic engagement — Resilient Durham NC: ICS works, 4 events. Code with the Carolinas Meetup: 10 events. SW Durham Rotary Google Calendar: 628 events. Durham People's Alliance + Durham CAN: NationBuilder, no public ICS. Durham Resistance Hub: Squarespace.
- Community / newcomers — Raleigh Triangle Activities Meetup: 10 events. Newcomers clubs (Raleigh/Cary/Chapel Hill): all member-gated.
- Sports / fitness — Bike Durham + Triangle Cycling (implemented). NC Roadrunners Meetup: valid ICS but currently 0 events.
- Government / public affairs — Legistar done (wake, chapelhill, durhamcounty); Raleigh API broken.

### Not Yet Done

- Google Calendar ID extraction — Wake Audubon, New Hope Bird Alliance, Eno River Assn all embed Google Calendars. Extracting the calendar IDs from page source would yield free ICS feeds.
- Health & Well-Being — yoga, fitness, mindfulness, wellness: not yet searched
- Food & Drink — wine, cooking classes: not yet searched
- Animals & Environment — pets, wildlife, animal care, sustainability: not yet searched
- Play & Games — gaming cafes, puzzle groups: not yet searched
- Ideas & Learning — writing groups, genealogy, philosophy: not yet searched
- Technology & Work — digital skills, careers, coworking: not yet searched
