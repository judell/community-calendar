# Community Calendar Context

This document captures the domain language and key concepts for the community calendar project.

## Overview

A comprehensive community event aggregator that scrapes and combines events from hundreds of sources (venues, organizations, Meetup groups, government agencies) into a single searchable calendar per city. The project values **complete coverage over curation** — long-tail events (book clubs, neighborhood cleanups, craft meetups) are the target, not just major venues.

**Current cities:** Bloomington, IN (with Santa Rosa, Davis, Petaluma, and Toronto in the upstream repo)

**Live app:** https://judell.github.io/community-calendar/ (XMLUI frontend → Supabase backend)

## Key Concepts

### Event Sources

Two types of sources feed the calendar:

1. **ICS Feeds** — Direct calendar URLs that need no scraping (e.g., `https://venue.com/events/?ical=1`, Meetup ICS feeds, Tockify feeds). These are stored in the Supabase `feeds` table as `feed_type='ics_url'` and downloaded by `download_feeds.py` during the CI build.

2. **Scrapers** — Python scripts in `scrapers/` that extract events from sites without ICS feeds. They inherit from base classes in `scrapers/lib/` (e.g., `GoDaddyScraper`, `BibliocommonsEventsScraper`) or use helper libraries (`jsonld.py`, `tribe_events.py`). Scrapers are registered in the `feeds` table as `feed_type='scraper'` with a `scraper_cmd` field, and are invoked by GitHub Actions during builds.

### Cities

Each city has:
- A directory under `cities/{city}/` containing generated `.ics` files from scrapers
- A `SOURCES_CHECKLIST.md` tracking discovery progress (implemented sources, pending sources, non-starters)
- Optional `city.conf` for geo-filtering (if events from neighboring towns need filtering)
- Entries in the UI (`index.html` cityNames map + `Main.xmlui` city picker buttons)
- An edge function URL in `supabase/functions/load-events/index.ts`

### Source Attribution

Every event has a `source` field that flows through this pipeline:

```
Scraper/Feed ICS  →  combine_ics.py  →  ics_to_json.py  →  Supabase DB  →  EventCard.xmlui
   X-SOURCE           X-SOURCE           source column       source column    italic "Source: X"
```

- **X-SOURCE** is an ICS header carrying the human-readable source name ("Bohemian Events", "Davis High Athletics", etc.)
- For **feeds**, `download_feeds.py` injects `X-SOURCE` and `X-SOURCE-URL` into every VEVENT at download time
- For **scrapers**, `BaseScraper.create_event()` sets `X-SOURCE` from the `--name` command-line argument
- `EventCard.xmlui` line 26 renders `source` as an italic line below the event description

**Important:** Do NOT put "Source: X" text in event descriptions — it causes duplicate display.

### Feeds Table (Source of Truth)

The Supabase `feeds` table is the authoritative registry of all sources:

- **ICS feeds:** `feed_type='ics_url'`, has `url` + `name` + optional `fallback_url`
- **Scrapers:** `feed_type='scraper'`, has `scraper_cmd` (e.g., `python scrapers/legistar.py --client santa-rosa`)
- **Status:** `active` (included in builds), `pending` (awaiting approval), `removed` (archived)

During builds, `download_feeds.py` queries active feeds and `export_feeds_txt.py` regenerates `feeds.txt` from the DB. `feeds.txt` is a compatibility layer — the DB is the source of truth.

### pending_feeds.txt

Each city has a `cities/{city}/pending_feeds.txt` file — a staging area for contributors without database access to propose new feeds. During the build, entries are moved from `pending_feeds.txt` into the `feeds` table, then the file is cleared back to its template. This is a temporary inbox, not permanent storage.

### Event Classification

Events are auto-classified into categories ("Music & Concerts", "Arts & Culture", "Sports & Recreation", etc.) by Claude Haiku:

- `classify_events_json.py` runs in CI on `events.json` files
- `classify_events_anthropic.py` operates directly on Supabase for backfills
- Categories are title-deduped (recurring "Tuesday Trivia Night" instances classified once)
- The `category_overrides` table stores curator manual corrections, which also serve as few-shot examples for future classifications

### Geo-Filtering

Optional per-city. Some feeds include events from neighboring towns outside the target area. A `cities/{city}/city.conf` file defines lat/lon boundaries:

```bash
CENTER_LAT=38.4404
CENTER_LON=-122.7141
RADIUS_MILES=15
```

`scripts/geo_filter.py` reads this config and filters `events.json`. If no `city.conf` exists, all events pass through.

### Deduplication

Events are deduplicated by `source_uid` (a unique ID from the source, stored in the `events` table with a unique index). When the same event appears in multiple sources (e.g., a concert on both the venue's calendar and Songkick), the first-seen version is kept.

## Business Rules

### Discovery Philosophy: Complete Coverage, Not Curation

1. **Long-tail events matter** — Book clubs, craft meetups, neighborhood events are the target, not just major venues
2. **Schools are gold mines** — Athletics, theater, concerts, parent nights
3. **Churches and community centers** — Special events (not weekly services)
4. **If in doubt, add it** — Missing events is worse than having too many

### When to Add a Source

- Has future public events (not just archives or past events)
- Events are for the general public (not member-only or private)
- Has a machine-readable feed (ICS, JSON-LD, API) OR can be scraped reliably
- NOT behind hard bot protection (Cloudflare challenges, login walls) unless there's a workaround

### When to Write a Scraper vs Use a Feed

- **Prefer feeds** — ICS feeds are maintenance-free; scrapers break when sites change
- **Write a scraper when:**
  - No ICS feed exists and the platform has no standard one
  - The site has structured data (JSON-LD, embedded JSON, clean APIs) that's stable
  - Ticketing platform indirection (venue site is hard to scrape, but Eventbrite/Songkick has clean data)

### Source Attribution Rules

- `X-SOURCE` header is the single source of truth for attribution
- Source names should be human-readable and specific ("Sweetwater Music Hall", not "sweetwater.ics")
- Never put "Source: X" text in event descriptions — the UI renders it separately
- For feeds, `download_feeds.py` injects `X-SOURCE` at download time
- For scrapers, `BaseScraper.create_event()` or manual `X-SOURCE` addition handles it

### Scraper Hygiene: Minimize Fetches

When a scraper must fetch individual event pages (listing + detail pattern):

1. **Prefer APIs** that return dates in the listing (no detail fetch needed)
2. **Filter at listing stage** — use publish dates, URL patterns, or page position to skip past events
3. **Cap pagination** — bound worst-case fetch count
4. **Be a good citizen** — don't hammer source sites

## Component Relationships

### Build Pipeline (GitHub Actions)

```
1. Checkout repo
2. Download ICS feeds (download_feeds.py reads feeds table, injects X-SOURCE)
3. Run scrapers (workflow YAML invokes python scrapers/*.py for each city)
4. Combine ICS files (combine_ics.py merges all .ics → cities/{city}/combined.ics)
5. Convert to JSON (ics_to_json.py → cities/{city}/events.json)
6. Classify events (classify_events_json.py adds category field)
7. Load into Supabase (supabase/functions/load-events/index.ts edge function)
8. Commit and push (updated events.json files, feeds.txt)
9. Deploy to GitHub Pages (xmlui/ directory)
```

### Frontend (XMLUI App)

```
index.html (redirector)
  ↓
xmlui/index.html (entry point)
  ↓
Main.xmlui (city picker OR calendar view based on ?city= param)
  ↓
components/EventCard.xmlui (individual event cards)
  ↓
Supabase queries (SELECT * FROM events WHERE city = ?)
```

**URL pattern:** `index.html?city=bloomington` sets `window.cityFilter` and `window.cityName`

### Data Flow: Feed → Database

```
Feeds table (Supabase)
  ↓
download_feeds.py (queries active feeds, downloads ICS, injects X-SOURCE)
  ↓
cities/{city}/feed_name.ics
  ↓
combine_ics.py (merges all .ics)
  ↓
ics_to_json.py (parses ICS → JSON, extracts X-SOURCE → source field)
  ↓
cities/{city}/events.json
  ↓
load-events edge function (upserts to Supabase events table by source_uid)
```

### Data Flow: Scraper → Database

```
Scraper (python scrapers/example.py --name "Source Name" -o cities/{city}/example.ics)
  ↓
BaseScraper.create_event() (sets X-SOURCE from --name)
  ↓
cities/{city}/example.ics (with X-SOURCE headers)
  ↓
[same as feed flow: combine_ics.py → ics_to_json.py → load-events]
```

### Database Schema (Key Tables)

- **events** — All calendar events (title, start_time, location, description, source, category, city, source_uid)
- **feeds** — Source registry (url, name, city, status, feed_type, scraper_cmd)
- **picks** — User-saved events (user_id, event_id)
- **category_overrides** — Curator manual category corrections (source_uid, category)
- **event_enrichments** — Audio capture transcripts and enrichments (event_id, transcript)

## Important Patterns

### Reusable Scraper Base Classes

- **`scrapers/lib/base.py`** — `BaseScraper` with `create_event()`, `write_ics()`, CLI arg parsing
- **`scrapers/lib/bibliocommons.py`** — Library event platforms (subclass sets `library_slug`, `timezone`)
- **`scrapers/lib/godaddy.py`** — GoDaddy Website Builder calendar widget (subclass sets UUIDs)
- **`scrapers/lib/tribe_events.py`** — WordPress Tribe Events REST API client
- **`scrapers/lib/jsonld.py`** — JSON-LD Event/MusicEvent extraction helpers

### Platform-Specific Patterns

| Pattern | Description |
|---------|-------------|
| **Meetup ICS** | `https://www.meetup.com/{group-slug}/events/ical/` |
| **WordPress Tribe** | `{domain}/events/?ical=1` OR `/wp-json/tribe/events/v1/events/` if ICS blocked |
| **Tockify** | `https://tockify.com/api/feeds/ics/{CALENDAR_ID}` |
| **Legistar** | `https://webapi.legistar.com/v1/{client}/events` (try city slugs) |
| **Songkick** | `https://www.songkick.com/venues/{ID}-{slug}` (JSON-LD MusicEvent) |
| **Listing + Detail** | Fetch listing page → extract event URLs → parse individual pages (minimize with date filtering) |

### Source Metadata Flow

```
Feeds table (DB)
  ↓
export_feeds_txt.py
  ↓
feeds.txt (generated, for compatibility)
  ↓
combine_ics.py reads as fallback display-name map
```

DO NOT manually edit `feeds.txt` or the legacy `SOURCE_NAMES`/`SOURCE_URLS` dicts in `combine_ics.py`. The `feeds` table is the source of truth.

### Adding a New Scraper (Workflow)

1. Write scraper in `scrapers/` (inherit from `BaseScraper` or use helpers)
2. Run `python scripts/add_scraper.py {scraper} {city} "Source Name"` — this:
   - Adds workflow invocation line (GitHub Actions YAML)
   - Adds metadata to `pending_feeds.txt` (staging for `feeds` table)
3. Update `cities/{city}/SOURCES_CHECKLIST.md`
4. Commit and push

**Do NOT** skip `add_scraper.py` — manual edits miss one half of the integration.

### Adding a New City

1. Create `cities/{city}/` directory with `SOURCES_CHECKLIST.md`
2. Run source discovery (Meetup, WordPress `?ical=1`, Tockify, topical searches)
3. Add scrapers and feeds
4. Update workflow YAML (add city to locations list, add scrape section, add commit step)
5. Update UI (two places: `index.html` cityNames map + `Main.xmlui` city picker buttons)
6. Add city to `load-events` edge function (`EVENTS_URLS` map)
7. Optional: create `cities/{city}/city.conf` for geo-filtering
8. Commit and push

### Edge Function Gotcha

Redeploying any Supabase edge function via the Supabase MCP tool resets "Require JWT" to ON. The workflow calls `load-events` with the anon key, so after redeploying you must **manually turn off "Require JWT"** in the Supabase dashboard or the build will fail.

### Known Platform Limitations

- **Facebook Events** — No public API since 2018
- **Bandsintown** — Behind Cloudflare, API requires approval, no venue endpoint
- **Granicus video** — Backward-looking only (archived videos, not upcoming events)
- **SeeTickets/Eventim US** — No public API, affiliate account required
- **Cloudflare-protected sites** — Challenge pages block scrapers (look for ticketing platform indirection)
