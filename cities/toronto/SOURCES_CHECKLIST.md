# Toronto Calendar Source Checklist

## Currently Implemented (44 sources)

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

### Outdoor & Nature
| Source | Type | Events | Notes |
|--------|------|--------|-------|
| Ontario Nature | WordPress Tribe ICS | 11 | Birding trips, nature talks, conservation |

### Meetup Groups (20 groups)
| Group | Events | Category |
|-------|--------|----------|
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

## Additional Meetup Groups (discovered, not yet added)

These were verified with active ICS feeds — can be added later to broaden coverage:

| Group | Slug | Events | Category |
|-------|------|--------|----------|
| 20s 30s Toronto Social | `20s-30s-toronto-social-activities` | 10 | Social |
| Soul City Social Club | `soulcity` | 10 | Social |
| Experience Toronto | `experiencetoronto` | 7 | Arts/culture |
| Hiking Network | `hiking-network` | 3 | Hiking |
| GTA Hiking & Stuff | `gta-hiking-meetup` | 1 | Hiking |
| Toronto Bruce Trail Club | `Toronto-Bruce-Trail-Club` | 1 | Hiking |
| Wilderness Union | `wildernessunion` | 2 | Outdoors |
| Toronto Heavy Boardgamers | `toronto-heavy-boardgamers` | 10 | Board games |
| Toronto Movies & Social | `toronto-movies-and-social-group` | 10 | Film |
| Sci Fi Book Club | `thescifibookclub` | 6 | Book club |
| Post-Apocalyptic Book Club | `post-apocalyptic-book-club-toronto-chapter` | 2 | Book club |
| Silent Book Club | `toronto-silent-book-club-meetup-group` | 1 | Book club |
| Toronto Japanese English Exchange | `tjex-ca` | 10 | Language |
| Language Exchange Toronto | `toronto` | 10 | Language |
| TILE Language Party | `biggest-language-party-event-social-in-toronto` | 5 | Language |
| Improv For New Friends | `meetup-group-fqsmjvcq` | 2 | Improv |
| Toronto AI & ML | `toronto-ai-machine-learning-data-science` | 10 | Tech |
| Microsoft Reactor Toronto | `microsoft-reactor-toronto` | 10 | Tech |
| Toronto Tech Stack Exchange | `toronto-tech-stack-exchange` | 10 | Tech |
| Toronto Enterprise DevOps | `toronto-enterprise-devops-user-group` | 3 | Tech |
| Toronto Postgres | `toronto-postgres` | 2 | Tech |
| Toronto Women in Business | `downtown-toronto-women-in-business-meetup` | 2 | Business |
| Toronto 20s-50s Singles Social | `toronto-20s-to-50s-singles-social` | 2 | Social |

## Needs Further Assessment

- **Toronto Public Library** — JSON API at `gateway.bibliocommons.com/v2/libraries/tpl/events` returns ~8,000 items, but these are library programs (book clubs, yoga, tech help). Needs JSON-to-ICS conversion and scoping decision.
- **U of T Events** — Localist platform at events.utoronto.ca. Site timed out during testing. Standard endpoints should work: `/api/2/events`, `/events.rss`. [Localist API docs](https://developer.localist.com/doc/api)
- **BlogTO** — Highest volume Toronto source (215+ events) but needs custom scraper. JSON embedded in event pages (`var event = {...}`).
- **Explore Kids Ontario Adventures** — Tockify feed (`ekoad`) has 822 events but covers broader GTA/Ontario, not just Toronto. May need geo-filtering.

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Facebook Events | No public API since 2018 |
| Bandsintown | 403 errors, no public feed |
| Destination Toronto | Uses Cruncho widget, no feeds |
| Toronto.com RSS | Rate limited (429) |
| City of Toronto | WordPress RSS exists but empty; events page is static editorial |
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

---

## Research Log

### 2026-02-14: Initial research + full discovery pass

**Discovery methods used:**
- DuckDuckGo platform searches (Tockify, Localist, WordPress Tribe)
- Direct WordPress `?ical=1` probing on Toronto venue/org sites
- Meetup group discovery across 13+ categories
- Aggregator assessment (BlogTO, NOW, City of Toronto, etc.)

**Key finds:**
- **torevent** Tockify calendar: ~2,900 Toronto events — single biggest source
- **CultureLink**: 494 community/newcomer events via WordPress Events Manager
- **St. Lawrence NA**: 82 events via Tockify
- **13 Meetup groups** with active ICS feeds across social, arts, hiking, cycling, dance, games, books, comedy, tech
- **6 WordPress Tribe venue sites** with working `?ical=1` feeds (museums, theatre, botanical garden)
- **25 additional Meetup groups** verified but held back for later

**Total events across all feeds:** ~3,800+
