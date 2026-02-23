# Toronto Calendar Source Checklist

## Currently Implemented (83 sources)

### Aggregators
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| NOW Magazine | WordPress Tribe ICS | ~30 | Arts, music, comedy, cultural events |
| Toronto Events (torevent) | Tockify ICS | ~2,899 | Music, comedy, film, nightlife — biggest source |

### Venues & Institutions
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Union Station | WordPress Tribe ICS | 18 | Art installations, music |
| Distillery District | Tockify ICS | 5 | Iconic venue programming |
| Gardiner Museum | WordPress Tribe ICS | 30 | Ceramics museum |
| Toronto Botanical Garden | WordPress Tribe ICS | 30 | Garden/nature programs |
| Textile Museum of Canada | WordPress Tribe ICS | 9 | |
| Bata Shoe Museum | WordPress Tribe ICS | 5 | |
| Buddies in Bad Times Theatre | WordPress Tribe ICS | 4 | LGBTQ+ theatre |
| Factory Theatre | WordPress Tribe ICS | 9 | Canadian theatre |
| High Park Nature Centre | WordPress Tribe ICS | 10 | Outdoor/nature programs |

### Universities
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| University of Toronto | HTML scraper | 176 | Aggregate page + 32 department deep-links |
| UofT Engineering | WordPress Tribe ICS | 17 | |
| UofT Philosophy | WordPress Tribe ICS | 7 | |
| UofT Social Work | WordPress Tribe ICS | 4 | |
| York University | WordPress MEC ICS | 6,558 | Huge feed, pipeline filters by date |

### Music Venues
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Jazz Bistro | WordPress Tribe ICS | 24 | Live jazz performances |
| Grossman's Tavern | WordPress Tribe ICS | 30 | Live music |

### Community Organizations
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| CultureLink | WordPress Events Manager ICS | 494 | Newcomer/community events |
| Scadding Court Community Centre | WordPress Tribe ICS | 30 | |
| St. Lawrence Neighbourhood Assoc. | Tockify ICS | 82 | Community meetings, markets, kids |
| Bloor West Village BIA | WordPress Tribe ICS | 6 | |
| Councillor Jamaal Myers | Tockify ICS | 27 | Scarborough community, city council |
| Show Up Toronto | iCal feed | TBD | Volunteering, mutual aid, civic organizing |
| Volunteer Toronto | HTML scraper | TBD | Volunteering opportunities and events |
| Toronto Public Library | Bibliocommons scraper | 2,438 | Kids/family scoped (school-age + teens), reusable base |

### Crafts & Makers
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Repair Cafe Toronto | WordPress ICS | 82 | Community repair workshops across GTA |
| Toronto Knitters Guild | WordPress Tribe ICS | 9 | Guild meetings, knit nights, workshops |
| Site 3 CoLaboratory | WordPress Tribe ICS | 1 | Art/tech makerspace workshops |

### Government & Public Affairs
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| City of Toronto Meetings | CKAN JSON scraper | 162 | Council, community councils, 56 committees |
| City of Toronto Festivals & Events | CKAN JSON scraper | 2,101 | Official city festival/event data, 37 categories |

### Science & Education
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| CITA Local Events | Public Google ICS | 339 | CITA/UofT science talks and local events |
| CITA Seminars | Public Google ICS | 1,089 | CITA seminar series (pipeline date filters apply) |
| CITA Special Events | Public Google ICS | 175 | CITA special event calendar |

### Outdoor & Nature
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Ontario Nature | WordPress Tribe ICS | 11 | Birding trips, nature talks, conservation |

### Meetup Groups (49 groups)
| Group | Events | Category |
|-------|--------|----------|
| SAI Dham Canada Toronto Volunteer Group | 10 | Volunteering / mutual aid |
| Toronto Dads Group | 10 | Kids / family |
| Little Sunbeams (Parents + Tots) | 10 | Kids / family |
| Mini + Me Meetups | 10 | Kids / family |
| TorontoBabel | 10 | Language exchange |
| Try New Things in Toronto | 10 | Social/activities |
| Toronto Arts & Culture | 10 | Arts outings |
| These Boots Are Made for Hiking | 5 | Hiking |
| Toronto Bike Meetup | 10 | Cycling |
| Board Games and Social | 10 | Board games |
| Salsa/Bachata/Kizomba GTA | 10 | Dance |
| Toronto Photography Group | 3 | Photography |
| A Book Club Downtown | 4 | Book club |
| Improv, Acting, Nature Walks | 4 | Comedy/improv |
| TechTO | 2 | Tech |
| Toronto JavaScript | 1 | Tech |
| Python Toronto | 1 | Tech |
| Founders Running Club Toronto | 10 | Running |
| High Park Yoga | 10 | Outdoor yoga |
| Mindful Movement Toronto | 10 | Outdoor yoga/wellness |
| Toronto Wellness | 10 | Yoga, meditation, wellness |
| Toronto SUP, Kayak & Canoe | seasonal | Water sports |
| Toronto Paddlers | seasonal | Waterfront kayaking |
| Toronto Canoe Trippers | seasonal | Canoe expeditions |
| 20s 30s Toronto Social | 10 | Social |
| Soul City Social Club | 10 | Social |
| Experience Toronto | 7 | Arts/culture |
| Hiking Network | 3 | Hiking |
| GTA Hiking & Stuff | 1 | Hiking |
| Toronto Bruce Trail Club | 1 | Hiking |
| Wilderness Union | 2 | Outdoors |
| Toronto Heavy Boardgamers | 10 | Board games |
| Toronto Movies & Social | 10 | Film |
| Sci Fi Book Club | 6 | Book club |
| Post-Apocalyptic Book Club | 2 | Book club |
| Silent Book Club | 1 | Book club |
| Toronto Japanese English Exchange | 10 | Language |
| Language Exchange Toronto | 10 | Language |
| TILE Language Party | 5 | Language |
| Improv For New Friends | 2 | Improv |
| Toronto AI & ML | 10 | Tech |
| Microsoft Reactor Toronto | 10 | Tech |
| Toronto Tech Stack Exchange | 10 | Tech |
| Toronto Enterprise DevOps | 3 | Tech |
| Toronto Postgres | 2 | Tech |
| Toronto Women in Business | 2 | Business |
| Toronto 20s-50s Singles Social | 2 | Social |
| Toronto 3D Printing | 10 | Makers/3D printing |
| Midtown Arts & Crafts | 1 | General crafts |

## Needs Further Assessment

- **Toronto Public Library** — now implemented as kids/family-scoped scraper (`scrapers/toronto_public_library.py`) on reusable Bibliocommons base (`scrapers/lib/bibliocommons.py`). Monitor ongoing signal/noise and adjust filters if needed.
- **BlogTO** — Highest volume Toronto source (215+ events) but needs custom scraper. JSON embedded in event pages (`var event = {...}`).
- **Explore Kids Ontario Adventures** — Tockify feed (`ekoad`) has 822 events but covers broader GTA/Ontario, not just Toronto. May need geo-filtering.
- **Toronto Bicycling Network** — Wild Apricot RSS at `tbn.ca/events/RSS` has 55 events (hiking, cycling, walks, skating, skiing). Richest outdoor recreation club. Needs RSS-to-ICS conversion.

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Facebook Events | No public API since 2018 |
| Bandsintown | 403 errors, no public feed |
| Destination Toronto | Uses Cruncho widget, no feeds |
| Toronto.com RSS | Rate limited (429) |
| Eventbrite | No public feeds; API requires OAuth key |
| Exclaim! | Events section returns 404 |
| AllEvents.in | No feeds, web-only |
| AGO | Cloudflare protected (403) |
| ROM | 404 on events page |
| TIFF | No ICS/RSS found |
| Mirvish | No feed found |
| Harbourfront Centre | RSS feed exists but empty |
| Massey Hall / Roy Thomson Hall | 404 |
| Canadian Opera Company | 526 error |
| do416.to | No feed |
| To Do Canada | 403 Forbidden |
| Songkick Toronto | No public feeds |
| Dice.fm | No Toronto page |
| Resident Advisor | 403 |
| The Rex | Squarespace but not events collection type |
| Horseshoe Tavern | Webflow, no feed |
| Lee's Palace | Custom app, no feed |
| Danforth Music Hall | Custom Chakra UI app, no feed |
| TSO | No feed found |
| Canadian Stage | No WordPress Tribe ICS |
| Tarragon Theatre | No WordPress Tribe ICS |
| Hot Docs | No WordPress Tribe ICS |
| Aga Khan Museum | No WordPress Tribe ICS |
| Power Plant Gallery | No WordPress Tribe ICS |
| MOCA Toronto | No WordPress Tribe ICS |
| The 519 | WordPress but no Tribe Events plugin |
| Lula Lounge | No feed |
| Tranzac | No feed |
| 918 Bathurst | No feed |
| Luminato Festival | No feed |
| Music Gallery | No feed |
| Small World Music | No feed |
| Scarborough Arts | No feed |
| TMU / OCAD | No ICS feeds (TMU custom CMS, OCAD Drupal) |
| TRCA | Events on Eventbrite only; no ICS/RSS for events |
| Tommy Thompson Park | Links to TRCA calendar; no own event feed |
| Rouge National Urban Park | No calendar; page says "check back soon" |
| Ontario Place | WordPress Tribe installed but ICS returns empty |
| Evergreen Brick Works | WordPress but no Tribe/MEC; no feeds |
| Toronto Outdoor Club | Custom ASP.NET, no feeds |
| Bruce Trail Conservancy (Toronto) | ECWD calendar plugin, no ICS endpoint |
| Toronto Field Naturalists | Members-only content, no public feed |
| Dragon Boat Canada | MEC installed but ICS returns HTML |
| Cycle Toronto | NationBuilder, no feeds |
| Downsview Park | Drupal, no feeds (30+ events but would need scraper) |
| City of Toronto (toronto.ca) | No Legistar; TMMIS behind Akamai WAF (403). Meeting data available via CKAN instead |
| Ontario Legislature | 403 on calendar page; no ICS/RSS |
| Toronto Police Services Board | Joomla, no feeds (~9 meetings/year) |
| TTC Board | Moved to TMMIS; meetings included in CKAN dataset |
| Metrolinx Board | Static HTML listing (~6 meetings/year) |
| TDSB / TCDSB | eScribe platform, no API or feeds; email subscription only |
| Waterfront Toronto | Drupal/FullCalendar, no feeds (~15 meetings/year) |

---

## Research Log

### 2026-02-14: Initial research + full discovery pass

**Discovery methods used:**
- DuckDuckGo platform searches (Tockify, Localist, WordPress Tribe)
- Direct WordPress `?ical=1` probing on Toronto venue/org sites
- Meetup group discovery across 13+ categories
- Aggregator assessment (BlogTO, NOW, City of Toronto, etc.)
- Topical searches: outdoor activities, government/public affairs, crafts/makers
- City of Toronto open data portal (CKAN API)

**Key finds:**
- **torevent** Tockify calendar: ~2,900 Toronto events — single biggest source
- **CultureLink**: 494 community/newcomer events via WordPress Events Manager
- **York University**: 6,558 events via WordPress MEC
- **University of Toronto**: 176 events via custom scraper + 3 department ICS feeds
- **Ontario Nature**: 11 events via WordPress Tribe
- **City of Toronto CKAN**: meeting schedule (162 future meetings) + festivals/events (2,101 future) via new CKAN base scraper
- **Repair Cafe Toronto**: 82 community repair workshops
- **49 Meetup groups** with active ICS feeds across social, arts, hiking, cycling, dance, games, books, comedy, tech, language, yoga, water sports, running, film, improv, business, makers, crafts, and kids/family

**Total: 80 sources, ~9,200+ events**

**Infrastructure built:**
- `scrapers/lib/ckan.py` — reusable CKAN datastore API base scraper (pagination, filters)
- `scrapers/lib/bibliocommons.py` — reusable Bibliocommons events API base scraper (entity mapping + filter hooks)
- `scrapers/toronto_meetings.py` — City of Toronto meetings via CKAN
- `scrapers/toronto_festivals.py` — City of Toronto festivals via CKAN JSON
- `scrapers/uoft_events.py` — UofT aggregate page + 32 department deep-links
- `scrapers/toronto_public_library.py` — TPL kids/family scraper on Bibliocommons base
- `scrapers/toronto_public_library.py` — TPL kids/family scraper on Bibliocommons base

---

## Topical Searches

Track progress on topical searches to find long-tail community sources.

### Completed

| Topic | Date | Sources Added | Notes |
|-------|------|---------------|-------|
| Outdoor activities | 2025-02-14 | (included in initial Meetup sweep) | Hiking, cycling, water sports |
| Government/public affairs | 2025-02-14 | toronto_meetings.py, toronto_festivals.py | CKAN open data |
| Crafts/makers | 2025-02-14 | Repair Cafe, Knitters Guild, Site 3, 3D printing | |
| Volunteering/mutual aid | 2025-02-15 | Show Up Toronto, SAI Dham Volunteer, Volunteer Toronto scraper | |
| Kids/family | 2025-02-15 | Toronto Dads, Little Sunbeams, Mini+Me Meetups, TPL scraper | Bibliocommons base |
| History/heritage | 2025-02-15 | Ontario Historical Society, Toronto History Walks, Medieval SCA | 25 events |
| Science/education | 2026-02-15 | CITA Local Events, CITA Seminars, CITA Special Events | 3 public Google ICS feeds from CITA calendar page |

### Not Yet Done

- Food & drink (cooking classes, tastings, farmers markets)
- Faith / spiritual
- Seniors
- Literary (readings, poetry, writing workshops)
- LGBTQ+ community
- Comedy (standup, open mics)
- Music participation (choirs, jam sessions, open mics)
- Gardening / urban farming

---

## Topical Search: Volunteering / Mutual Aid (2025-02-15)

### Added

| Source | Type | Notes |
|--------|------|-------|
| Show Up Toronto | ICS feed | `showuptoronto.ca/static/showupto.ics` |
| SAI Dham Canada Toronto Volunteer | Meetup ICS | Volunteer group |
| Volunteer Toronto | Scraper | `scrapers/volunteer_toronto.py` |

### Screened Out

| Source | Reason |
|--------|--------|
| Volunteer MBC | Regional beyond Toronto |
| VolunteerConnector | Ontario-wide, too broad |

---

## Topical Search: Kids / Family (2025-02-15)

### Added

| Source | Type | Notes |
|--------|------|-------|
| Toronto Dads Group | Meetup ICS | `meetup.com/torontodadsgroup/events/ical/` |
| Little Sunbeams | Meetup ICS | Parents + Tots meetup |
| Mini + Me Meetups | Meetup ICS | `meetup.com/mini-me-meetups/events/ical/` |
| Toronto Public Library | Scraper | `scrapers/toronto_public_library.py` on Bibliocommons base |

### Promising (Needs Work)

| Source | Notes |
|--------|-------|
| Jane/Finch Centre | Has per-event iCal links, not clean single feed |

### Screened Out

| Source | Reason |
|--------|--------|
| Kids Out and About Toronto | Promotional listing site, not producer-authoritative |

---

## Topical Search: History / Heritage (2025-02-15)

### Added

| Source | ICS URL | Events | Notes |
|--------|---------|--------|-------|
| Ontario Historical Society | `ontariohistoricalsociety.ca/events/?ical=1` | 5 | WordPress Tribe; province-wide, includes Toronto Postcard Club, Canada Black Music Archives |
| Toronto History Walks | `meetup.com/the-history-of-parkdale/events/ical/` | 10 | Walking tours: cemeteries, neighborhoods, interactive games |
| Medieval Renaissance Toronto SCA | `meetup.com/Medieval-Renaissance-Toronto-Royal-Citie-of-Eoforwic-SCA/events/ical/` | 10 | Medieval arts, science, dancing |

### Meetup Groups Assessed

| Group | Members | Events | Status |
|-------|---------|--------|--------|
| Toronto History Walks | 8,781 | 10 | ✅ Added |
| Medieval Renaissance Toronto SCA | 172 | 10 | ✅ Added |
| Hidden History Toronto! Walking Tours | 9,597 | n/a | Feed/group slug now returns 404 `Group not found` (checked 2026-02-15) |
| History Discussion Group | 3,586 | 0 | No current events |
| Eglinton History Salon | 266 | 0 | No current events |
| Toronto African Diaspora History Walking Tours | 63 | 0 | No current events |
| The Long Conversation | 16 | 0 | Philosophy/history |

### Organizations Assessed

| Organization | Feed Status | Notes |
|--------------|-------------|-------|
| Ontario Historical Society | ✅ ICS works | Province-wide heritage org |
| Heritage Toronto | No feed | Tours seasonal (June-Nov) |
| ACO Toronto | No feed | Annual symposiums |
| City of Toronto History Museums | No feed | 61 events on website |
| Toronto Historical Association | Inactive | Last events 2016 |

### Non-Starters

| Source | Reason |
|--------|--------|
| Toronto Family History (OGS) | Cloudflare protected |
| Casa Loma | Static site, RSS empty since 2018 |
| Fort York tickets | 404 error |
| Heritage Toronto tours | Seasonal only (June-Nov) |

---

## Topical Search: Science / Education (2026-02-15)

### Added

| Source | Type | Notes |
|--------|------|-------|
| CITA Local Events | Public Google ICS | `calendar.google.com/.../qfg129sn6k25ah00ioakus0gds.../public/basic.ics` |
| CITA Seminars | Public Google ICS | `calendar.google.com/.../4h7dspldpuviiv4o1slj9o5p5c.../public/basic.ics` |
| CITA Special Events | Public Google ICS | `calendar.google.com/.../d7muv9fjli72io6q1a7hkdpf04.../public/basic.ics` |

### Organizations Assessed

| Organization | Feed Status | Notes |
|--------------|-------------|-------|
| Canadian Institute for Theoretical Astrophysics (CITA) | ✅ 3 ICS feeds | Feed links available on event calendar page |
| RASC Toronto Centre | No feed found | Site does not expose ICS endpoint |
| Ontario Science Centre | No feed found | Event pages, no ICS/RSS endpoint identified |
| UofT Physics | No feed found | No working `?ical=1` endpoint |

### Meetup Groups Assessed

| Group | Events | Status |
|-------|--------|--------|
| Cognitive Toronto | 0 | Valid ICS, no upcoming events |
| Toronto Data Workshop | n/a | 404 `Group not found` |
| RASC Toronto Centre (Meetup slug) | n/a | 404 `Group not found` |

---

## Topical Search: Broad Web Scan (2026-02-23)

### New ICS Feeds Found

| Source | ICS URL | Events | Notes |
|--------|---------|--------|-------|
| Sunshine Centres for Seniors | `sunshinecentres.com/events/?ical=1` | 15 | Senior programs across multiple Toronto locations |
| GO Latin Dance | `golatindance.com/events/?ical=1` | 30 | Salsa, bachata, kizomba events (Dovercourt House) |
| Boulderz Climbing | `boulderzclimbing.com/events/?ical=1` | 6 | Climbing gym events |
| Toronto Dance | `torontodance.com/events/?ical=1` | ~68 (2025-26) | Dance community aggregator (large historical archive) |
| Toronto Choir | `torontochoir.org/events/?ical=1` | 1 | Community choir (small feed) |

### RSS Feeds (needs RSS-to-ICS conversion)

| Source | RSS URL | Events | Notes |
|--------|---------|--------|-------|
| Toronto Bicycling Network | `tbn.ca/events/RSS` | 50+ | Wild Apricot RSS; hiking, cycling, walks, skating, skiing. Previously identified in Needs Further Assessment, now confirmed 50+ events. |

### Promising Scraping Opportunities

| Source | URL | Notes |
|--------|-----|-------|
| YOHOMO | `yohomo.ca/events` | LGBTQ+ events aggregator - calendar page, would need scraper |
| Harbourfront Centre | `harbourfrontcentre.com/whats-on/` | Major venue, WP Engine site, likely has JSON API |
| Toronto Zoo Events | `torontozoo.com/events/` | Custom site, would need scraper |
| ROM Events | `rom.on.ca/whats-on/events` | Drupal site, may have JSON endpoint |
| Toronto Arts Council | `torontoartscouncil.org/events/` | WordPress, grant deadlines and arts events |
| Centre for Social Innovation | `socialinnovation.org/where-change-happens/events/` | Community/coworking/social enterprise events |
| TRCA Events | `trca.ca/events-calendar/` | Conservation authority nature events |
| The 519 | `the519.org/events/` | LGBTQ+ community centre (already in Non-Starters but worth re-checking) |

### Assessed - Non-Starters

| Source | Reason |
|--------|--------|
| Toronto Junction BIA | WordPress but not Tribe calendar plugin |
| Chinatown BIA | 404 on ICS endpoint |
| Toronto Dance Salsa | Cloudflare protected (403) |
| Jazz Near You Toronto | 403 Forbidden |
| 365 Etobicoke | WordPress but no ICS |
| Toronto Shambhala Meditation | Cloudflare challenge |
| Toronto Running Club | Custom site, 404 on events |
| Amadeus Choir | WordPress but no ICS |
| Annex Singers | 404 on ICS |
| Echo Women's Choir | 404 on ICS |
| Fire Mics (open mics) | Custom site, no ICS |
| Archdiocese of Toronto | 404 on ICS |
| Diocese of Toronto (Anglican) | HTML only |
| MCC Toronto | HTML only |
| Toronto Mass Choir | HTML only |
| Toronto Urban Growers | 404 on ICS |
| Museum of Toronto | HTML only |
| TRSL (Rec Sports) | 404 on events |
| XTSC | 404 on events |
| Community Living Toronto | HTML only |
| The Disability Collective | Wix site |

### Categories Explored

- Seniors (✅ Sunshine Centres)
- LGBTQ+ (scraper opportunity: YOHOMO, The 519)
- Dance (✅ GO Latin Dance, Toronto Dance)
- Climbing/Outdoor (✅ Boulderz)
- Cycling (RSS: TBN)
- Faith/Spiritual (no good feeds found)
- Music/Choir (small: Toronto Choir)
- Food & Drink (no feeds found - mostly Eventbrite)
- Comedy/Open Mic (no feeds found - mostly Facebook/Eventbrite)
- Gardening/Urban Farming (no feeds found)
- Literary/Poetry (no feeds found)
- Startup/Tech (mostly Meetup already covered)
- Museums (scraper opportunities: ROM, Toronto Zoo)
