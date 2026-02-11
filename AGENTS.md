# Agent Strategies for Calendar Source Discovery

## Quick Reference: Adding a New City

1. **Create city directory** under `cities/` with `feeds.txt` and `SOURCES_CHECKLIST.md`
2. **Run Meetup discovery** (Section 7) - find local groups with ICS feeds
3. **Run Eventbrite scraper** (Section 8) - scrape local ticketed events
4. **Update the GitHub Actions workflow** (`.github/workflows/generate-calendar.yml`):
   - Add curl commands for Meetup ICS feeds
   - Add Eventbrite scraper command
   - Add combine_ics.py step
5. **Update `combine_ics.py`** - add SOURCE_NAMES entries for new Meetup groups
6. **Add city to `index.html`** - add entry to `cityNames` map and a Button in `Main.xmlui`'s city picker
7. **Update SOURCES_CHECKLIST.md** - document findings, track pending sources
8. **Commit and push** - workflow runs daily or trigger manually

## App Architecture

The XMLUI app lives at the repo root and serves all cities from a single set of files:

- **`index.html`** — Entry point. Reads `?city=` URL param to set `window.cityFilter` and `window.cityName`. No param shows the city picker.
- **`Main.xmlui`** — App layout. Shows city picker when `!window.cityFilter`, calendar UI when a city is selected. Queries Supabase filtered by `window.cityFilter`.
- **`components/`** — Shared XMLUI components (EventCard, PickItem, etc.)
- **`Globals.xs`** — Shared state (pickEvent, picksData, enrichmentsData, refreshCounter) and functions (togglePick, removePick)
- **`helpers.js`**, **`config.json`** — Pure helper functions and app configuration

**URLs:** `index.html?city=santarosa`, `index.html?city=davis`, `index.html?city=bloomington`, etc.

**Do not duplicate app files into city directories.** City directories (`cities/<name>/`) hold only data (ICS files, events.json) and city-specific docs (SOURCES_CHECKLIST.md). Bloomington's legacy static HTML files are an exception.

Legacy HTML generation code (`cal.py`, templates, `sorttable.js`) lives in `legacy/`.

**Edge function gotcha:** Redeploying any edge function via the Supabase MCP tool resets "Require JWT" to ON. The workflow calls `load-events` with the anon key, so after redeploying you must manually turn off "Require JWT" in the Supabase dashboard (Edge Functions > function-name > Settings).

**DDL files (`supabase/ddl/`)** document the live database state — they are not migration scripts. When the schema changes in Supabase, update the corresponding DDL file to stay in sync. Files: 01_extensions, 02_events, 03_picks, 04_feed_tokens, 05_cron_jobs, 06_event_enrichments.

### SOURCES_CHECKLIST.md

Each city should have a `SOURCES_CHECKLIST.md` to track ongoing discovery:
- **Currently Implemented** - sources already in the workflow
- **Meetup Groups** - results of Meetup discovery with dates
- **Eventbrite** - scraper results and key venues found
- **Potential Additional Sources** - venues/orgs to investigate
- **Non-Starters** - sources that were checked but don't work (and why)

This serves as institutional memory so future work doesn't duplicate effort.

## Quick Reference: Meetup + Eventbrite for Existing City

1. **Meetup**: Browse `meetup.com/find/?location=us--{state}--{City}`, extract groups, test ICS feeds, verify locations
2. **Eventbrite**: Run `python scrapers/eventbrite_scraper.py --location {state}--{city} --months 2`
3. **Update workflow**: Add curl commands for Meetup, add eventbrite_scraper.py command
4. **Update combine_ics.py**: Add SOURCE_NAMES for Meetup groups
5. **Update SOURCES_CHECKLIST.md**: Document what was found

## Quick Reference: Adding a New Scraper

When creating a new scraper for an existing city, **all three steps are required**:

1. **Create the scraper** in `scrapers/` directory
2. **Add to workflow** (`.github/workflows/generate-calendar.yml`)
3. **Add source name** (`scripts/combine_ics.py`)

### Recommended: Use the add_scraper script

```bash
# Automatically adds to workflow and combine_ics.py:
python scripts/add_scraper.py myscraper santarosa "My Source Name"

# With testing:
python scripts/add_scraper.py myscraper santarosa "My Source Name" --test

# Preview without making changes:
python scripts/add_scraper.py myscraper santarosa "My Source Name" --dry-run
```

### Manual steps (if not using the script)

1. **Create the scraper** in `scrapers/` directory
   - Test it locally: `python scrapers/myscraper.py --output /tmp/test.ics`
   - Verify output: `grep -c "BEGIN:VEVENT" /tmp/test.ics`

2. **Add to workflow** (`.github/workflows/generate-calendar.yml`):
   - Find the city's "Scrape {City} sources" step
   - Add: `python scrapers/myscraper.py --output cities/{city}/myscraper.ics || true`

3. **Add source name** (`scripts/combine_ics.py`):
   - Add entry to `SOURCE_NAMES` dict: `'myscraper': 'My Source Name',`

**If you skip steps 2-3, the scraper won't run in CI and events won't appear!**

---

## Web Search Discovery Strategy

**Use search engines to find calendar platforms and feeds.** DuckDuckGo is recommended (Google may block automated queries).

### Platform Site Searches (High Value)

These searches find platforms that typically have ICS feeds:

```
{city} {state} site:meetup.com          # Meetup groups (have ICS feeds)
{city} site:tockify.com                   # Tockify calendars (have ICS feeds)
{city} {state} inurl:/localist/           # University/govt calendars (often have feeds)
```

### Calendar Export Searches (High Value)

Sites with "add to calendar" functionality often have discoverable ICS feeds:

```
"add to calendar" events {city} {state}           # Surfaces sites with ICS/iCal export
```

This pattern found Google Calendar feeds and LiveWhale ICS endpoints in testing.

### Discovery Searches

These help identify what events exist (may need scrapers):

```
{city} {state} events site:eventbrite.com         # Eventbrite (needs scraper)
{city} {state} "community calendar"               # Local aggregators
{city} {state} events site:facebook.com/events    # Limited: browser-only, no feeds, individual events only
```

### Platform Detection Searches

```
{city} {state} inurl:/tribe_events/       # WordPress Tribe Events Calendar
{city} {state} inurl:/events/             # Generic events pages
{city} {state} events "add to google calendar"   # Sites with calendar exports
```

### DuckDuckGo URL Templates

Ready-to-use (replace CITY and STATE):

```
https://duckduckgo.com/?q=CITY+STATE+site%3Ameetup.com
https://duckduckgo.com/?q=CITY+site%3Atockify.com
https://duckduckgo.com/?q=CITY+STATE+inurl%3A%2Flocalist%2F
https://duckduckgo.com/?q=CITY+STATE+events+site%3Afacebook.com%2Fevents
https://duckduckgo.com/?q=CITY+STATE+events+site%3Aeventbrite.com
https://duckduckgo.com/?q=CITY+STATE+%22community+calendar%22
```

### Testing Discovered Feeds

**Tockify** (URL like `tockify.com/calendarname/...`):
```bash
curl -sL "https://tockify.com/api/feeds/ics/CALENDAR_NAME" | grep -c "BEGIN:VEVENT"
```

**Meetup** (URL like `meetup.com/groupname/`):
```bash
curl -sL "https://www.meetup.com/GROUP_NAME/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
```

**Localist**:
```bash
curl -sL "https://DOMAIN/api/2/events" | head -50
```

See [docs/curator-guide.md](docs/curator-guide.md) for the complete curator workflow.

---

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
| **LiveWhale** | `https://{domain}/live/ical/events` - common at colleges (SRJC: 114 events, IU: 923 events) |
| **Tockify** | `https://tockify.com/api/feeds/ics/{calendar_name}` |
| **CitySpark** | POST to `https://portal.cityspark.com/v1/events/{slug}` |
| **Localist** | `https://{domain}/api/2/events` |
| **LibCal** | Check for `/calendar/ical/` endpoints |
| **Google Calendar** | Extract calendar ID from embed code |
| **Elfsight Event Calendar** | JSON API - see below |

### 3. HTML Scraping Patterns
When no feed exists, scrape structured HTML:

| Pattern | Example Sites |
|---------|---------------|
| **Schema.org/Event** | Many WordPress sites |
| **ISO 8601 in `content` attr** | The Bishop (Drupal) |
| **Date in URL slug** | Buskirk-Chumley |
| **SeatEngine** | Comedy Attic |
| **FullCalendar JSON** | Many modern sites |

### Elfsight Event Calendar

[Elfsight](https://elfsight.com/event-calendar-widget/) is a popular embeddable widget platform. Sites using their Event Calendar widget have all event data available via a JSON API.

**Detection:** Look in page source for `elfsight-app-` or `class="eapps-event-calendar-"` followed by a UUID.

**API Endpoint:**
```bash
# widget_id is the UUID found in the page source
curl -sL "https://core.service.elfsight.com/p/boot/?page={source_page_url}&w={widget_id}"
```

**Response:** JSON containing `events`, `locations`, `eventTypes`, `hosts` arrays with full event data including recurring event rules.

**Scraper Library:** Use `scrapers/lib/elfsight.py`:
```python
from scrapers.lib.elfsight import ElfsightCalendarScraper

class MySiteScraper(ElfsightCalendarScraper):
    name = "My Site Events"
    domain = "mysite.com"
    widget_id = "c18b022b-4e3e-4ab7-9baa-a3214cef181f"  # From page source
    source_page = "https://mysite.com/calendar"

if __name__ == '__main__':
    MySiteScraper.main()
```

**Known sites using Elfsight:**
- Sports Basement (`scrapers/sportsbasement.py`) - Bay Area sporting goods chain

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

### 7. Topic-Based Discovery
**Search for events by activity/interest rather than by venue:**

Useful when you want to find sources for specific community interests that may not be covered by major venues.

```bash
# Search patterns for topic-based event discovery
"birding events" bloomington calendar
"hiking club" bloomington events
"astronomy" bloomington "star party" OR "public viewing"
"garden club" bloomington events calendar
"book club" bloomington library events
"running club" bloomington calendar
"cycling" bloomington "group ride" calendar
```

This can reveal:
- Meetup.com groups (which have ICS feeds)
- Facebook groups with event calendars
- Niche organizations with their own calendars
- Parks/nature centers with outdoor programming
- Library branches with special interest events

Meetup.com is particularly valuable - groups have ICS feeds at:
`https://www.meetup.com/{group-name}/events/ical/`

**Meetup Discovery Process:**

1. **Browse groups near location** using browser:
   ```
   https://www.meetup.com/find/?keywords=&location=us--ca--Santa%20Rosa&source=GROUPS
   ```

2. **Extract group URLs** from the page using browser JS:
   ```javascript
   const links = Array.from(document.querySelectorAll('a')).filter(a => 
     a.href.match(/meetup\.com\/[^\/]+\/?$/) && 
     !a.href.includes('/find')
   );
   const groups = [...new Set(links.map(a => a.href.match(/meetup\.com\/([^\/\?]+)/)?.[1]).filter(Boolean))];
   ```

3. **Test ICS feeds** for each group:
   ```bash
   curl -sL "https://www.meetup.com/{group-name}/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
   ```

4. **Verify location** (some groups may be nearby but not in target city):
   ```bash
   curl -sL "https://www.meetup.com/{group-name}/" -A "Mozilla/5.0" | grep -oP '"city"\s*:\s*"\K[^"]+'
   ```

5. **Check event content** - exclude travel groups whose events are international destinations

6. **Update workflow** - After adding feeds to `feeds.txt`, also add to `.github/workflows/generate-calendar.yml`:
   ```yaml
   # In the "Download [City] live feeds" step:
   curl -sL -A "Mozilla/5.0" "https://www.meetup.com/{group-name}/events/ical/" -o meetup_{short_name}.ics || true
   ```

7. **Add source name** to `combine_ics.py` SOURCE_NAMES dict:
   ```python
   'meetup_{short_name}': 'Meetup: Group Display Name',
   ```

### 8. Eventbrite Scraping

**Eventbrite has no public feed, but individual event pages have JSON-LD structured data.**

Use `scrapers/eventbrite_scraper.py`:
```bash
# Scrape events for a location, limited to next N months
python scrapers/eventbrite_scraper.py --location ca--santa-rosa --months 2

# For Davis area with multiple cities
python scrapers/eventbrite_scraper.py --location ca--davis --months 2 \
  --cities davis woodland dixon winters "west sacramento"
```

The scraper:
1. Fetches event URLs from `eventbrite.com/d/{location}/all-events/?end_date={date}`
2. Extracts JSON-LD Schema.org Event data from each page
3. Filters by city (addressLocality field)
4. Outputs ICS format

**Add to workflow** in `.github/workflows/generate-calendar.yml`:
```yaml
# In scraper or download step:
python scrapers/eventbrite_scraper.py --location ca--{city} --months ${SCRAPE_MONTHS:-2} > {city}/eventbrite.ics || true
```

**Note:** Eventbrite requires periodic re-scraping (no live feed). The `--months` flag uses Eventbrite's `end_date` URL parameter to pre-filter, reducing scrape time.

### 9. WordPress Plugin Detection
**Identify upstream sources by checking what plugins a site uses:**

```bash
# List WordPress plugins
curl -sL "https://example.com/events/" -A "Mozilla/5.0" | grep -o "wp-content/plugins/[^/]*" | sort -u
```

Useful discoveries:
- `import-eventbrite-events` → Events come from Eventbrite
- `widget-for-eventbrite-api` → Same as above
- `tribe-events-calendar` → Try `?ical=1` endpoint
- `events-manager` → Check for ICS export option
- `the-events-calendar` → Tribe Events, try ICS

Example: Indiana Audubon uses Eventbrite plugins, meaning their events originate from an Eventbrite organizer page.

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

## Validation Checklist
Before adding a source, verify:
1. **Location relevance** - Is it actually in the target area?
2. **Event count** - Does it have enough events to be worth adding?
3. **Feed validity** - Does the ICS parse correctly?
4. **Content type** - Are events public community events vs internal meetings?
5. **Overlap** - Does it duplicate events from existing sources?

## Known Platform Limitations

| Platform | Issue |
|----------|-------|
| **Planning Center/Church Center** | No public API; requires login |
| **Simpleview CMS** | Tourism sites; no public events API |
| **OpenDate** | Ticketing platform; no public feed |
| **Cloudflare-protected sites** | Challenge pages block scrapers |
| **Facebook Events** | No public API since 2018; `site:facebook.com/events` only works in browser, not via search APIs; finds individual events, not feeds |
