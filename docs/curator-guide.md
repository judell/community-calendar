# Community Calendar Curator Guide

## Overview

Public events are trapped in information silos. The library posts to their website, the YMCA uses Google Calendar, the theater uses Eventbrite, Meetup groups have their own pages. Anyone wanting to know "what's happening this weekend?" must check a dozen different sites.

Existing local aggregators typically expect event producers to "submit" events via a web form. This means producers must submit to several aggregators to reach their audience—tedious and error-prone. Worse, if event details change, producers must update each aggregator separately.

This project takes a different approach: **event producers are the authoritative sources for their own events**. They publish once to their own calendar, and individuals and aggregators pull from those sources. When details change, the change propagates automatically. This is how RSS transformed blogging, and iCalendar can do the same for events.

The gold standard is **iCalendar (ICS) feeds**—a format that machines can read, merge, and republish. If you're an event producer and your platform can publish a ICS feed, that's great. But ICS isn't the only way. The real requirement is to **embrace the open web**. A clean HTML page with well-structured event data works. What doesn't work: events locked in Facebook or behind login walls.

## The Curator Role

A **curator** builds and maintains the calendar for their community. You don't create events—you discover and connect existing event sources:

- Find organizations publishing calendars
- Test that feeds work and contain relevant events
- Add working feeds to the aggregator
- Filter out noise (events too far away, duplicates, off-topic)

The goal is a comprehensive, low-maintenance calendar that updates automatically as source organizations post their events.

## What Makes a Good Source

**Best**: Native ICS feeds (Meetup groups, Tockify calendars, Google Calendar public links). These "just work" and stay current automatically. Unfortunately, native ICS is rarer than it used to be.

**Fallback 1 — Platform APIs**: Some platforms (Eventbrite, LibCal) offer APIs or structured data that scrapers can convert to ICS. The project includes scrapers for common platforms.

**Fallback 2 — Custom scrapers**: For sites with no feed or API, an LLM can help write a scraper. Describe the calendar page structure to Claude or ChatGPT, and it can generate BeautifulSoup or Puppeteer code to extract events.

**Fallback 3 — Event posters**: For events promoted only via images (posters, flyers), an LLM can extract event details from a photo. Point your phone at a poster, and the system can parse it into calendar data.

https://github.com/judell/community-calendar/raw/main/video/event-poster-capture.mp4

**Skip**: Facebook events (API restrictions), Cloudflare-protected sites.

When you find a source that needs a scraper, document it in the city's `SOURCES_CHECKLIST.md` with the URL and any notes about the page structure. A developer (or you, with LLM assistance) can then build the scraper.

---

## Playbook for Launching a New Citywide Calendar

### Phase 1: Platform searches (grab the easy wins)
Search for feeds by platform — Tockify, Meetup ICS, WordPress `?ical=1`, Localist, Google Calendar embeds. These reliably turn up dozens of ready-to-use ICS feeds in a single pass. See Step 1 below.

### Phase 2: Topical searches (find venues by category)
Search by topic to find venues and organizations, then probe their websites for feeds (try `?ical=1`, check for Squarespace `?format=json`, look for Google Calendar embeds). This is where you find the Jazz Bistros and Grossman's Taverns that don't show up in platform searches.

This is a conversation with your agent. The topics below are a starting point — add, remove, or adjust based on what makes your city distinctive. A beach town needs "surfing, sailing, tide pools." A college town needs "alumni, Greek life." You know your community best.

**Topics to search:**

| Category | Topics |
|----------|--------|
| Arts & Culture | music, theater, comedy, dance, film, art, crafts, literature |
| Ideas & Learning | poetry, book clubs, writing, history, genealogy, philosophy, talks |
| Outdoors & Nature | hiking, walking, running, cycling, gardening, birding, conservation |
| Health & Well-Being | yoga, fitness, mindfulness, mental health, wellness |
| Food & Drink | beer, wine, food, cooking, farmers markets |
| Play & Games | trivia, board games, puzzles, casual gaming |
| Animals & Environment | pets, wildlife, animal care, sustainability |
| Community & Life Stages | kids, families, seniors, caregivers, newcomers |
| Identity & Belonging | faith, LGBTQ+, cultural heritage |
| Civic & Social Good | volunteering, mutual aid, civic engagement |
| Technology & Work | tech, digital skills, careers |

### Phase 3: Custom scrapers (last resort for high-value sources)
Only after exhausting phases 1 and 2, build scrapers for important sources that have no feeds. Prioritize by event volume and community relevance.

### Throughout all phases:
- **Test** each discovered feed to verify it works and has events (Step 2)
- **Document** findings in `cities/{city}/SOURCES_CHECKLIST.md` (Step 3)
- **Add** working feed URLs to `cities/{city}/feeds.txt` (Step 4)
- **Configure geo-filtering** if feeds include events outside your area (Step 5)
- **Register the city** in the app's home page (Step 6)

You can do these things by hand, or with any kind and amount of LLM assistance that you are comfortable with.

---

## Step 1: Platform Searches

Use DuckDuckGo (Google may block automated queries). Replace `{city}` and `{state}` with your target location.

### Google ICS Discovery (find sites serving actual .ics files)

Google indexes the raw content of ICS files. Searching for the ICS header string plus a city name surfaces sites that serve ICS feeds directly:

```
"BEGIN:VCALENDAR" "toronto"
"BEGIN:VCALENDAR" "santa rosa"
"BEGIN:VCALENDAR" "bloomington" "indiana"
```

Scan the results for sites that look like local organizations — ignore documentation pages, Stack Overflow, and timezone false positives (many ICS files reference `America/Toronto` as a timezone even if they're not Toronto events).

### High-Value Searches (do these first)

| Search | What You'll Find |
|--------|------------------|
| `{city} {state} site:meetup.com` | Meetup groups with ICS feeds |
| `{city} site:tockify.com` | Tockify calendars with ICS feeds |
| `{city} {state} inurl:/localist/` | University/govt Localist calendars |
| `"add to calendar" events {city} {state}` | Sites with ICS/iCal export |

### Discovery Searches (find potential sources)

| Search | What You'll Find |
|--------|------------------|
| `{city} {state} events site:eventbrite.com` | Eventbrite events (requires scraper) |
| `{city} {state} "community calendar"` | Local event aggregators |
| `{city} {state} inurl:/tribe_events/` | WordPress Tribe Events Calendar |
| `{city} "business improvement" events` | Neighbourhood business district calendars |
| `{city} "settlement services" OR "newcomer" events` | Immigrant service orgs (often high volume) |
| `{city} "community centre" OR "community center" events` | Community centres with event calendars |

### Ready-to-Use DuckDuckGo URLs

Copy these and replace `CITY` and `STATE`:

```
https://duckduckgo.com/?q=CITY+STATE+site%3Ameetup.com
https://duckduckgo.com/?q=CITY+site%3Atockify.com
https://duckduckgo.com/?q=CITY+STATE+inurl%3A%2Flocalist%2F
https://duckduckgo.com/?q=CITY+STATE+events+site%3Aeventbrite.com
https://duckduckgo.com/?q=CITY+STATE+%22community+calendar%22
```

### Meetup Deep Dive

1. **Browse groups near location** in browser:
   ```
   https://www.meetup.com/find/?keywords=&location=us--ca--Santa%20Rosa&source=GROUPS
   ```

2. **Extract group URLs** using browser console:
   ```javascript
   const links = Array.from(document.querySelectorAll('a')).filter(a =>
     a.href.match(/meetup\.com\/[^\/]+\/?$/) &&
     !a.href.includes('/find')
   );
   const groups = [...new Set(links.map(a => a.href.match(/meetup\.com\/([^\/\?]+)/)?.[1]).filter(Boolean))];
   console.log(groups.join('\n'));
   ```

3. **Test ICS feeds** for each group:
   ```bash
   curl -sL "https://www.meetup.com/{group-name}/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
   ```

4. **Verify location** (some groups may be nearby but not in target city):
   ```bash
   curl -sL "https://www.meetup.com/{group-name}/" -A "Mozilla/5.0" | grep -oP '"city"\s*:\s*"\K[^"]+'
   ```

5. **Exclude travel groups** whose events are international destinations

---

## Step 2: Test Discovered Feeds

### Tockify Calendar
```bash
# Extract calendar name from URL (e.g., tockify.com/pdaevents)
curl -sL "https://tockify.com/api/feeds/ics/CALENDAR_NAME" | grep -c "BEGIN:VEVENT"
```

### Meetup Group
```bash
# Extract group name from URL (e.g., meetup.com/go-wild-hikers)
curl -sL "https://www.meetup.com/GROUP_NAME/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"
```

### LiveWhale/Localist (Universities)
```bash
curl -sL "https://DOMAIN/live/ical/events" | grep -c "BEGIN:VEVENT"
# or
curl -sL "https://DOMAIN/api/2/events" | head -50
```

### WordPress Site
```bash
# Check what plugins they use
curl -sL "https://example.com/events/" -A "Mozilla/5.0" | grep -o "wp-content/plugins/[^/]*" | sort -u

# Try common feed endpoints
curl -sL "https://example.com/events/?ical=1" | head -20              # Tribe Events Calendar
curl -sL "https://example.com/events/?mec-ical-feed=1" | head -20     # Modern Events Calendar (MEC)
curl -sL "https://example.com/events/feed/" | head -20
```

### MembershipWorks
Look for "Subscribe" dropdown on calendar pages. Feed URL pattern:
```
https://api.membershipworks.com/v2/events?_op=ics&org={ORG_ID}
```

---

## Step 3: Document Findings

Create/update `cities/{cityname}/SOURCES_CHECKLIST.md`:

```markdown
# {City} Sources Checklist

## Currently Implemented
| Source | Type | Events | Status |
|--------|------|--------|--------|
| Downtown Association | Tockify ICS | 45 | ✅ Ready |

## Discovered - Ready to Add
| Source | Feed URL | Events | Notes |
|--------|----------|--------|-------|
| Go Wild Hikers | meetup.com/go-wild-hikers/events/ical/ | 12 | Outdoor hikes |

## Discovered - Needs Scraper
| Source | URL | Notes |
|--------|-----|-------|
| Local Theatre | example.com/events | SeeTickets widget |

## Non-Starters
| Source | Reason |
|--------|--------|
| City Website | Cloudflare protection |

## To Investigate
- [ ] Local library system
- [ ] High school athletics
```

---

## Step 4: Add Working Feeds

Add working feed URLs to `cities/{city}/feeds.txt`, one per line. Comments starting with `#` are supported for organization:

```
# Meetup groups
https://www.meetup.com/go-wild-hikers/events/ical/
https://www.meetup.com/local-book-club/events/ical/

# Tockify calendars
https://tockify.com/api/feeds/ics/downtown_events
```

The automated pipeline reads this file and fetches each URL during the daily build.

---

## Step 5: Geo-Filtering Setup

Geo-filtering prevents events from distant locations (e.g., away games, regional feeds) from appearing.

### Create allowed_cities.txt

Create `cities/{cityname}/allowed_cities.txt` with a radius, state, and the names of nearby cities to include:

```
# radius: 30
# state: CA
#
Davis
Woodland
Sacramento
West Sacramento
Dixon
Winters

# Excluded cities (prefix with !)
# These are filtered even without address indicators
!Fairfield
!Vacaville
```

**Syntax:**
- Plain city names are **allowed** (events there will appear)
- `!CityName` means **excluded** (events there are filtered out)
- Excluded cities catch venues like "Fairfield Library" that lack state/ZIP

**Important:**
- The `# state:` line is critical — it disambiguates city names during geocoding (Durham NC vs Durham CA). Always set it to the correct state abbreviation.
- For multi-city calendars (e.g., `raleighdurham`), the directory name isn't a real place, so auto-geocoding will fail. Use `--center lat,lng` to specify the center point manually.

You don't need to look up coordinates — the script does that automatically.

### Geocode and Validate

Run the geocoding script to add coordinates and validate distances:

```bash
python scripts/geocode_cities.py --city {cityname}

# For multi-city calendars where the directory name isn't a real place:
python scripts/geocode_cities.py --city raleighdurham --center 35.8701,-78.7937
```

This will:
1. Geocode the city name to determine the center point
2. Geocode each allowed city using OpenStreetMap (rate-limited, cached)
3. Calculate distance from center
4. Warn about any cities outside the radius
5. Update the file with coordinates

Example output:
```
No center defined, geocoding 'davis'... OK (38.5449, -121.7405)
Center: (38.5449, -121.7405)
Radius: 30.0 miles
Cities: 6

Distance report:
  Davis: 0.0 mi
  Dixon: 12.3 mi
  Sacramento: 15.2 mi
  Woodland: 8.7 mi
  Winters: 14.8 mi ⚠️ OUTSIDE RADIUS
```

### How Geo-Filtering Works

The filter only applies to events with **address-like locations** containing:
- State abbreviation (", CA")  
- ZIP code
- Street address pattern ("123 Main St")

Events with just venue names ("Theater", "Community Center") pass through unfiltered.
Virtual events (Zoom, online, webinar) always pass through.

### Validate-Only Mode

To check existing config without making API calls:

```bash
python scripts/geocode_cities.py --city {cityname} --validate-only
```

---

## Step 6: Register the City in the App

Once feeds are flowing, add the city to the app's home page so users can find it.

**`index.html`** — Add an entry to the `cityNames` map:
```javascript
const cityNames = {
  santarosa: 'Santa Rosa', davis: 'Davis', ..., yourcity: 'Your City'
};
```

**`Main.xmlui`** — Add a button in the city picker VStack (search for the existing city buttons):
```xml
<Button variant="outlined" width="100%" onClick="window.location.search = '?city=yourcity'">Your City</Button>
```

**`load-events` edge function** — Add the city's events.json URL to the `EVENTS_URLS` map in the Supabase `load-events` edge function. Without this, the CI workflow will generate events.json to GitHub Pages but the app won't see them (it reads from Supabase, not GitHub Pages directly).

The city key must match the directory name under `cities/` and the `?city=` URL parameter.

---

## Platform Reference

| Platform | Feed Discovery |
|----------|----------------|
| **Tockify** | `https://tockify.com/api/feeds/ics/{calendar_name}` |
| **Meetup** | `https://www.meetup.com/{group}/events/ical/` |
| **LiveWhale** | `https://{domain}/live/ical/events` |
| **MembershipWorks** | `https://api.membershipworks.com/v2/events?_op=ics&org={ID}` |
| **WordPress Tribe** | `https://example.com/events/?ical=1` |
| **WordPress MEC** | `https://example.com/events/?mec-ical-feed=1` |
| **Google Calendar** | Extract calendar ID from embed code |
| **Legistar** | `scrapers/legistar.py --client {client}` (WebAPI) |
| **Squarespace** | `https://example.com/events?format=json` |
| **GrowthZone** | `scrapers/growthzone.py --site {chamber}` |

---

## Duplicates

Don't worry about the same event appearing in multiple sources. The calendar deduplicates events that are identical, but when the same event comes from different sources it preserves the event and lists all the sources. For example, a concert might show sources: `Bohemian, GoLocal, Eventbrite`. This is a feature, not a bug — it reveals provenance and syndication patterns, showing how events flow through the local information ecosystem.

---

## Long-Running Events

Some sources (particularly CitySpark-powered calendars like North Bay Bohemian and Press Democrat) return multi-day events as separate daily occurrences. For example, an art exhibition like "The Unknown Wayne Thiebaud: Passionate Printmaker" at Sebastopol Center for the Arts might run for two months — and would appear as 60+ separate events, one for each day the gallery is open.

The calendar automatically collapses these long-running events to **show once per week**. This keeps exhibitions, recurring library programs, and ongoing classes visible without cluttering every single day.

**How it works:**
- Events with the same title + location + time-of-day that appear 5+ times are identified as "long-running"
- Only the first occurrence in each calendar week is displayed
- The event remains visible throughout its run, just not every day

This reduces event count significantly (typically 10-15% fewer displayed events) while maintaining weekly visibility of ongoing attractions. Curators don't need to do anything — this happens automatically in the display layer.

---

## Government & Civic Sources

### Legistar (City Council, Boards, Commissions)
Many cities use Legistar for agenda management. Check if your city has one:
```bash
# Try common client slugs: city name, county name, hyphenated
curl -s "https://webapi.legistar.com/v1/{client}/events" | head -50
# Examples: santa-rosa, wake, chapelhill, durhamcounty
```

If the API returns a JSON array of events, use the Legistar scraper:
```bash
python scrapers/legistar.py --client santa-rosa --source "City of Santa Rosa" -o legistar.ics
```

**Client name:** Extract from URL (e.g., `santa-rosa.legistar.com` → `santa-rosa`). Also try county/town names without the domain — some clients (like `wake`, `chapelhill`) don't have obvious `.legistar.com` web UIs but the API works.

**Gotcha — broken Legistar APIs:** Some cities have a `{city}.legistar.com` web UI but the API returns errors like "LegistarConnectionString not set up." This means the city uses a different backend (often BoardDocs or Granicus directly). Always test the API before adding to the workflow.

### Granicus vs Legistar (both Granicus-owned, different purposes)
- **Legistar WebAPI** → forward-looking meeting calendar with dates, committees, agendas. **This is what we scrape.**
- **Granicus video** (`{city}.granicus.com`) → backward-looking archive of meeting recordings. RSS feeds contain past meetings only. **Not useful for upcoming events.**

Don't confuse the two. A city may have Granicus video streaming but no working Legistar API (e.g., Raleigh).

### BoardDocs
Some cities use BoardDocs for agenda publishing (e.g., `go.boarddocs.com/nc/raleigh/`). No public calendar API — only a document viewer. Not currently scrapable for event feeds.

### City Website Calendars (CivicPlus, etc.)
Many city websites have ICS export. Look for "Subscribe" or calendar icons. Common patterns:
```
https://www.{city}.org/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID={N}
```
**Warning:** These feeds are often stale or incomplete. Legistar is usually more authoritative for government meetings.

---

## Additional Platform Techniques

### Squarespace Sites
Squarespace sites expose event data via `?format=json`:
```bash
curl -sL "https://example.com/events?format=json" | head -100
```
Look for `<!-- This is Squarespace. -->` in page source to confirm. Use `scrapers/lib/squarespace.py` base class.

### Wix Sites — Don't Scrape Directly
Wix sites are heavy JS nightmares. Instead, find what ticketing platform the venue uses:
- Search Eventbrite for the venue name
- Check for SeeTickets widgets
- Look for Dice.fm or AXS links

### GrowthZone (Chambers of Commerce)
Chamber sites on GrowthZone have public APIs:
```bash
curl -sL "https://business.{chamber}.com/api/events" | head -50
```
Use `scrapers/growthzone.py --site {chamber}`.

### Google Calendar Embeds
If a site embeds Google Calendar, extract the calendar ID from the iframe `src` URL:
```
https://calendar.google.com/calendar/ical/{CALENDAR_ID}/public/basic.ics
```

---

## See Also

- [docs/discovery-lessons.md](discovery-lessons.md) — Real-world lessons and gotchas from source discovery
- [AGENTS.md](../AGENTS.md) — Technical reference for scrapers and automation
