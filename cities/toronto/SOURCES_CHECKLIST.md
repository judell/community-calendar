# Toronto Calendar Source Checklist

## Research Phase: Major Aggregators

Toronto is a major city (~3M metro). Strategy: identify major aggregators first, assess data access, then build venue list from their coverage.

### Aggregators Assessed (2025-02-14)

| Aggregator | URL | Feed? | Scrapable? | Volume | Notes |
|------------|-----|-------|------------|--------|-------|
| BlogTO | blogto.com/events | RSS (15 only) | YES - JSON in pages | 215+ events | Best source - clean JSON in event pages |
| NOW Magazine | nowtoronto.com/events | **ICS** ✅ | YES | 30 events | WordPress Tribe, direct iCal feed works |
| Toronto.com | toronto.com/events | RSS (rate limited) | Blocked | ? | Got 429 on RSS feed |
| Destination Toronto | destinationtoronto.com | No | No | - | Simpleview CMS, no public API |
| Eventbrite Toronto | eventbrite.ca/d/canada--toronto | No | YES | varies | Need to adapt scraper for Canada |
| Facebook Events | - | No | No | - | Dead end (since 2018) |
| Bandsintown | - | No | No | - | 403 errors |

### Ready to Implement

1. **NOW Magazine iCal** - `https://nowtoronto.com/events/?ical=1`
   - 30 events, WordPress Tribe Events
   - Venues include: Aga Khan Museum, Bata Shoe Museum, Casa Loma, ROM, Comedy Lab, etc.

2. **BlogTO** - needs custom scraper
   - RSS only has 15 events but page loads 215+
   - JSON embedded in each event page (clean structure)
   - Would need to scrape listing page for URLs, then extract JSON from each

---

## Venue List (Built from Aggregators)

### Music Venues
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| Massey Hall | BlogTO | PENDING | Major concert hall |
| Roy Thomson Hall | BlogTO | PENDING | TSO home |
| Danforth Music Hall | BlogTO | PENDING | |
| Phoenix Concert Theatre | BlogTO | PENDING | |
| Horseshoe Tavern | BlogTO | PENDING | |
| Cameron House | BlogTO | PENDING | |
| Lee's Palace | BlogTO | PENDING | |
| Velvet Underground | BlogTO | PENDING | |
| Queen Elizabeth Theatre | BlogTO | PENDING | |
| Coca-Cola Coliseum | BlogTO | PENDING | Concerts + sports |
| Palais Royale Ballroom | BlogTO | PENDING | Historic venue |
| Free Times Cafe | BlogTO | PENDING | |

### Theaters & Performing Arts
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| Ed Mirvish Theatre | BlogTO | PENDING | Mirvish Productions |
| Royal Alexandra Theatre | PENDING | PENDING | Mirvish |
| Princess of Wales Theatre | PENDING | PENDING | Mirvish |
| Four Seasons Centre | PENDING | PENDING | COC + National Ballet |
| Harbourfront Centre | BlogTO | PENDING | Multiple venues |
| Crow's Theatre | BlogTO | PENDING | |
| Buddies in Bad Times | BlogTO | PENDING | LGBTQ+ theatre |
| Berkeley Street Theatre | BlogTO | PENDING | |
| Tarragon Theatre | PENDING | PENDING | |
| Factory Theatre | PENDING | PENDING | |
| Soulpepper Theatre | PENDING | PENDING | Distillery District |
| VideoCabaret | BlogTO | PENDING | |
| Second City Toronto | PENDING | PENDING | Comedy |
| Comedy Bar | PENDING | PENDING | |
| Backroom Comedy Club | NOW | PENDING | |
| The Comedy Lab | NOW | PENDING | |

### Museums & Galleries
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| Art Gallery of Ontario (AGO) | BlogTO | PENDING | Major museum |
| Royal Ontario Museum (ROM) | NOW, BlogTO | PENDING | Major museum |
| Aga Khan Museum | NOW, BlogTO | PENDING | Islamic arts |
| Bata Shoe Museum | NOW | PENDING | |
| Gardiner Museum | BlogTO | PENDING | Ceramics |
| Textile Museum of Canada | BlogTO | PENDING | |
| Toronto Railway Museum | BlogTO | PENDING | |
| TIFF Lightbox | BlogTO | PENDING | Film |
| Hot Docs Ted Rogers Cinema | BlogTO | PENDING | Documentary |
| OCAD University | BlogTO | PENDING | Art shows |
| Power Plant | PENDING | PENDING | Contemporary art |
| McMichael Canadian Art | NOW | PENDING | In Kleinburg |

### Major Attractions & Event Spaces
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| Casa Loma | BlogTO, NOW | PENDING | Historic castle |
| Evergreen Brick Works | BlogTO | PENDING | Markets, events |
| Nathan Phillips Square | BlogTO | PENDING | City Hall events |
| STACKT Market | BlogTO | PENDING | Container market |
| Distillery District | PENDING | PENDING | Multiple venues |
| St. Lawrence Market | PENDING | PENDING | |
| The Bentway | BlogTO | PENDING | Under Gardiner |
| Toronto Zoo | BlogTO | PENDING | |
| Little Canada | BlogTO | PENDING | |
| CN Tower | PENDING | PENDING | |
| Ripley's Aquarium | PENDING | PENDING | |
| Ontario Science Centre | PENDING | PENDING | Closed? |

### Sports & Arenas
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| Scotiabank Arena | BlogTO | PENDING | Leafs, Raptors, concerts |
| Rogers Centre | PENDING | PENDING | Blue Jays |
| BMO Field | PENDING | PENDING | TFC, Argos |
| Coca-Cola Coliseum | BlogTO | PENDING | Marlies, concerts |

### Libraries
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| Toronto Reference Library | BlogTO | BiblioCommons | 100 branches, many programs |
| Toronto Public Library | TPL site | BiblioCommons | No public iCal found |

### Community & Cultural Centers
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| Harbourfront Centre | BlogTO | PENDING | Major arts center |
| Japanese Canadian Cultural Centre | PENDING | PENDING | |
| Native Canadian Centre | PENDING | PENDING | |
| Miles Chicken Cultural Centre | PENDING | PENDING | |
| Various community centres | City of TO | PENDING | 100+ city-run |

### Universities
| Venue | Source Found | Direct Feed? | Notes |
|-------|--------------|--------------|-------|
| University of Toronto | PENDING | Likely Localist | events.utoronto.ca (slow/timeout) |
| Ryerson/TMU | PENDING | PENDING | |
| York University | PENDING | PENDING | |
| OCAD University | BlogTO | PENDING | |

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Facebook Events | No public API since 2018 |
| Bandsintown | 403 errors, no public feed |
| Destination Toronto | Simpleview CMS, no public API |
| Toronto.com RSS | Rate limited (429) |

---

## Research Log

### 2025-02-14: Initial Aggregator Research

**BlogTO** (blogto.com/events)
- Best aggregator found
- RSS feed: `https://www.blogto.com/rss/events.xml` - only 15 items
- Main page loads 215+ events with venue data
- Event pages have clean JSON embedded: `var event = {...}`
- JSON includes: title, venue_name, address, city, website, description
- Venues extracted: 110+ unique including major ones
- **Recommendation**: Custom scraper to fetch listing URLs, then extract JSON from each page

**NOW Magazine** (nowtoronto.com/events)
- WordPress Tribe Events Calendar (Events Calendar Pro)
- **Working iCal feed**: `https://nowtoronto.com/events/?ical=1`
- 30 events in feed
- Powered by Destination Toronto
- Venues: Aga Khan Museum, Bata Shoe Museum, Casa Loma, ROM, Comedy Lab, etc.
- **Ready to add as ICS feed**

**Toronto Public Library**
- Uses BiblioCommons for events
- URL: `https://tpl.bibliocommons.com/events`
- No public iCal/RSS feed found
- Would need scraper if we want TPL events

**City of Toronto**
- Has WordPress site with events page
- No obvious calendar feed found yet
- Need to investigate further

**Next Steps**:
1. Add NOW Magazine ICS feed (immediate win)
2. Build BlogTO scraper (high value)
3. Investigate major venue websites directly
4. Check Meetup for Toronto groups
5. Test Eventbrite scraper with Canada location
