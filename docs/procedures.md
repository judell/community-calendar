# Procedures for Source Discovery and Pipeline Setup

These are the step-by-step procedures referenced by the [Curator Guide](curator-guide.md) and [AGENTS.md](../AGENTS.md).

## Table of Contents

- [1. Search for Feeds](#1-search-for-feeds)
  - [Google ICS Discovery](#google-ics-discovery-find-sites-serving-actual-ics-files)
  - [High-Value Searches](#high-value-searches-do-these-first)
  - [Discovery Searches](#discovery-searches-find-potential-sources)
  - [Ready-to-Use DuckDuckGo URLs](#ready-to-use-duckduckgo-urls)
  - [Meetup Deep Dive](#meetup-deep-dive)
- [2. Test Discovered Feeds](#2-test-discovered-feeds)
  - [Tockify Calendar](#tockify-calendar)
  - [Meetup Group](#meetup-group)
  - [LiveWhale/Localist (Universities)](#livewhalelocalist-universities)
  - [WordPress Site](#wordpress-site)
  - [MembershipWorks](#membershipworks)
- [3. Document Findings](#3-document-findings)
- [4. Add Working Feeds](#4-add-working-feeds)
- [5. Geo-Filtering Setup](#5-geo-filtering-setup)
  - [Create allowed_cities.txt](#create-allowed_citiestxt)
  - [Geocode and Validate](#geocode-and-validate)
  - [How Geo-Filtering Works](#how-geo-filtering-works)
  - [Validate-Only Mode](#validate-only-mode)
- [6. Register the City in the App](#6-register-the-city-in-the-app)
- [Platform Reference](#platform-reference)
- [Government & Civic Sources](#government--civic-sources)
  - [Legistar (City Council, Boards, Commissions)](#legistar-city-council-boards-commissions)
  - [Granicus vs Legistar](#granicus-vs-legistar-both-granicus-owned-different-purposes)
  - [BoardDocs](#boarddocs)
  - [City Website Calendars (CivicPlus, etc.)](#city-website-calendars-civicplus-etc)
- [Additional Platform Techniques](#additional-platform-techniques)
  - [Squarespace Sites](#squarespace-sites)
  - [Wix Sites](#wix-sites--dont-scrape-directly)
  - [GrowthZone (Chambers of Commerce)](#growthzone-chambers-of-commerce)
  - [Google Calendar Embeds](#google-calendar-embeds)

---

## 1. Search for Feeds

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

## 2. Test Discovered Feeds

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

## 3. Document Findings

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

## 4. Add Working Feeds

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

## 5. Geo-Filtering Setup

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

## 6. Register the City in the App

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
