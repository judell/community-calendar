# Toronto Calendar Source Checklist

## Currently Implemented (76 sources)

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

### Outdoor & Nature
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Ontario Nature | WordPress Tribe ICS | 11 | Birding trips, nature talks, conservation |

### Meetup Groups (46 groups)
| Group | Events | Category |
|-------|--------|----------|
| SAI Dham Canada Toronto Volunteer Group | 10 | Volunteering / mutual aid |
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

- **Toronto Public Library** — JSON API at `gateway.bibliocommons.com/v2/libraries/tpl/events` returns ~8,000 items, but these are library programs (book clubs, yoga, tech help). Needs JSON-to-ICS conversion and scoping decision.
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
| Toronto Public Library | No ICS feed (only JSON API via BiblioCommons) |
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
- **44 Meetup groups** with active ICS feeds across social, arts, hiking, cycling, dance, games, books, comedy, tech, language, yoga, water sports, running, film, improv, business, makers, crafts

**Total: 76 sources, ~6,800+ events**

**Infrastructure built:**
- `scrapers/lib/ckan.py` — reusable CKAN datastore API base scraper (pagination, filters)
- `scrapers/toronto_meetings.py` — City of Toronto meetings via CKAN
- `scrapers/toronto_festivals.py` — City of Toronto festivals via CKAN JSON
- `scrapers/uoft_events.py` — UofT aggregate page + 32 department deep-links

**Topical searches completed:** outdoor activities, government/public affairs, crafts/makers

### 2026-02-15: Topical pass 1 — volunteering / mutual aid

**Added this session**
- **Show Up Toronto** — iCal feed at `https://showuptoronto.ca/static/showupto.ics` (site also exposes RSS). Added to `feeds.txt`, workflow fetch, and `combine_ics.py` source mappings.
- **Meetup: SAI Dham Canada Toronto Volunteer Group** — iCal feed at `https://www.meetup.com/sai-dham-canada-toronto-volunteer-group/events/ical/`. Added to `feeds.txt`, workflow fetch, and `combine_ics.py` source mappings.
- **Volunteer Toronto scraper** — added `scrapers/volunteer_toronto.py` and wired workflow output `volunteer_toronto.ics` plus `combine_ics.py` source mappings. Needs runtime validation for event volume.

**Screened out for now (not Toronto-specific enough)**
- **Volunteer MBC** (`https://www.volunteermbc.org/events/?ical=1`) — valid ICS, but appears regional beyond Toronto.
- **VolunteerConnector** (`https://www.volunteerconnector.org/events?ical=1`) — valid ICS, but Ontario-wide feed likely too broad without city filtering.

**Topical searches not yet done:**
- Food & drink (cooking classes, tastings, farmers markets)
- Faith / spiritual
- Kids / family
- Seniors
- Literary (readings, poetry, writing workshops)
- Science / education (lectures, astronomy clubs)
- LGBTQ+ community
- Comedy (standup, open mics)
- Music participation (choirs, jam sessions, open mics)
- Gardening / urban farming

---

## Topical Search: History / Heritage (2025-02-15)

**Objective**: Find long-tail events in history/heritage category

### Working ICS Feeds (Added to feeds.txt)

| Source | ICS URL | Events | Notes |
|--------|---------|--------|-------|
| Ontario Historical Society | `ontariohistoricalsociety.ca/events/?ical=1` | 5 | WordPress Tribe; province-wide but includes Toronto events like Toronto Postcard Club (Feb 22), Canada Black Music Archives (Feb 18) |
| Toronto History Walks | `meetup.com/the-history-of-parkdale/events/ical/` | 10 | Walking tours: U of T & Yorkville, Mt Pleasant Cemetery, St James Cemetery, Distillery District, Lakeshore Psychiatric Hospital, PATH System, Little India |
| Medieval Renaissance Toronto SCA | `meetup.com/Medieval-Renaissance-Toronto-Royal-Citie-of-Eoforwic-SCA/events/ical/` | 10 | Society for Creative Anachronism - medieval arts, science, dancing, games |

### Meetup Groups Discovered (History/Heritage)

| Group | Members | ICS Events | Status |
|-------|---------|------------|--------|
| Toronto History Walks (the-history-of-parkdale) | 8,781 | 10 | ✅ Added - excellent walking tours |
| Medieval Renaissance Toronto SCA | 172 | 10 | ✅ Added - medieval reenactment |
| Eglinton History Salon | 266 | 0 | No current events |
| History Discussion Group | 3,586 | 0 | No current events |
| The Long Conversation | 16 | 0 | Philosophy/history discussion |
| Toronto African Diaspora History Walking Tours | 63 | 0 | No current events |
| Hidden History Toronto! Walking Tours | 9,597 | 0 | No current events |

### Key Organizations Assessed

| Organization | URL | Feed Status | Notes |
|--------------|-----|-------------|-------|
| Ontario Historical Society | ontariohistoricalsociety.ca | ✅ ICS works | Province-wide heritage org |
| Heritage Toronto | heritagetoronto.org | No feed | Tours seasonal (June-Nov), next season late spring 2026 |
| ACO Toronto | acotoronto.ca | No feed | Annual symposiums, static page |
| Toronto Historical Association | torontohistory.net | Inactive | Last events from 2016 |
| City of Toronto History Museums | toronto.ca | No feed | 61 events but WordPress, no ICS |
| Toronto Family History (OGS) | torontofamilyhistory.org | Blocked | Cloudflare protected |

### Historic Sites / Museums

| Venue | URL | Feed Status | Notes |
|-------|-----|-------------|-------|
| Casa Loma | casaloma.ca | No feed | RSS from 2018, empty; static events page |
| Fort York | fortyork.streamintickets.com | 404 | Ticketing system down |
| City of Toronto Archives | toronto.ca/archives | No feed | Static events page |
| Doors Open Toronto | toronto.ca/doors-open | Scheduled | May 23-24, 2026 - 150+ sites |

### Sample Events from Toronto History Walks

- University of Toronto and Historic Yorkville!
- Mount Pleasant Cemetery (WEEKDAY)
- St. James Cemetery and Castle Frank
- Alcohol Wars: The Distillery and the Brewery District (EVENING)
- With Strength: Toronto Women on the Edge of History!
- The Mystery of Alfreda Mae Hillier: Interactive Game and Tour
- Historic Little India: Gerrard India Bazaar
- The Massey Murder: Interactive Game and Tour
- The PATH System: Specialist Course and Guide
- The Lakeshore Psychiatric Hospital and Camp M

### Non-Starters (History/Heritage)

| Source | Reason |
|--------|--------|
| Toronto Historical Association | Site inactive since 2016 |
| Toronto Family History | Cloudflare protected |
| Casa Loma | Static site, RSS empty since 2018 |
| Fort York tickets | 404 error on events page |
| Heritage Toronto tours | Seasonal only (June-Nov) |
