# Toronto Calendar Source Checklist

## Research Phase: Major Aggregators

Toronto is a major city (~3M metro). Strategy: identify major aggregators first, assess data access, then build venue list from their coverage.

### Aggregators Assessed

| Aggregator | URL | Feed? | Volume | Notes |
|------------|-----|-------|--------|-------|
| NOW Magazine | nowtoronto.com/events | **ICS** ✅ | ~30 events | WordPress Tribe, direct iCal feed works |
| BlogTO | blogto.com/events | RSS (15 only) | 215+ on site | Needs custom scraper — JSON embedded in event pages |
| Toronto Public Library | tpl.bibliocommons.com/events | **JSON API** | ~8,000 programs | Unauthenticated API, but library programs not general events |
| U of T Events | events.utoronto.ca | Localist (ICS/JSON/RSS) | Unknown | Site timed out; standard Localist endpoints should work |
| Meetup | meetup.com/find/?location=ca--toronto | ICS per group | 1-5/group | Pattern: `meetup.com/{GROUP}/events/ical/` — need to curate group list |

### Ready to Implement

1. **NOW Magazine iCal** — `https://nowtoronto.com/events/?ical=1`
   - ~30 events, WordPress Tribe Events
   - Already in feeds.txt

2. **BlogTO** — needs custom scraper
   - RSS at `blogto.com/rss/events.xml` only has ~15 items
   - Main page loads 215+ events; JSON embedded in each event page (`var event = {...}`)
   - High value, highest volume Toronto source

3. **U of T Events** — standard Localist feeds (when site is accessible)
   - `https://events.utoronto.ca/api/2/events?pp=50&days=30` (JSON)
   - `https://events.utoronto.ca/events.rss` (RSS)
   - [Localist API docs](https://developer.localist.com/doc/api)

### Needs Further Assessment

- **Toronto Public Library** — JSON API at `gateway.bibliocommons.com/v2/libraries/tpl/events` returns ~8,000 items, but these are library programs (book clubs, yoga, tech help). Need to decide if this is in scope.
- **Meetup** — per-group ICS works (`meetup.com/{GROUP}/events/ical/`) but requires curating a list of relevant Toronto groups.

---

## Non-Starters

| Source | Reason |
|--------|--------|
| Facebook Events | No public API since 2018 |
| Bandsintown | 403 errors, no public feed |
| Destination Toronto | Uses Cruncho widget, no feeds |
| Toronto.com RSS | Rate limited (429) |
| City of Toronto | WordPress RSS exists but empty (0 items); events page is static editorial |
| Eventbrite | No public feeds; API requires OAuth key |
| Exclaim! | Events section returns 404 |
| AllEvents.in | No feeds, web-only |

---

## Research Log

### 2026-02-14: Initial Aggregator Research

**BlogTO** (blogto.com/events)
- Best aggregator found
- RSS feed: `https://www.blogto.com/rss/events.xml` - only 15 items
- Main page loads 215+ events with venue data
- Event pages have clean JSON embedded: `var event = {...}`
- JSON includes: title, venue_name, address, city, website, description
- **Recommendation**: Custom scraper to fetch listing URLs, then extract JSON from each page

**NOW Magazine** (nowtoronto.com/events)
- WordPress Tribe Events Calendar (Events Calendar Pro)
- **Working iCal feed**: `https://nowtoronto.com/events/?ical=1`
- ~30 events in feed
- Venues: Aga Khan Museum, Bata Shoe Museum, Casa Loma, ROM, Comedy Lab, etc.
- **Ready to add as ICS feed** ✅ Added to feeds.txt

**Toronto Public Library**
- Uses BiblioCommons for events
- JSON API: `https://gateway.bibliocommons.com/v2/libraries/tpl/events`
- ~8,000 events, unauthenticated, paginated
- Content is library programs (crafts, book clubs, yoga, tech help), not general community events

**City of Toronto**
- WordPress RSS at `toronto.ca/feed/` exists but has 0 items
- Events section is static editorial (annual festivals list), not a dynamic calendar

**U of T Events**
- Uses Localist platform (events.utoronto.ca)
- Site timed out during testing
- Standard Localist endpoints should work: `/api/2/events`, `/events.ics`, `/events.rss`

**Meetup**
- No city-wide feed
- Per-group ICS works: `meetup.com/{GROUP}/events/ical/`
- Verified with TorontoJS

**Other aggregators checked**: Exclaim! (404), AllEvents.in (no feeds), Destination Toronto (Cruncho widget, no feeds)
