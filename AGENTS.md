# Agent Strategies for Calendar Source Discovery

## Table of Contents

- [Discovery Philosophy](#discovery-philosophy)
- [Quick Reference: Adding a New City](#quick-reference-adding-a-new-city)
- [App Architecture](#app-architecture)
  - [SOURCES_CHECKLIST.md](#sources_checklistmd)
- [Editing the Workflow YAML](#editing-the-workflow-yaml)
- [Quick Reference: Adding a New Scraper](#quick-reference-adding-a-new-scraper)
  - [Verification Checklist](#verification-checklist)
  - [Recommended: Use the add_scraper script](#recommended-use-the-add_scraper-script)
  - [feeds.txt is auto-generated](#feedstxt-is-auto-generated)
- [Quick Reference: Adding a New ICS Feed](#quick-reference-adding-a-new-ics-feed)
- [Reusable Scrapers](#reusable-scrapers)
  - [MaxPreps](#maxpreps-scrapersmaxprepspy---high-school-athletics)
  - [GrowthZone](#growthzone-scrapersgrowthzonepy---chamber-of-commerce)
  - [Library Intercept](#library-intercept-scriptslibrary_interceptpy)
  - [Elfsight Calendar](#elfsight-calendar-scraperslibelfsigtpy)
  - [Legistar](#legistar-scraperslegistarpy---city-government-meetings)
  - [Bibliocommons](#bibliocommons-scraperslibbibliocommunspy---library-event-platforms)
  - [GoDaddy Calendar](#godaddy-calendar-scraperslibgodaddypy---godaddy-website-builder)
  - [Mobilize.us](#mobilizeus-scrapersmobilizepy---civic-and-political-organizing)
- [Platform-Specific Techniques](#platform-specific-techniques)
  - [SeeTickets Widgets](#seetickets-widgets)
  - [Wix Events](#wix-events)
- [Source Discovery](#source-discovery)
  - [Strategy 1: Ticketing Platform Indirection](#strategy-1-ticketing-platform-indirection)
  - [Strategy 2: Topical Search for New Cities](#strategy-2-topical-search-for-new-cities)
  - [Strategy 3: Meetup ICS Pattern](#strategy-3-meetup-ics-pattern)
  - [Strategy 4: Platform-Specific Discovery](#strategy-4-platform-specific-discovery)
- [Pipeline Validation](#pipeline-validation)
  - [Validation Script](#validation-script)
  - [Common Silent Failure Causes](#common-silent-failure-causes)
- [Known Platform Limitations](#known-platform-limitations)

## Discovery Philosophy

**We want COMPLETE coverage, not curated coverage.** This means:

1. **Long-tail events matter** - A book club with 5 members, a small craft meetup, a neighborhood cleanup - these ARE our target. Don't skip sources just because they seem niche or low-volume.

2. **Schools are gold mines** - High schools and colleges have athletic events, theater, band concerts, art shows, parent nights, graduation ceremonies.

3. **Churches and community centers** - Weekly services may not be interesting, but special events (concerts, fundraisers, community dinners) are.

4. **Youth sports leagues** - Worth checking but rarely viable; most use member-only platforms (see [discovery lessons](docs/discovery-lessons.md)).

5. **If in doubt, add it** - We can always filter later. Missing events is worse than having too many.

## Quick Reference: Adding a New City

1. **Create city directory** under `cities/` with `SOURCES_CHECKLIST.md`
2. **Run source discovery** — platform searches (Tockify, WordPress `?ical=1`, Meetup ICS), topical searches. See [docs/curator-guide.md](docs/curator-guide.md). Run the playbook first, assess gaps second.
3. **Update the GitHub Actions workflow** (`.github/workflows/generate-calendar.yml`):
   - Add city to the locations list (line with `echo "list=..."`)
   - Add a city section with curl commands for all feeds + `combine_ics.py` call
   - Add city to the backup/restore lists in the commit step (`for city in ...`)
4. **Source metadata** — for feeds, `add_feed.py` writes structured comments to `feeds.txt` (friendly name + fallback URL); for scrapers, `add_scraper.py` adds `SOURCE_NAMES` entries to `combine_ics.py`. No manual dict editing needed.
5. **Add city to UI** — TWO places must be updated:
   - `index.html`: add entry to `cityNames` map (e.g., `toronto: 'Toronto'`)
   - `Main.xmlui`: add a Button in the city picker VStack (search for "Choose your city")
6. **Add city to load-events function** — add URL entry to `EVENTS_URLS` in `supabase/functions/load-events/index.ts`, then redeploy the edge function
7. **Optionally set up geo-filtering** — create `city.conf` if feeds include events outside your area. This is optional; if the file doesn't exist, all events pass through. See [docs/procedures.md](docs/procedures.md#5-geo-filtering-setup).
8. **Update SOURCES_CHECKLIST.md** — document findings, track pending sources
9. **Commit and push** — workflow runs daily or trigger manually

## App Architecture

The XMLUI app lives at the repo root and serves all cities from https://judell.github.io/community-calendar/.

- **`index.html`** — Entry point. Reads `?city=` URL param to set `window.cityFilter` and `window.cityName`. No param shows the city picker.
- **`Main.xmlui`** — App layout. Shows city picker when `!window.cityFilter`, calendar UI when a city is selected. Queries Supabase filtered by `window.cityFilter`.
- **`Main.xmlui.xs`** — Shared state (pickEvent, picksData, enrichmentsData, refreshCounter) and functions (togglePick, removePick)
- **`components/`** — Shared XMLUI components (EventCard, PickItem, etc.)
- **`helpers.js`**, **`config.json`** — Pure helper functions and app configuration

**URLs:** `index.html?city=santarosa`, `index.html?city=davis`, `index.html?city=bloomington`, etc.

**Edge function gotcha:** Redeploying any edge function via the Supabase MCP tool resets "Require JWT" to ON. The workflow calls `load-events` with the anon key, so after redeploying you must manually turn off "Require JWT" in the Supabase dashboard.

**DDL files (`supabase/ddl/`)** document the live database state — they are not migration scripts.

### Source Attribution

Source attribution flows through a single structured field, **not** through event descriptions:

```
Scraper/Feed ICS  →  combine_ics.py  →  ics_to_json.py  →  Supabase DB  →  EventCard.xmlui
   X-SOURCE           X-SOURCE           source column       source column    italic "Source: X"
   DESCRIPTION         (untouched)        description col     description col  (search snippets only)
```

- **`X-SOURCE`** ICS header carries the source name. `combine_ics.py` adds it only if missing.
- **`source`** DB column is populated from `X-SOURCE` by `ics_to_json.py`.
- **`EventCard.xmlui`** line 26 renders `$props.event.source` as an italic line.
- **DESCRIPTION** is for actual event content only. Do NOT put "Source:" text in descriptions — it causes duplicate display since the app renders both.

**How X-SOURCE gets set — two paths:**

1. **Feeds** (ICS URLs in `feeds.txt`): `download_feeds.py` reads the structured comment above each URL (e.g., `# Friendly Name | https://fallback-url/`) and injects `X-SOURCE` and `X-SOURCE-URL` headers into every VEVENT at download time. No dict entry needed.

2. **Scrapers** (Python scripts in the workflow): `BaseScraper.create_event()` sets `X-SOURCE` from the `--name` argument. `add_scraper.py` also adds a `SOURCE_NAMES` entry in `combine_ics.py` as a fallback.

**`SOURCE_NAMES`/`SOURCE_URLS`** dicts in `combine_ics.py` are a **legacy fallback** for ICS files that lack `X-SOURCE`. New feeds should never need entries there — the structured comment in `feeds.txt` is the source of truth. Do NOT add new feed entries to these dicts.

### SOURCES_CHECKLIST.md

Each city should have a `SOURCES_CHECKLIST.md` to track ongoing discovery:
- **Currently Implemented** - sources already in the workflow
- **Meetup Groups** - results of Meetup discovery with dates
- **Scraper Sources** - results of scraper-based discovery
- **Potential Additional Sources** - venues/orgs to investigate
- **Non-Starters** - sources that were checked but don't work (and why)

---

## Editing the Workflow YAML

The workflow file (`.github/workflows/generate-calendar.yml`) looks intimidating but every source is just one of two patterns. Each city has two steps that group these, but a given source uses one or the other:

**Pattern 1: Live feed** — the site provides an ICS URL, just curl it:
```yaml
        curl -sL "https://example.com/events/?ical=1" -o example.ics || true
```
(For Meetup feeds, add `-A "Mozilla/5.0"` after `curl -sL`.)

**Pattern 2: Scraper** — no ICS feed, so a Python script extracts events:
```yaml
        python scrapers/myscraper.py --output cities/{city}/myscraper.ics || true
```

That's it. Everything else in the workflow (setup, combine, commit, deploy) is boilerplate you don't touch. Just append your line to the right city section.

---

## Quick Reference: Adding a New Scraper

When creating a new scraper for an existing city, **all steps are required**:

1. **Create the scraper** in `scrapers/` directory
2. **Run the scraper** to generate initial ICS file in `cities/{city}/`
3. **Add scraper to workflow** (`.github/workflows/generate-calendar.yml`)
4. **Update SOURCES_CHECKLIST.md** - document what was added
5. **Commit and push** - include the ICS file

`add_scraper.py` handles steps 3 and also adds a `SOURCE_NAMES` entry in `combine_ics.py` as fallback. You do NOT need to edit `feeds.txt` for scrapers.

### Verification Checklist

Before considering a scraper "done", verify:

| Step | Command/Check |
|------|---------------|
| Scraper runs | `python scrapers/myscraper.py -o cities/{city}/myscraper.ics` |
| ICS has events | `grep -c 'BEGIN:VEVENT' cities/{city}/myscraper.ics` |
| In workflow | `grep myscraper .github/workflows/generate-calendar.yml` |
| In combine_ics.py | `grep myscraper scripts/combine_ics.py` |
| Committed | `git status` shows no uncommitted scraper files |

### Recommended: Use the add_scraper script

After creating the scraper in `scrapers/`, use `add_scraper.py` to wire it into the pipeline. The script automates two of the manual steps above:

1. **Finds the scraper** in `scrapers/` (including subdirectories)
2. **Adds it to the workflow** — inserts a `python scrapers/<name>.py --output cities/<city>/<name>.ics || true` line into the city's "Scrape" section in `.github/workflows/generate-calendar.yml`
3. **Adds the source name** — adds an entry to `SOURCE_NAMES` in `scripts/combine_ics.py`

With `--test`, it also runs the scraper first and checks that it produces a valid .ics file with events.

```bash
# Simple scraper (dedicated .py file)
python scripts/add_scraper.py myscraper santarosa "My Source Name"
python scripts/add_scraper.py myscraper santarosa "My Source Name" --test      # test first
python scripts/add_scraper.py myscraper santarosa "My Source Name" --dry-run   # preview

# Reusable/parameterized scraper (e.g. eventbrite, squarespace, songkick)
python scripts/add_scraper.py eventbrite petaluma "Blue Zones Project Petaluma" \
  --extra-args '--url "https://www.eventbrite.com/o/78957912343" --name "Blue Zones Project Petaluma"' \
  --output-name bluezones_petaluma
```

`--extra-args` inserts flags before `--output` in the workflow command. `--output-name` overrides the .ics filename (default: scraper name). The script is idempotent — safe to run again on an already-added scraper.

You still need to manually update `SOURCES_CHECKLIST.md` and commit/push.

**If you skip any step, events won't appear in the calendar!**

### feeds.txt is the source of truth for live feeds

`feeds.txt` is where live feed URLs and their metadata live. Each URL should have a structured comment above it:

```
# Friendly Source Name | https://fallback-url/
https://actual-feed-url/events/?ical=1

# Friendly Source Name
https://another-feed-url/events/ical/
```

The `|`-separated fallback URL is optional — only needed when the ICS feed's events lack per-event URLs. `download_feeds.py` reads these comments and injects `X-SOURCE` (and `X-SOURCE-URL`) headers into every VEVENT at download time. This is how friendly source names get into the pipeline for feeds — no `SOURCE_NAMES` dict entry needed.

---

## Quick Reference: Adding a New ICS Feed

For ICS feeds that don't need a scraper (direct curl), use `add_feed.py`:

```bash
python scripts/add_feed.py "https://example.com/events/?ical=1" toronto "Example Events"
python scripts/add_feed.py URL city "Source Name" --test      # test first
python scripts/add_feed.py URL city "Source Name" --dry-run   # preview
```

This will:
1. Test the feed URL returns valid ICS
2. Add a structured comment + URL to `cities/{city}/feeds.txt`

At build time, `download_feeds.py` reads the comment, downloads the ICS, and injects `X-SOURCE` headers. You do **not** need to edit `combine_ics.py` — the friendly name flows from the `feeds.txt` comment.

You still need to manually update `SOURCES_CHECKLIST.md`.

---

## Reusable Scrapers

### MaxPreps (`scrapers/maxpreps.py`) - High School Athletics
```bash
python scrapers/maxpreps.py --school petaluma-trojans -o events.ics
python scrapers/maxpreps.py --school casa-grande-gauchos -o events.ics
python scrapers/maxpreps.py --url "https://www.maxpreps.com/ca/davis/davis-blue-devils/events/" --name "Davis High" -o events.ics
```

### GrowthZone (`scrapers/growthzone.py`) - Chamber of Commerce
```bash
python scrapers/growthzone.py --site petalumachamber -o events.ics
```

### Library Intercept (`scripts/library_intercept.py`)
```bash
python scripts/library_intercept.py --location petaluma -o library.ics
```

### Elfsight Calendar (`scrapers/lib/elfsight.py`)
For sites using Elfsight Event Calendar widget. See `scrapers/sportsbasement.py` for example.

### Legistar (`scrapers/legistar.py`) - City Government Meetings
```bash
python scrapers/legistar.py --client santa-rosa -o events.ics
python scrapers/legistar.py --client santa-rosa --source "City of Santa Rosa" -o events.ics
```
For cities using Legistar for agenda management. Client name is from the Legistar URL (e.g., `santa-rosa.legistar.com` → `santa-rosa`). Uses the Legistar WebAPI with OData queries for future events.

**Discovery:** Try `curl -s "https://webapi.legistar.com/v1/{client}/events" | head -50`. If it returns JSON, the client works. Common client names: city slug (`santa-rosa`), county slug (`wake`, `durhamcounty`), or town name (`chapelhill`).

**Gotcha:** Some cities have a `{city}.legistar.com` web UI but a broken API (e.g., Raleigh returns "LegistarConnectionString not set up"). These cities use Granicus for video but not Legistar for legislative data. Always test the API before adding to the workflow.

### Guild.host (`scrapers/guildhost.py`) - Tech Community Events
```bash
python scrapers/guildhost.py --group civic-tech-toronto --name "Civic Tech Toronto" -o cities/toronto/guildhost_civic_tech.ics
```
Guild.host is a community platform used mainly by **tech-focused groups** (JavaScript meetups, civic tech, DevTools, etc.). No ICS feeds — it's a JS-rendered SPA, but individual event pages have clean JSON-LD `Event` schema. The scraper fetches the listing page, extracts event slugs, then parses JSON-LD from each event page. Handles mixed physical + virtual locations.

**Discovery:** `site:guild.host "{city}"` — the platform has no location-based search. Most useful for cities with active tech scenes (Toronto, Montreal, London, Amsterdam). For a typical non-tech city, expect zero results.

### Songkick (`scrapers/songkick.py`) - Music Venue Showtimes
```bash
python scrapers/songkick.py --url "https://www.songkick.com/venues/32209-wellmont-theater" --name "Wellmont Theater" -o events.ics
```
Extracts `MusicEvent` JSON-LD from any Songkick venue page. Artists push their own tour dates to Songkick, so this gives you artist-sourced data in a single HTTP request — no bot protection to deal with, no pagination needed. See [Strategy 4](#strategy-4-artist-sourced-data-songkick-bandsintown) for when and why to use this.

### Montclair Film (`scrapers/montclair_film.py`) - Film Showtimes via JSON-LD subEvents
```bash
python scrapers/montclair_film.py -o cities/montclair/montclair_film.ics
```
Montclair Film uses WordPress with a groundplan-pro plugin. The listing page at `/all-event/` links to ~15 current films; each film page has JSON-LD with a `subEvent` array of individual screenings. This is a site-specific scraper but illustrates the **listing page + JSON-LD** pattern: discover URLs from a listing page, then extract structured data from each. 16 fetches yield 128 screenings.

### Sweetwater Music Hall (`scrapers/sweetwater.py`) - RSS Feed + JSON-LD
```bash
python scrapers/sweetwater.py -o cities/santarosa/sweetwater.ics
```
Sweetwater's WordPress site has an RSS feed at `/events/feed/` with ~90 items. Each item links to an event page with clean JSON-LD (`startDate`, location, etc.). The RSS `pubDate` is the **publish date**, not the event date, so we must fetch individual pages for accurate dates.

**Limiting strategy for listing-page + per-page scrapers:** When a listing page (RSS, sitemap, index page) has many items but most are past events, filter before fetching individual pages. Sweetwater's scraper skips RSS items with `pubDate` older than 60 days — this cut 90 fetches to ~49 while still capturing all future events. The same principle applies to any scraper that discovers URLs from a listing and then fetches each one: find a cheap signal (publish date, URL pattern, list position) to skip items that are almost certainly past, and only pay the per-page fetch cost for likely-future events.

### Bibliocommons (`scrapers/lib/bibliocommons.py`) - Library Event Platforms
Reusable base for public-library systems on Bibliocommons gateway APIs.

Example (Toronto Public Library):
```bash
python scrapers/toronto_public_library.py -o events.ics
```
To create a new city/library scraper, subclass `BibliocommonsEventsScraper` and set:
- `library_slug` (e.g., `tpl`)
- `timezone`
- optional filters like `audience_ids`, `type_ids`, `program_ids`, `language_ids`

### GoDaddy Calendar (`scrapers/lib/godaddy.py`) - GoDaddy Website Builder
For sites built with GoDaddy Website Builder that use the calendar/events widget. These sites serve event data from a JSON API at `calendar.apps.secureserver.net` — no headless browser needed.

**Discovery:** Open the site's calendar page in a browser, open DevTools Network tab, and look for a GET request to `calendar.apps.secureserver.net/v1/events/{website_id}/{section_id}/{widget_id}`. The three UUIDs in the URL are what you need.

To create a scraper, subclass `GoDaddyScraper` and set:
- `website_id`, `section_id`, `widget_id` (from the API URL)
- `default_location` (fallback when event has no location)
- `timezone` (IANA timezone string, e.g., `"America/Denver"`)

Example:
```python
from lib.godaddy import GoDaddyScraper

class MyVenueScraper(GoDaddyScraper):
    name = "My Venue"
    domain = "myvenue.com"
    website_id = "850abeb2-..."
    section_id = "9c296a07-..."
    widget_id = "f33a9bca-..."
    default_location = "My Venue, 123 Main St, Anytown, CA"
    timezone = "America/Los_Angeles"

if __name__ == '__main__':
    MyVenueScraper.main()
```

### Mobilize.us (`scrapers/mobilize.py`) - Civic and Political Organizing
Mobilize.us hosts event pages for political and civic organizations. Each organization has a public page (e.g., `mobilize.us/indivisiblesonomacounty/`) that embeds event data as JSON in `window.__MLZ_EMBEDDED_DATA__`. The scraper extracts this data — no API key needed.

```bash
python scrapers/mobilize.py --url "https://www.mobilize.us/indivisiblesonomacounty/" --name "Indivisible Sonoma County (Mobilize)" --output cities/santarosa/mobilize_indivisible_sonoma.ics
```

Events often have multiple timeslots (recurring phone banks, weekly protests, etc.) — each timeslot becomes a separate calendar event. The scraper handles virtual events, location data, and event images.

**Discovery:** Search `site:mobilize.us "{city name}"` or `site:mobilize.us "{county name}"` to find organizations in a given area.

**Note:** Mobilize.us appears to have a public API at `api.mobilize.us/v1/` but we could not find the correct organization endpoint for specific groups. The embedded-data approach works reliably. If you find a working API pattern, prefer it over HTML parsing.

---

## Platform-Specific Techniques

| Platform | Feed Pattern |
|----------|--------------|
| **MembershipWorks** | `https://api.membershipworks.com/v2/events?_op=ics&org={ORG_ID}` |
| **Tockify** | `https://tockify.com/api/feeds/ics/{CALENDAR_ID}` |
| **LiveWhale** | `https://{domain}/live/ical/events` |
| **Localist** | `https://{domain}/api/2/events` |
| **GoDaddy Calendar** | Check DevTools for `calendar.apps.secureserver.net` requests (use scraper) |
| **WordPress Tribe** | `https://example.com/events/?ical=1` |
| **WordPress MEC** | `https://example.com/events/?mec-ical-feed=1` |
| **Legistar** | `https://webapi.legistar.com/v1/{client}/events` (WebAPI, use scraper) |
| **CivicPlus** | `https://www.{city}.org/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID={N}` |
| **Songkick** | `https://www.songkick.com/venues/{ID}-{slug}` (JSON-LD MusicEvent, use `scrapers/songkick.py`) |
| **Guild.host** | No ICS feeds. JSON-LD Event on individual pages. Tech-focused platform. Use `scrapers/guildhost.py` |

### SeeTickets Widgets
HTML classes: `.title a`, `.date`, `.see-showtime`, `.see-doortime`, `.genre`, `.ages`, `.price`
Example: `scrapers/mystic_theatre.py`

### Wix Events
Wix event pages vary. Some use cross-origin iframes from `geteventviewer.com` (not scrapeable). But others server-render events in a **Wix Repeater component** with structured HTML — these are scrapeable (see `scrapers/cafefrida.py` for an example). Check the page source before writing off a Wix site. If the events are in the HTML (look for `data-hook` attributes and repeater items), a scraper can extract them. If it's an iframe to `geteventviewer.com`, check if the venue is on Eventbrite instead.

---

## Source Discovery

**See [docs/procedures.md](docs/procedures.md) for the complete discovery workflow including:**
- Platform searches (Meetup, Tockify, Localist)
- Testing discovered feeds
- DuckDuckGo search templates
- Meetup discovery process
- Geo-filtering setup
- City registration

**See [docs/discovery-lessons.md](docs/discovery-lessons.md) for real-world lessons** (e.g., WordPress iCal endpoints, Wix→Eventbrite indirection, youth sports dead ends).

### Strategy 1: Ticketing Platform Indirection

When a venue's website is hard to scrape (Wix, heavy JS, Squarespace, etc.), **check what ticketing platform they use**. The ticketing site often has:
- Structured data (JSON-LD)
- Search APIs
- Much cleaner HTML

**Example:** A venue with a Wix or Squarespace site (heavy JS, no static content) may ticket via **SeeTickets** or **Eventbrite**, where events have structured data and cleaner HTML.

**Common ticketing platforms to check:**
- Eventbrite (search by venue name + city)
- SeeTickets (often embedded in venue sites)
- Dice.fm (music venues)
- AXS (larger venues)
- Ticketmaster (arenas, major venues)

### Strategy 2: Topical Search for New Cities

For discovering sources in a new city, search **DuckDuckGo** (Google often blocks) for `[topic] + [city name]` across the topic list in the [curator guide](docs/curator-guide.md#phase-2-topical-searches-find-venues-by-category).

City names like "Petaluma" or "Bloomington" are discriminatory enough to filter results effectively. Move quickly - assess what's worth pursuing, don't get bogged down.

**What to look for:**
- Meetup groups (add ICS feed)
- Venues with event calendars
- Community organizations
- Recurring events (trivia nights, farmers markets)

**Search for directories, not just venues.** Also search for curated venue lists and directories — these are force multipliers. A single directory can surface dozens of venues that individual topical searches miss.

Search patterns:
- `"live music venues" + {city/county}` — local music blogs, tourism boards
- `"things to do" + {city/county}` — lifestyle aggregators
- `"best {topic}" + {city/county}` — magazine/blog roundups

Example directories that proved valuable for Sonoma County:
- `northbaylivemusic.com/venues` — 350+ venues, comprehensive
- `sonomamag.com` roundups — curated picks by category
- `sonomacounty.com/activities` — tourism board

Cross-reference directories against existing sources to find gaps. A second topical pass using directories found 26 music venues with regular programming that the initial pass missed — roadhouses, brewpubs, and neighborhood bars that don't use Eventbrite/Meetup/WordPress.

**Use Yelp as a discovery tool.** Search Yelp for businesses in your area that might host events — not just entertainment venues, but craft shops, history museums, galleries, pottery studios. Then check each website for calendar plugins. Also search Yelp for **surrounding towns** within your geo-filter radius; tourism boards for neighboring communities often have rich MEC or Tribe Events calendars.

**Check downtown association member lists.** Downtown business associations (e.g., `downtownbloomington.com/our-members/`) list 100+ businesses. Most won't have calendars, but scanning the list surfaces non-obvious venues like history centers, galleries, and craft shops that host events.

**Check community radio stations.** Community radio stations often maintain volunteer-curated calendars that aggregate events across dozens of venues — including small venues with no web presence. These are high-value aggregator sources. The WFHB Community Calendar in Bloomington covers 349 events across venues that have no scrapeable calendar of their own.

**When ICS is blocked, try the REST API.** WordPress sites using The Events Calendar (Tribe) expose a JSON API at `/wp-json/tribe/events/v1/events/` that often works even when the ICS export at `?ical=1` is blocked by WAFs. The API returns structured data (dates, venues, descriptions) — no HTML parsing needed. See `lib/tribe_events.py`.

**Discovery is iterative.** The first pass catches the obvious venues. Come back later and cross-reference against directories. Each pass finds things the previous one missed.

### Strategy 3: Meetup ICS Pattern

Every Meetup group has a public ICS feed at:
```
https://www.meetup.com/{group-slug}/events/ical/
```

No scraping needed - just discover groups and add their feeds. Test with:
```bash
curl -s "https://www.meetup.com/{group-slug}/events/ical/" | head -30
```

### Strategy 4: Artist-Sourced Data (Songkick only — not Bandsintown)

When a music venue's own site is hard to scrape (bot protection, heavy JS, ticketing widgets), **look for the venue on Songkick**, where artists push their own tour dates. Songkick aggregates these onto clean venue pages with structured JSON-LD.

**Why this works:** The data flows artist → aggregator → venue page. You're getting artist-sourced tour data, not scraping the venue. A single page fetch returns `MusicEvent` JSON-LD for all upcoming shows.

**Example:** The Wellmont Theater uses ShowDog bot protection and routes through Ticketmaster/AXS. Direct scraping is impractical. But `https://www.songkick.com/venues/32209-wellmont-theater` serves clean JSON-LD with every upcoming show — one fetch, structured data, no bot games.

**How to check:**
```bash
# Search Songkick for the venue
curl -sL "https://www.songkick.com/search?query=wellmont+theater&type=venues" | grep -o 'href="/venues/[^"]*"' | head -5

# Fetch the venue page and check for JSON-LD
curl -sL "https://www.songkick.com/venues/32209-wellmont-theater" | grep -c 'MusicEvent'
```

**Reusable scraper:** `scrapers/songkick.py` handles any Songkick venue page (see [Reusable Scrapers](#reusable-scrapers) below).

**Why NOT Bandsintown:** Bandsintown looks similar but is a walled garden. The website is behind Cloudflare (403 on curl). The REST API (`rest.bandsintown.com`) requires an app ID that needs written approval from Bandsintown — it's not self-serve like Ticketmaster. And even with API access, there is **no venue endpoint** — only `/artists/{name}/events`, so you can't query "all events at venue X." Songkick is the only viable platform in this category.

**When to use this strategy:**
- Venue site has bot protection (ShowDog, Cloudflare, etc.)
- Venue tickets through a platform that's hard to scrape (Ticketmaster, AXS)
- You want clean, structured data with minimal HTTP requests
- The venue is a music venue (this pattern is music-specific)

### Strategy 5: Platform-Specific Discovery

Many event platforms have predictable feed URLs:

| Platform | Discovery Method |
|----------|------------------|
| **MembershipWorks** | Look for "Subscribe" button, org ID in URL |
| **Tockify** | Calendar ID in embed code or `tockify.com/api/feeds/ics/{id}` |
| **GrowthZone** | Chamber sites: `business.{chamber}.us/api/events` |
| **LiveWhale** | University sites: `{domain}/live/ical/events` |
| **WordPress Tribe** | `{domain}/events/?ical=1` |
| **Legistar** | `curl -s "https://webapi.legistar.com/v1/{client}/events"` — try city/county slugs |

---

## Event Classification

Events are classified into categories (Music & Concerts, Community Events, etc.) by Claude Haiku. There are **two classifiers** — one for CI, one for manual use. Both do title-dedup to avoid re-classifying recurring event instances (e.g., "Tuesday Food Deals" × 13 weeks is classified once).

### `classify_events_json.py` — CI pipeline classifier

Used by the GitHub Actions workflow during the build. Operates on `events.json` files on disk. This is the one that runs automatically.

```bash
python scripts/classify_events_json.py cities/bloomington/events.json
python scripts/classify_events_json.py cities/*/events.json
python scripts/classify_events_json.py cities/bloomington/events.json --dry-run
```

- Reads events from JSON files, classifies events missing a `category` field
- Writes classifications back to the same JSON file
- Categories carried forward from previous builds via `merge_categories.py` (runs first in CI)
- Curator overrides from the `category_overrides` Supabase table are used as few-shot examples

### `classify_events_anthropic.py` — Manual/Supabase classifier

For ad-hoc classification of events already in Supabase. Operates directly on the database.

```bash
python scripts/classify_events_anthropic.py --limit 500
python scripts/classify_events_anthropic.py --limit 50 --city bloomington --dry-run
```

- Fetches events where `category IS NULL` from Supabase
- Updates categories directly in the database via psql (requires `SUPABASE_DB_URL`)
- Useful for backfilling categories after schema changes or manual data loads

### Curator overrides

Both classifiers respect the `category_overrides` table in Supabase. When a curator manually sets a category via the pencil icon in the UI, it's stored as an override that:
1. Is never overwritten by the classifier
2. Is used as a few-shot example to improve future classifications

---

## Minimizing Per-Event Fetches

When a scraper must visit individual event pages (listing + detail pattern), minimize HTTP requests by filtering at the listing stage. Every fetch we can skip makes the build faster and reduces load on source sites.

**Strategies, in order of preference:**
1. **Use an API that returns dates in the listing** — no detail fetch needed at all (e.g., Squarespace `?format=json`, CitySpark API, Tribe Events REST API, Localist JSON API)
2. **Filter by date signal in the listing** — if the listing includes publish dates, event dates, or date-bearing URLs, skip items that are certainly past before fetching detail pages (e.g., Sweetwater skips RSS items with `pubDate` > 60 days old)
3. **Filter by URL pattern** — some sites encode dates in event URLs (e.g., `/events/2026-04-01/concert`), allowing date filtering without any fetch
4. **Cap pagination** — limit to N pages of results to bound the worst case (e.g., Monroe County History Center caps at 5 pages / 250 items)

The goal is to get sources to publish ICS feeds so scrapers become unnecessary. Until then, be a good citizen — fetch only what you need.

---

## Pipeline Validation

### Validation Script
```bash
python scripts/validate_pipeline.py --cities santarosa,bloomington,davis
python scripts/validate_pipeline.py --cities santarosa --strict
```

### Common Silent Failure Causes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| events.json not updated | Whitespace in city name | `xargs` trim in workflow |
| Scraper produces 0 events | Site changed or blocked | Check logs, update scraper |
| Source missing from events.json | Scraper not in workflow | Run `add_scraper.py` |

---

## Known Platform Limitations

| Platform | Issue |
|----------|-------|
| **Planning Center/Church Center** | No public API; requires login |
| **Simpleview CMS** | Tourism sites; no public events API |
| **Cloudflare-protected sites** | Challenge pages block scrapers |
| **Facebook Events** | No public API since 2018 |
| **Granicus video** | RSS feeds at `{instance}.granicus.com/ViewPublisherRSS.php?view_id={N}` are **backward-looking only** (archived meeting videos). Not useful for upcoming events. Don't confuse with Legistar (also Granicus-owned), which has a forward-looking WebAPI. |
| **Bandsintown** | Website behind Cloudflare (403 on curl). REST API requires written approval from Bandsintown. Even with API access, no venue endpoint — only `/artists/{name}/events`. Not viable. |
| **SeeTickets / Eventim US** | SeeTickets US rebranded as Eventim in March 2025 (same platform). No public API — affiliate account required. Cannot filter by single venue. US platform runs legacy ASP.NET (`wafform.aspx`), unlike Eventim Europe which has an unauthenticated search API at `public-api.eventim.com`. Venues like Mystic Theatre and HopMonk use this platform for ticketing. |
| **BoardDocs** | Used by some cities for agenda publishing (e.g., `go.boarddocs.com/nc/raleigh/`). No public calendar API; LlamaIndex has a reader but it's for document extraction, not event feeds. |
