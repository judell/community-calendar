# Toronto Calendar Source Checklist

## Currently Implemented (115 sources)

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

### Ticketmaster Venues (via Discovery API)
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Scotiabank Arena | Ticketmaster scraper | ~631 | Raptors, Leafs, concerts |
| History | Ticketmaster scraper | ~127 | Music venue |
| Danforth Music Hall | Ticketmaster scraper | ~68 | Indie/rock concerts |
| Lee's Palace | Ticketmaster scraper | ~49 | Indie music |
| Massey Hall | Ticketmaster scraper | ~38 | Iconic concert hall |
| Horseshoe Tavern | Ticketmaster scraper | ~19 | Legendary music venue |
| Queen Elizabeth Theatre | Ticketmaster scraper | ~11 | Performing arts |
| Roy Thomson Hall | Ticketmaster scraper | ~8 | TSO home venue |

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

### Literary & Bookstores
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Another Story Bookshop | Eventbrite organizer (eb-to-ical) | 16 upcoming | Roncesvalles social-justice/diversity focus; very active |
| Ben McNally Books | Eventbrite organizer (eb-to-ical) | active | Downtown indie; Fresh Off The Press book club + open mic + launches |
| Glad Day Bookshop | Eventbrite organizer (eb-to-ical) | active | World's oldest LGBTQ+ bookstore; drag brunches, readings, fundraisers |
| Hopeless Romantic Books | Eventbrite organizer (eb-to-ical) | active | Romance specialty; monthly hybrid book club |
| Queen Books | Eventbrite organizer (eb-to-ical) | currently dormant | Leslieville general indie; live source is Bookmanager scraper below |
| Book*hug Press | Eventbrite (filtered) | 7 | Literary press; launches across Toronto venues |
| Coach House Books | Eventbrite (filtered) | 63 | Literary press (60 yrs); launches at Society Clubhouse |
| Cormorant Books | Eventbrite (filtered) | 31 | Literary press; events at Ben McNally, Sleuth, etc. |
| Penguin Random House Canada | Eventbrite (filtered) | 70 | Big-five Canadian arm |
| HarperCollins Canada | Eventbrite (filtered) | 37 | Big-five publisher |
| Simon & Schuster Canada | Eventbrite (filtered) | 13 | Big-five publisher |
| Diaspora Dialogues | Eventbrite (filtered) | 113 | Toronto literary org; reading series, mentorship |
| House of Anansi | Eventbrite (filtered) | 5 | Toronto literary press; Poetry Bash series at Henderson Brewing |
| Bakka Phoenix Books | Bookmanager scraper | 1 | SF/F specialty (since 1972); `scrapers/bookmanager.py --san 1684035` |
| Flying Books | Bookmanager scraper | 12 | College St + Neverland; biggest Bookmanager haul; book clubs + launches |
| Ben McNally Books (Bookmanager) | Bookmanager scraper | 9 | Complements Eventbrite feed: BMB Book Club + publisher launches |
| Queen Books (Bookmanager) | Bookmanager scraper | 8 | Currently the live source for Queen Books events |
| A Different Booklist | Bookmanager scraper | 4 | Black-owned, Annex; covers events not on a Bookstore organizer page |

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
- ~~**BlogTO**~~ — Implemented as `scrapers/blogto.py`. Uses public `/api/v2/events/?date=YYYY-MM-DD&bundle_type=medium` listing endpoint (no per-event fetch). Walks day-by-day, dedupes by event id, stops after 7 empty days.
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
| ~~Massey Hall / Roy Thomson Hall~~ | ~~404~~ **Implemented** via Ticketmaster Discovery API |
| Canadian Opera Company | 526 error |
| do416.to | No feed |
| To Do Canada | 403 Forbidden |
| Songkick Toronto | No public feeds |
| Dice.fm | No Toronto page |
| Resident Advisor | 403 |
| The Rex | Squarespace but not events collection type |
| ~~Horseshoe Tavern~~ | ~~Webflow, no feed~~ **Implemented** via Ticketmaster Discovery API |
| ~~Lee's Palace~~ | ~~Custom app, no feed~~ **Implemented** via Ticketmaster Discovery API |
| ~~Danforth Music Hall~~ | ~~Custom Chakra UI app, no feed~~ **Implemented** via Ticketmaster Discovery API |
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
| Literary / bookstores | 2026-04-11 | 5 store organizers (Another Story, Ben McNally, Glad Day, Hopeless Romantic, Queen Books) + 4 publisher organizers (Coach House, Cormorant, Book*hug, Penguin Random House Canada) | Deep-dive into Toronto's indie bookstore scene; see dedicated section below |

### Not Yet Done

- Food & drink (cooking classes, tastings, farmers markets)
- Faith / spiritual
- Seniors
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
- Literary/Poetry (✅ deep dive 2026-04-11; see "Topical Search: Literary / Bookstores" section)
- Startup/Tech (mostly Meetup already covered)
- Museums (scraper opportunities: ROM, Toronto Zoo)

---

## Topical Search: Literary / Bookstores (2026-04-11)

Vertical deep-dive into Toronto's indie bookstore scene. Goal: capture author readings, book launches, signings, book clubs.

### Aggregator-based discovery

Three independent sources cross-referenced to build a complete venue inventory:

| Aggregator | URL | Toronto stores found | Method |
|------------|-----|----------------------|--------|
| indiebookstores.ca (CIBA public face) | `indiebookstores.ca/locations/` | 30 | WordPress paginated; Cloudflare 403 on default UA, works with browser UA. 28 pages × ~12 stores each = 332 Canada-wide |
| NewPages Ontario | `newpages.com/independent-bookstores/ontario-independent-bookstores/` | 33 | Plain HTML directory, structured by `City:` field |
| Bookmanager `nearbyStores/get` API | `api.bookmanager.com/customer/nearbyStores/get` | 30 (deduped) | **🎯 Free public API** — see API section below. Returns lat/long + per-store URL |

**Combined unique Toronto bookstore inventory: ~50 stores** (overlap is heavy; each aggregator catches some the others miss).

### Eventbrite organizer sweep

Per-store Eventbrite searches across all 50 stores looking for `/o/{name}-{ID}/` organizer pages.

#### ✅ Confirmed organizer pages → wired into pipeline

| Store | Organizer ID | Notes |
|---|---|---|
| Another Story Bookshop | `32458688399` | 16 upcoming events at sweep time |
| Ben McNally Books | `13414493715` | Active book club + open mic + launches |
| Glad Day Bookshop | `12026081388` | Active; not in indiebookstores.ca, found via Eventbrite browse |
| Hopeless Romantic Books | `98641543971` | Monthly hybrid book club |
| Queen Books | `64558396403` | Currently dormant (0 upcoming, 26 past) |

#### ✅ Publisher organizer pages → wired into pipeline

Discovery: many bookstore events are hosted by **publishers**, not the venues themselves. Wiring publisher organizers captures events at multiple stores in one feed.

| Publisher | Organizer ID | Events in feed | Toronto venues used |
|---|---|---|---|
| Coach House Books | `6007837525` | 74 | Society Clubhouse, Coach House HQ |
| Cormorant Books | `31280011011` | 38 | Ben McNally, Sleuth of Baker Street |
| Book*hug Press | `30975200167` | 8 | Another Story, Type Books |
| Penguin Random House Canada | `13112142972` | 96 | Various; geo-filter trims to Toronto |

Pipeline geo-filter (`city.conf`) drops non-Toronto events from publisher feeds automatically.

#### ⚠️ Has Eventbrite events as venue, no own organizer page

These stores host events on Eventbrite but don't maintain a store organizer profile. Events route through individual authors or publisher organizer pages instead. Already partially captured via the publisher feeds above.

- **A Different Booklist** — events organized by authors / co-presenting orgs
- **Caversham Booksellers** — psych/social-science specialty; events co-hosted with publishers
- **Flying Books / Flying Books at Neverland** — Neverland Book Club series; event-by-event organizers
- **Little Ghosts Books** — author-organized launches (e.g., Mark Sampson `109211559751` for Lowfield Launch)
- **Manifest Bookstore** — past Black Literacy Book Fair (one-off organizers)
- **Swipe Design \| Books + Objects** — design book launches
- **The Beguiling Books & Art** — comics; main programming is via TCAF (Toronto Comic Arts Festival), separate organization
- **Type Books** (3 locations: Forest Hill, Junction, Queen West) — launches hosted by publishers (Book*hug, PRH already captured)

#### ❌ No Eventbrite presence at all

Bookmanager-hosted, used/rare, university, or specialty stores that don't use Eventbrite. Mostly captured at the venue level via publisher feeds when authors visit.

- **Bakka Phoenix Books** — sci-fi/fantasy specialty; manual-curation venue (see below)
- **BMV Books** (3 locations) — used + remainder chain
- **Book City** (4 locations: Bloor West, Danforth, Yonge & St. Clair, In the Beach)
- **Anansi Bookshop** — House of Anansi storefront; events on Henderson Brewing not Eventbrite
- **Spacing Store** — urban-themed, runs own programming off-platform
- **Inhabit Books** — Inuit publishing storefront
- **Sleuth of Baker Street** — mystery specialty; Cormorant publisher events captured
- **Book Bar** (Bookmanager-hosted) — events-friendly venue; possibly own platform
- **A Good Read**, **Acadia Art & Rare Books**, **Balfour Books**, **Contact Editions**, **David Mason Books**, **Doug Miller Books**, **Re: Reading**, **The Monkey's Paw**, **Seekers Books**, **Thunderstruck Bookstore**, **Zoinks Music & Books**, **Cornerstone Bookshop** (Christian), **Fa Yuan Bookstore** (Chinese), **Multilingual / Mosaique**, **Tyndale Campus Store**, **UofT Bookstore**, **Ella Minnow**, **Mabel's Fables**, **Good Egg**

### Discovered via publisher-feed triangulation (after the original 50-store walk)

While building the publisher-feed venue filter (`scrapers/eventbrite_filtered.py`), the Penguin Random House Canada feed surfaced a Toronto bookstore that wasn't in indiebookstores.ca, NewPages, or the Bookmanager nearby API:

- **Moonbeam Books** — 335 Jane Street (Bloor West Village). Children's & YA indie founded 2017. Squarespace-hosted (DNS 198.185.159.144). Listed on blogTO and NewPages but not in CIBA's directory and not on Bookmanager. Site blocks `curl` (likely Squarespace bot detection); has some Eventbrite venue presence ("Holiday Happy Hour @ Moonbeam Books") but no organizer page. Status: in inventory, no event source wired yet — needs Squarespace `?format=json` probe via WebFetch and manual organizer ID lookup.

This is the triangulation working as intended: publisher feeds are filtered for known venues *and* surface new ones.

### Publisher-feed venue filter (`scrapers/eventbrite_filtered.py`)

The 8 publisher organizer feeds (Coach House, Cormorant, Book*hug, PRH Canada, HarperCollins Canada, Simon & Schuster Canada, Diaspora Dialogues, House of Anansi) used to be wired as raw `eb-to-ical` URLs. That dumped Vancouver, Montreal, Halifax, and Calgary launches into the Toronto feed. Replaced with a parameterized filter scraper that applies two rules:

- **Denylist** (`cities/toronto/bookstore_venue_denylist.txt`) — drop events at Indigo / Chapters chain stores. Currently catches 0 events; serves as a safeguard for the future.
- **Geo allowlist** (`cities/toronto/geo_allowlist.txt`) — require LOCATION to contain "Toronto" or one of the 5 inner boroughs (North York, Scarborough, Etobicoke, East York, York). Events with no location at all pass (online events from Toronto orgs).

Filtered counts (April 2026):

| Publisher | Raw | Toronto-only | Trimmed |
|---|---|---|---|
| Penguin Random House Canada | 96 | 70 | 26 |
| HarperCollins Canada | 47 | 37 | 10 |
| Simon & Schuster Canada | 19 | 13 | 6 |
| Diaspora Dialogues | 136 | 113 | 23 |
| House of Anansi | 5 | 5 | 0 |
| Coach House Books | 74 | 63 | 11 |
| Cormorant Books | 38 | 31 | 7 |
| Book*hug Press | 8 | 7 | 1 |
| **Total** | **423** | **339** | **84 (~20%)** |

The `--report` flag prints the denied + out-of-area + passed venue lists, which is useful both for tuning the filters and for discovering new Toronto literary-event venues we might want to investigate (Henderson Brewing, Society Clubhouse, MaRS Discovery District, Heliconian Hall, MOCA Toronto, etc.).

### Bookmanager platform investigation → reusable scraper

13 of the 50 Toronto indies are hosted on Bookmanager's React SPA platform (URL pattern: `{store}.com/item/_Qr...`). Reverse-engineered the platform's free public API:

```
POST https://api.bookmanager.com/customer/{endpoint}?_cb={san}
Origin: https://{store-domain}
FormData: store_id, session_id, webstore_name=<san>, ...
```

**Bootstrap sequence:** `store/getSettings` → `session/get` → `event/v2/list`.

**Useful endpoints found:**
- `nearbyStores/get` — list all Bookmanager stores near lat/long (used for the inventory walk above; reusable for any city)
- `event/v2/list` — store's events feed; rows include id, title, description, date/time, location_text, category, image_url, books[], tickets[]
- `store/getSettings` — store metadata including `san`, `id`, `address`, `lat/long`
- `event/v2/getRsvpInfo` — RSVP/waitlist counts per event

**Cautionary tale.** Initial survey hit `event/getList` (a v1 endpoint found in the JS bundle) and got 0 rows from all 7 stores I tested, leading to the **false** conclusion that "Bookmanager events feature is not used by any Toronto store" and that Bakka Phoenix should be parked as manual-curation. Verifying with playwright (rendering the actual /events page and capturing API calls) revealed the SPA calls **`event/v2/list`** instead — and several stores have populated event databases. The lesson: when an API call returns empty, render the actual UI to verify before concluding the feature is unused.

**Confirmed via v2 endpoint** (5 of 13 Toronto Bookmanager stores actively use events):

| Store | Events | Notes |
|---|---|---|
| Flying Books | 12 | Biggest haul; book clubs + launches at Neverland |
| Ben McNally Books | 9 | Complements Eventbrite feed (different event series) |
| Queen Books | 8 | Bookmanager is the live source; Eventbrite dormant |
| A Different Booklist | 4 | Closes "ambiguous bucket" gap |
| Bakka Phoenix Books | 1 | Unparks from manual-curation status |
| Another Story, Book Bar, Book City, Ella Minnow, Mabel's Fables, Sleuth, The Beguiling | 0 | On platform but don't populate events; route through Eventbrite or social |

**Implementation:**
- `scrapers/lib/bookmanager.py` — `BookmanagerEventsScraper` reusable base class (parallel to `BibliocommonsEventsScraper`)
- `scrapers/bookmanager.py` — parameterized CLI: `--san --domain --name`
- 5 workflow invocations in `.github/workflows/generate-calendar.yml`
- Each store's SAN is extracted from `var san="..."` in the store's `/events` page HTML

**Bakka Phoenix:** No longer parked as manual-curation. Now wired via the Bookmanager scraper. The earlier "manual curation" verdict was based on the v1-endpoint mistake.

### Aggregators not used (but worth noting)

| Aggregator | Status | Notes |
|---|---|---|
| CIBA `cibabooks.ca/member-directory` | JS-rendered, no data on initial fetch | Public face is indiebookstores.ca |
| All Lit Up (`alllitup.ca`) | Has bookstore map on the site but not at the URL searched | Literary Press Group; could re-check |
| Penguin Random House Canada `/canadian-independent-bookstores` | Returned page chrome only, no list visible in initial fetch | Could be JS-rendered |
| Retail Council bookstore map | 403 (Cloudflare) | Skipped |

### eb-to-ical infrastructure note

All 9 wired feeds use the third-party `eb-to-ical.daylightpirates.org` service to convert Eventbrite organizer pages to ICS. **Single point of failure** — if it goes dark, all 9 feeds break simultaneously. Documented in `discovery-lessons.md:467`. Fallback: scrape Eventbrite JSON-LD via existing `scrapers/lib/jsonld.py`.
