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

### Still to Investigate

- Toronto Public Library (BiblioCommons — no public iCal found yet)
- City of Toronto events page (WordPress, no obvious feed)
- Eventbrite Toronto (need to adapt scraper for Canada)
- Meetup Toronto groups
- University calendars (UofT uses Localist — events.utoronto.ca was slow/timeout)

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
1. ✅ Add NOW Magazine ICS feed (done - in feeds.txt)
2. Build BlogTO scraper (high value)
3. Investigate TPL BiblioCommons, City of Toronto, Meetup, Eventbrite Canada
4. Check university calendars (UofT Localist)
