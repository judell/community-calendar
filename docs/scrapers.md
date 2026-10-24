# Reusable Scrapers

## MaxPreps (`scrapers/maxpreps.py`) — High School Athletics

```bash
python scrapers/maxpreps.py --school petaluma-trojans -o events.ics
python scrapers/maxpreps.py --school casa-grande-gauchos -o events.ics
python scrapers/maxpreps.py --url "https://www.maxpreps.com/ca/davis/davis-blue-devils/events/" --name "Davis High" -o events.ics
```

## GrowthZone (`scrapers/growthzone.py`) — Chamber of Commerce

```bash
python scrapers/growthzone.py --site petalumachamber -o events.ics
```

## Library Intercept (`scripts/library_intercept.py`)

```bash
python scripts/library_intercept.py --location petaluma -o library.ics
```

## Elfsight Calendar (`scrapers/lib/elfsight.py`)

For sites using Elfsight Event Calendar widget. See `scrapers/sportsbasement.py` for example.

## Legistar (`scrapers/legistar.py`) — City Government Meetings

```bash
python scrapers/legistar.py --client santa-rosa -o events.ics
python scrapers/legistar.py --client santa-rosa --source "City of Santa Rosa" -o events.ics
```

For cities using Legistar for agenda management. Client name is from the Legistar URL (e.g., `santa-rosa.legistar.com` → `santa-rosa`). Uses the Legistar WebAPI with OData queries for future events.

**Discovery:** Try `curl -s "https://webapi.legistar.com/v1/{client}/events" | head -50`. If it returns JSON, the client works. Common client names: city slug (`santa-rosa`), county slug (`wake`, `durhamcounty`), or town name (`chapelhill`).

**Gotcha:** Some cities have a `{city}.legistar.com` web UI but a broken API (e.g., Raleigh returns "LegistarConnectionString not set up"). These cities use Granicus for video but not Legistar for legislative data. Always test the API before adding to the workflow.

## Guild.host (`scrapers/guildhost.py`) — Tech Community Events

```bash
python scrapers/guildhost.py --group civic-tech-toronto --name "Civic Tech Toronto" -o cities/toronto/guildhost_civic_tech.ics
```

Guild.host is a community platform used mainly by **tech-focused groups** (JavaScript meetups, civic tech, DevTools, etc.). No ICS feeds — it's a JS-rendered SPA, but individual event pages have clean JSON-LD `Event` schema. The scraper fetches the listing page, extracts event slugs, then parses JSON-LD from each event page. Handles mixed physical + virtual locations.

**Discovery:** `site:guild.host "{city}"` — the platform has no location-based search. Most useful for cities with active tech scenes (Toronto, Montreal, London, Amsterdam). For a typical non-tech city, expect zero results.

## Songkick (`scrapers/songkick.py`) — Music Venue Showtimes

```bash
python scrapers/songkick.py --url "https://www.songkick.com/venues/32209-wellmont-theater" --name "Wellmont Theater" -o events.ics
```

Extracts `MusicEvent` JSON-LD from any Songkick venue page. Artists push their own tour dates to Songkick, so this gives you artist-sourced data in a single HTTP request — no bot protection to deal with, no pagination needed. See [platforms.md](platforms.md#songkick) for discovery strategy.

## Montclair Film (`scrapers/montclair_film.py`) — Film Showtimes via JSON-LD subEvents

```bash
python scrapers/montclair_film.py -o cities/montclair/montclair_film.ics
```

Montclair Film uses WordPress with a groundplan-pro plugin. The listing page at `/all-event/` links to ~15 current films; each film page has JSON-LD with a `subEvent` array of individual screenings. This is a site-specific scraper but illustrates the **listing page + JSON-LD** pattern: discover URLs from a listing page, then extract structured data from each. 16 fetches yield 128 screenings.

## Sweetwater Music Hall (`scrapers/sweetwater.py`) — RSS Feed + JSON-LD

```bash
python scrapers/sweetwater.py -o cities/santarosa/sweetwater.ics
```

Sweetwater's WordPress site has an RSS feed at `/events/feed/` with ~90 items. Each item links to an event page with clean JSON-LD (`startDate`, location, etc.). The RSS `pubDate` is the **publish date**, not the event date, so we must fetch individual pages for accurate dates.

**Limiting strategy for listing-page + per-page scrapers:** When a listing page (RSS, sitemap, index page) has many items but most are past events, filter before fetching individual pages. Sweetwater's scraper skips RSS items with `pubDate` older than 60 days — this cut 90 fetches to ~49 while still capturing all future events. The same principle applies to any scraper that discovers URLs from a listing and then fetches each one: find a cheap signal (publish date, URL pattern, list position) to skip items that are almost certainly past, and only pay the per-page fetch cost for likely-future events.

## Bibliocommons (`scrapers/lib/bibliocommons.py`) — Library Event Platforms

Reusable base for public-library systems on Bibliocommons gateway APIs.

Example (Toronto Public Library):

```bash
python scrapers/toronto_public_library.py -o events.ics
```

To create a new city/library scraper, subclass `BibliocommonsEventsScraper` and set:

- `library_slug` (e.g., `tpl`)
- `timezone`
- optional filters like `audience_ids`, `type_ids`, `program_ids`, `language_ids`

## GoDaddy Calendar (`scrapers/lib/godaddy.py`) — GoDaddy Website Builder

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


if __name__ == "__main__":
    MyVenueScraper.main()
```

## Mobilize.us (`scrapers/mobilize.py`) — Civic and Political Organizing

Mobilize.us hosts event pages for political and civic organizations. Each organization has a public page (e.g., `mobilize.us/indivisiblesonomacounty/`) that embeds event data as JSON in `window.__MLZ_EMBEDDED_DATA__`. The scraper extracts this data — no API key needed.

```bash
python scrapers/mobilize.py --url "https://www.mobilize.us/indivisiblesonomacounty/" --name "Indivisible Sonoma County (Mobilize)" --output cities/santarosa/mobilize_indivisible_sonoma.ics
```

Events often have multiple timeslots (recurring phone banks, weekly protests, etc.) — each timeslot becomes a separate calendar event. The scraper handles virtual events, location data, and event images.

**Discovery:** Search `site:mobilize.us "{city name}"` or `site:mobilize.us "{county name}"` to find organizations in a given area.

**Note:** Mobilize.us appears to have a public API at `api.mobilize.us/v1/` but we could not find the correct organization endpoint for specific groups. The embedded-data approach works reliably. If you find a working API pattern, prefer it over HTML parsing.

## Tribe Events Calendar REST (`scrapers/lib/tribe_events.py`, `scrapers/tribe_rest.py`) — WordPress

WordPress sites running The Events Calendar ("Tribe") plugin expose a JSON API at `/wp-json/tribe/events/v1/events/`, which often works when the site's ICS export is blocked or returns an empty body.

```bash
# Parameterized: one site per invocation
python scrapers/tribe_rest.py --api-base "https://example.org" --name "Example Venue" \
  --timezone America/Indiana/Indianapolis --output cities/bloomington/example.ics
```

Two entry points share the same fetch behavior:

- `scrapers/lib/tribe_events.py` (`TribeEventsScraper`) — subclass and set `api_url` for site-specific parsing (e.g. `scrapers/bloomington_symphony.py`).
- `scrapers/tribe_rest.py` (`TribeRestScraper`) — parameterized, driven by `--api-base`; used by Hard Truth Distilling Co., Upland Brewing, Boys & Girls Club, and Bloomington Community Band. `--user-agent` overrides the UA for hosts that 403 the default.

**Failure behavior:** if the *first* page cannot be fetched — HTTP error, network error, or unparseable JSON — the run fails non-zero, so feed-health reports a scraper failure instead of a quiet calendar. A first page returning HTTP 200 with an empty `events` array is a genuinely dormant calendar and still writes a valid-empty calendar. A failure *after* the first page keeps the pages already fetched; that partial set then becomes the source's whole output, so the unfetched events are swept from the database until the next clean run. The 50% partial-load check warns about such a source but does not preserve its rows — a truncated run and real churn look the same at that layer (ADR 0017).
