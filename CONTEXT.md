# Community Calendar Context

This document captures the domain language and key concepts for the community calendar project.

## Overview

A comprehensive community event aggregator that scrapes and combines events from hundreds of sources (venues, organizations, Meetup groups, government agencies) into a single searchable calendar per city. The project values **complete coverage over curation** — long-tail events (book clubs, neighborhood cleanups, craft meetups) are the target, not just major venues.

**Current cities:** Bloomington, IN (with Santa Rosa, Davis, Petaluma, and Toronto in the upstream repo)

**Live app:** https://judell.github.io/community-calendar/ (XMLUI frontend → Supabase backend)

## Language

**Database test**:
A test that verifies database behavior against a disposable local project database.
_Avoid_: SQL unit test, production test

**Static chrome check**:
File-content assertions over declarative markup (`.xmlui`/theme files) with no runtime execution. Runs under vitest in `tests/js/`, distinct from browser groups in `xmlui/test.html`.
_Avoid_: JS unit test, integration test (when referring to this script type)

**Vitest seam test**:
Behavioral assertions over the pure date-window/helpers seam (`date-windows.js`, `helpers.js`) loaded via a `vm` stub harness in `tests/js/`. Hand-computed literals, never the engine's own output, so the test can disagree with the code.
_Avoid_: bare-node script (the pre-vitest form), browser test (when referring to this seam type)

**Browser group**:
A served-file group in `xmlui/test.html` (Date tabs, Brand chrome, Content links) asserting over fetched shipped files in a real browser. Gated in PR CI via Playwright (`pnpm playwright test`); the vitest files are fast mirrors, not the source of truth.
_Avoid_: static chrome check (when referring to the browser execution)

**Source**:
A venue, organization, group, or government body that contributes events to the calendar. The user-facing concept — what a calendar visitor sees (e.g., "Buskirk-Chumley Theater").
_Avoid_: Venue, organization (when referring to the calendar entry point)

**Feed**:
The technical mechanism that delivers events from a source — an ICS URL or a scraper command. One source has one feed. The implementation layer — what the pipeline operates on.
_Avoid_: URL, scraper (when referring to the abstraction)

**Source id**:
The `.ics` filename stem a feed's build produces — a scraper's output filename, or the slug of an ICS URL. The build stamps it on every event as `X-SOURCE-ID` and records it on the feed row in `feeds.source_ids`, which is a history because a feed's URL can change. Stable per feed, unlike the display `source`, which becomes a comma-joined aggregate after a Merge. A stem that two same-city feeds share identifies neither exclusively; retirement keeps those rows.
_Avoid_: Source name, slug (when the identity is meant)

**Feed-owned survivor**:
A Merge survivor belongs to the feed whose copy won the Merge: its `source_id` is that feed's. Retiring that feed deletes the survivor; retiring a member feed does not, because the survivor's `source_id` names another feed and its saved picks must stay.
_Avoid_: Primary source (when ownership is meant)

**Quiet source**:
A source whose build wrote a valid calendar with no upcoming events — a genuinely dormant calendar, not a problem to fix. A quiet source is a ran source only when its scraper declared it reached its source; a valid-empty calendar from a scraper that never reached it is a False quiet, which is a failure.
_Avoid_: Empty feed, broken source

**False quiet**:
A valid-empty calendar produced by a scraper that never reached its source; it looks like a Quiet source and would be swept like one, so the scraper fails instead of writing it.
_Avoid_: Quiet source (when the source was never reached), empty feed

**Ran source**:
A source whose ingestion succeeded in a build run — a scraper that exited 0, declared it reached its source, and left a parseable calendar, or a feed fetch that returned a valid ICS body — regardless of how many events survive later filtering. The build lists these in `cities/<city>/ran_sources.txt`, and the stale sweep deletes only from them. A quiet source and a source the geo or horizon filter emptied are both ran; a failed source is not.
_Avoid_: Successful source (when ingestion success is meant), processed source

**Fork**:
This repository is a *hard fork* of the upstream community-calendar project (judell/community-calendar). It intentionally diverges from upstream — origin/main contains Bloomington-only customizations, scrapers, and infrastructure that are not present in upstream/main. origin/main ≠ upstream/main by design.
_Avoid_: Tracking fork, downstream mirror

**Wall-clock time**:
A datetime with no timezone, meaning "the time shown on a clock in the venue's local zone". Scrapers parse these; the pipeline attaches a zone later.
_Avoid_: Naive datetime, local time

**Absolute instant**:
A timezone-aware datetime denoting one specific moment in time, independent of any local clock.
_Avoid_: UTC time, aware datetime

**City timezone**:
The IANA zone a city's events default to when a source states none. Read from `cities/{city}/city.conf` (`# timezone:`), falling back to `America/Los_Angeles`.
_Avoid_: Local timezone, calendar timezone

**Event timezone (TZID)**:
The IANA zone an individual event declares via an ICS `TZID` parameter. Overrides the city timezone for that event.
_Avoid_: Event tz, source timezone

**Date window**:
The absolute `[start, end)` interval the calendar is currently filtered to, resolved in the city timezone. What the list, pager, and URL all reflect.
_Avoid_: Date filter, day offsets

**Preset**:
A named rule that resolves to a date window relative to the day it is opened (Today, Tonight, Tomorrow, This weekend, Next 7 days, This month, Custom, All). Rolling presets stay evergreen; Custom carries exact dates.
_Avoid_: Tab, quick filter

**Date tab**:
The control in the date-tab strip that commits one preset or opens the Custom flow. Exactly one is pressed at a time, announced as such to assistive technology; Custom stays pressed while its picker flow is open, even before a range commits.
_Avoid_: Preset (the rule the tab commits), quick filter

**Commit**:
The moment a chosen window becomes active: the list re-filters, the pager resets, and the URL syncs. Discrete picks commit instantly; continuous gestures commit on release/confirm, never per tick.
_Avoid_: Apply, select (when meaning the committed state)

**Horizon**:
The end of the prefetched event set: the configured scrape window, about 90 days out in production. Windows past it clamp and label the truncation; the calendar running out is distinct from the filter matching nothing.
_Avoid_: Max date, data end

**Clamping**:
Moving a range start earlier than today forward to today, rewriting the URL so reload is stable. Never a silent empty from a stale date.
_Avoid_: Snapping, correcting

**Truncation**:
Labeling when a window extends past the horizon so the visitor knows the calendar ended, not the filter.
_Avoid_: Cutoff (when meaning horizon), capping

**Listing**:
One row from one source: a single source's rendering of an event. Two sources carrying one real-world event produce two listings.
_Avoid_: Event (when the source's copy is meant), record

**Merge**:
The destructive band of the confidence route: listings that are certainly one event (identical cleaned full title, same start instant, compatible locations present on both sides — a stricter location test than Group's, since a shared town or state is not evidence, a pair with no street number needs three shared tokens rather than two, and a shared generic token is not enough when neither side names a town) collapse to one surviving row; the other sources fold into it. Merge is an equivalence class over the exact-title relation alone — it never propagates through a similarity edge, so no threshold change can delete a row.
_Avoid_: Dedupe, fuzzy match

**Group**:
The non-destructive band: listings that look like one event (similarity at or above the threshold, same start instant, compatible locations) but are not certain. Every row is kept; the members share a `duplicate_group` id so consumers render one card from one decision.
_Avoid_: Cluster, collapse

**Separate**:
The route's default and its authoritative outcome: listings left apart are never re-collapsed by a downstream fallback. A NULL `duplicate_group` means the route left the row alone — one row is one group.
_Avoid_: Unmatched, rejected

**Duplicate group**:
The opaque, versioned id (format `cr2-<hash>`) the route assigns to every surviving member of one Group. Deterministic over the sorted member `source_uid`s within a route version; it changes when membership changes or `ROUTE_VERSION` is bumped. No consumer may persist it as identity (picks stay on `event_id` plus the `merged_ids` union).
_Avoid_: Cluster id, dedupe key

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
- For **scrapers**, `BaseScraper.create_event()` sets `X-SOURCE` from the scraper class's `name` attribute (not a `--name` command-line argument)
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

### Timezone Handling

Events flow through the pipeline as **wall-clock times** and become **absolute instants** only at the ICS→JSON boundary:

1. **Scrapers** emit `DTSTART`/`DTEND` one of two ways. When the source site states a clock time but no zone (the common case), the value is emitted **naive (wall-clock)** — no zone can be attached at scrape time. When the source declares a known zone (e.g. an event-level `timezone` field), the scraper **attaches it directly** (`dtstart.replace(tzinfo=...)`) and the ICS output carries that `TZID`. Both paths flow to the ICS→JSON boundary below.
2. **Feeds** carry their own `TZID`/`Z`/`VTIMEZONE` where the publisher provides one.
3. **`ics_to_json.py`** stamps the **event timezone (TZID)** when present, else the **city timezone** from `city.conf` (default `America/Los_Angeles`), producing an offset-qualified ISO string. A `Z`-suffixed time is converted to the city zone.
4. All-day events anchor to midnight in the city zone; a weekly wall-clock event stays at the same clock time across a DST transition.

`now()`/`today()` in the pipeline use UTC (`datetime.now(timezone.utc)`), relying on the code's ±1-day tolerance rather than a city-local "today".

### Deduplication

One build-time **confidence route** (in `scripts/ics_to_json.py`) decides Merge / Group / Separate for every cleaned listing and stores the result as `events.duplicate_group`. Consumers do not recompute grouping: the `deduplicated_events` materialized view, the main calendar, the dashboard tiles, saved picks, and the RSS feed all collapse from that one stored id. `source_uid` (unique per source, enforced by a unique index) drives UID-level de-duplication upstream in `combine_ics.py`; the route is the only authority on whether two *different* listings are one event. See [ADR 0013](docs/adr/0013-confidence-route-merge-group-separate.md).

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
Scraper (python scrapers/example.py -o cities/{city}/example.ics)
  ↓
BaseScraper.create_event() (sets X-SOURCE from the scraper class's `name` attribute)
  ↓
cities/{city}/example.ics (with X-SOURCE headers)
  ↓
[same as feed flow: combine_ics.py → ics_to_json.py → load-events]
```

### Database Schema (Key Tables)

- **events** — All calendar events (title, start_time, location, description, source, category, city, source_uid). `load-events` upserts by `source_uid`, then sweeps stale rows scoped to the `source_id`s present in the payload, so a source that failed to produce output keeps its rows.
- **feeds** — Source registry (url, name, city, status, feed_type, scraper_cmd, source_ids)
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

Scraper execution is DB-first: the build runs whatever active scraper rows
exist in the `feeds` table, so the workflow carries no per-source lines.

1. Write scraper in `scrapers/` (inherit from `BaseScraper` or use helpers)
2. Run `python scripts/add_scraper.py {scraper} {city} "Source Name"` — this:
   - Tests the exact command being registered (aborts if the test fails)
   - Appends the entry to `pending_feeds.txt`, staging the `feeds` table row
     (validated at insert time; the DB-first runner executes it that build)
3. Update `cities/{city}/SOURCES_CHECKLIST.md`
4. Commit and push

**Do NOT** skip `add_scraper.py` — it tests the command and writes the
registration metadata the DB-first runner consumes; hand-writing the entry
skips that test. See `CONTRIBUTING.md` for the full contract.

### Adding a New City

1. Create `cities/{city}/` directory with `SOURCES_CHECKLIST.md`
2. Run source discovery (Meetup, WordPress `?ical=1`, Tockify, topical searches)
3. Add scrapers and feeds
4. Update workflow YAML (add city to locations list, add scrape section, add commit step)
5. Update UI (two places: `index.html` cityNames map + `Main.xmlui` city picker buttons)
6. Optional: create `cities/{city}/city.conf` for geo-filtering
7. Commit and push

No edge-function change is needed: the workflow POSTs each city's payload to `load-events`, which takes one city per request.

### Edge Function Gotcha

Redeploying any Supabase edge function via the Supabase MCP tool resets "Require JWT" to ON. The workflow calls `load-events` with the anon key, so after redeploying you must **manually turn off "Require JWT"** in the Supabase dashboard or the build will fail. That JWT check is not what protects `load-events` — the `x-load-events-secret` header is (GHSA-qmc5-6cfg-38p7); without the `LOAD_EVENTS_SECRET` project secret the function returns 500 and writes nothing.

### Known Platform Limitations

- **Facebook Events** — No public API since 2018
- **Bandsintown** — Behind Cloudflare, API requires approval, no venue endpoint
- **Granicus video** — Backward-looking only (archived videos, not upcoming events)
- **SeeTickets/Eventim US** — No public API, affiliate account required
- **Cloudflare-protected sites** — Challenge pages block scrapers (look for ticketing platform indirection)
