# Agent Strategies for Calendar Source Discovery

## Feed Discovery Strategies

### 1. Direct ICS/RSS Probing
Check common feed URL patterns:
```bash
# WordPress Events Calendar
curl -sL "https://example.com/events/?ical=1"
curl -sL "https://example.com/events/feed/"

# Tribe Events Calendar
curl -sL "https://example.com/events/?ical=1"

# Google Calendar embed detection
curl -sL "https://example.com/events/" | grep -i "calendar.google.com"

# Generic feed discovery
curl -sL "https://example.com/events/" | grep -iE "(ical|\.ics|webcal|rss|feed|xml)"
```

### 2. Platform-Specific APIs
Known platforms with discoverable feeds:

| Platform | Discovery Method |
|----------|------------------|
| **LiveWhale** (IU) | `https://events.iu.edu/live/ical/events/group_id/{id}` - find group_id in page source |
| **Tockify** | `https://tockify.com/api/feeds/ics/{calendar_name}` |
| **CitySpark** | POST to `https://portal.cityspark.com/v1/events/{slug}` |
| **Localist** | `https://{domain}/api/2/events` |
| **LibCal** | Check for `/calendar/ical/` endpoints |
| **Google Calendar** | Extract calendar ID from embed code |

### 3. HTML Scraping Patterns
When no feed exists, scrape structured HTML:

| Pattern | Example Sites |
|---------|---------------|
| **Schema.org/Event** | Many WordPress sites |
| **ISO 8601 in `content` attr** | The Bishop (Drupal) |
| **Date in URL slug** | Buskirk-Chumley |
| **SeatEngine** | Comedy Attic |
| **FullCalendar JSON** | Many modern sites |

### 4. WordPress REST API
Many WordPress sites expose event data:
```bash
curl -sL "https://example.com/wp-json/wp/v2/events"
curl -sL "https://example.com/wp-json/tribe/events/v1/events"
```

### 5. Network Inspection
Use browser DevTools to find hidden APIs:
- XHR/Fetch requests loading event data
- JSON endpoints for calendar widgets
- Embedded calendar iframe sources

### 6. Web Search for Alternative Sources
**When a site blocks scraping, search for the event elsewhere:**
```bash
# Search for a specific event title + location
# May reveal:
# - Aggregator sites with feeds (Eventbrite, Facebook Events, etc.)
# - Press releases with structured data
# - Partner sites that syndicate the same events
# - The original source if the blocked site is an aggregator
```

This can reveal:
- The upstream source (which may have a feed)
- Alternative aggregators that include the same events
- Whether the site is worth pursuing or just duplicates other sources

Example workflow:
1. Site blocks scraping (e.g., Buskirk-Chumley returns 403)
2. Get an event name from their RSS feed (even if limited)
3. Search web for: `"Event Name" bloomington site:eventbrite.com OR site:facebook.com/events`
4. If found on Eventbrite, check if venue has organizer page with feed
5. If on Facebook, events may be accessible via their API or third-party scrapers

## Anti-Scraping Workarounds

### Blocked by 403/406
- Add User-Agent header
- Add Accept header
- Try RSS feed instead of HTML

### Cloudflare Challenge
- Usually not worth bypassing
- Look for alternative sources
- Check if they have a public API

### Rate Limiting
- Add delays between requests
- Respect robots.txt
- Cache aggressively

## Source Prioritization

### Tier 1: Native Feeds (prefer these)
- ICS feeds (most reliable)
- Google Calendar public URLs
- RSS with structured dates
- Platform APIs (Tockify, LiveWhale, etc.)

### Tier 2: Scrapeable HTML
- Sites with consistent structure
- Schema.org markup
- ISO 8601 dates in attributes

### Tier 3: Lower Priority
- Sites requiring JavaScript rendering
- Heavy anti-scraping measures
- Aggregators (often duplicates)

## Deduplication Notes
When adding sources, check for overlap:
- Same venue appearing in multiple aggregators
- Regional calendars that scrape local venues
- Newspaper event listings (usually derivative)
