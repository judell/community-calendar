# Community Calendar Curator Guide

## Overview

Public events are trapped in information silos. The library posts to their website, the YMCA uses Google Calendar, the theater uses Eventbrite, Meetup groups have their own pages. Anyone wanting to know "what's happening this weekend?" must check a dozen different sites.

Existing local aggregators typically expect event producers to "submit" events via a web form. This means producers must submit to several aggregators to reach their audience—tedious and error-prone. Worse, if event details change, producers must update each aggregator separately.

This project takes a different approach: **event producers are the authoritative sources for their own events**. They publish once to their own calendar, and individuals and aggregators pull from those sources. When details change, the change propagates automatically. This is how RSS transformed blogging, and iCalendar can do the same for events.

The gold standard is **iCalendar (ICS) feeds**—a format that machines can read, merge, and republish. If you're an event producer and your platform supports ICS export, use it. But ICS isn't the only way. The real requirement is to **embrace the open web**: publish your events in a way that's scrapable and linkable. A clean HTML page with structured event data works. A public Google Calendar works. A Meetup group works. What doesn't work: events locked in Facebook, behind login walls, or buried in PDFs and images.

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

**Skip**: Facebook events (API restrictions), Cloudflare-protected sites, PDFs and images.

When you find a source that needs a scraper, document it in the city's `SOURCES_CHECKLIST.md` with the URL and any notes about the page structure. A developer (or you, with LLM assistance) can then build the scraper.

---

## Quick Start

1. **Search for existing feeds** using platform searches
2. **Test discovered feeds** to verify they work
3. **Document findings** in the city's `SOURCES_CHECKLIST.md`
4. **Add working feeds** to the GitHub Actions workflow
5. **Set up geo-filtering** to exclude distant locations

---

## Step 1: Platform Searches

Use DuckDuckGo (Google may block automated queries). Replace `{city}` and `{state}` with your target location.

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

### Ready-to-Use DuckDuckGo URLs

Copy these and replace `CITY` and `STATE`:

```
https://duckduckgo.com/?q=CITY+STATE+site%3Ameetup.com
https://duckduckgo.com/?q=CITY+site%3Atockify.com
https://duckduckgo.com/?q=CITY+STATE+inurl%3A%2Flocalist%2F
https://duckduckgo.com/?q=CITY+STATE+events+site%3Aeventbrite.com
https://duckduckgo.com/?q=CITY+STATE+%22community+calendar%22
```

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
curl -sL "https://example.com/events/?ical=1" | head -20
curl -sL "https://example.com/events/feed/" | head -20
```

### MembershipWorks
Look for "Subscribe" dropdown on calendar pages. Feed URL pattern:
```
https://api.membershipworks.com/v2/events?_op=ics&org={ORG_ID}
```

---

## Step 3: Meetup Discovery Process

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

## Step 4: Document Findings

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

## Step 5: Add Working Feeds

### Add Meetup Feed to Workflow

In `.github/workflows/generate-calendar.yml`, find the city's download step and add:
```yaml
curl -sL -A "Mozilla/5.0" "https://www.meetup.com/{group-name}/events/ical/" -o meetup_{short_name}.ics || true
```

### Add Source Name

In `scripts/combine_ics.py`, add to SOURCE_NAMES dict:
```python
'meetup_{short_name}': 'Meetup: Group Display Name',
```

### Run Eventbrite Scraper

```bash
python scrapers/eventbrite_scraper.py --location ca--{city} --months 2 > cities/{city}/eventbrite.ics
```

---

## Step 6: Geo-Filtering Setup

Geo-filtering prevents events from distant locations (e.g., away games, regional feeds) from appearing.

### Create allowed_cities.txt

Create `cities/{cityname}/allowed_cities.txt`:

```
# center: {lat}, {lng}
# radius: {miles}
# state: {state_abbrev}
#
# List cities to allow:
CityName1
CityName2
CityName3
```

Example for Davis:
```
# center: 38.5449, -121.7405
# radius: 30
# state: CA
#
Davis
Woodland
Sacramento
West Sacramento
Dixon
Winters
```

### Geocode and Validate

Run the geocoding script to add coordinates and validate distances:

```bash
python scripts/geocode_cities.py --city {cityname}
```

This will:
1. Geocode each city using OpenStreetMap (rate-limited, cached)
2. Calculate distance from center
3. Warn about any cities outside the radius
4. Update the file with coordinates

Example output:
```
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

## Platform Reference

| Platform | Feed Discovery |
|----------|----------------|
| **Tockify** | `https://tockify.com/api/feeds/ics/{calendar_name}` |
| **Meetup** | `https://www.meetup.com/{group}/events/ical/` |
| **LiveWhale** | `https://{domain}/live/ical/events` |
| **MembershipWorks** | `https://api.membershipworks.com/v2/events?_op=ics&org={ID}` |
| **WordPress Tribe** | `https://example.com/events/?ical=1` |
| **Google Calendar** | Extract calendar ID from embed code |

---

## Tips

- **Check for duplicates** - Same venue may appear in multiple aggregators
- **Prefer ICS feeds** over scraping when available
- **Schools are gold mines** - Check MaxPreps for high school athletics
- **Libraries often have APIs** - Look for BiblioCommons, LibCal, etc.
- **Chamber of Commerce** - Often use GrowthZone platform with XML API
