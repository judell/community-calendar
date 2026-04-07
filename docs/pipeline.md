# Event Pipeline

## Event Sources

### Discovery Philosophy

**We want COMPLETE coverage, not curated coverage.** This means:

- **Long-tail events matter** - A book club with 5 members, a small craft meetup, a neighborhood cleanup - these ARE our target. Don't skip sources just because they seem niche or low-volume.
- **Schools are gold mines** - High schools and colleges have athletics, theater productions, band concerts, art shows, parent nights, and graduations.
- **Churches and community centers** - Special events like concerts, fundraisers, and community dinners are valuable even if weekly services aren't.
- **Youth sports leagues** - Little League, youth soccer, swim teams often have public calendars.
- **If in doubt, add it** - We can always filter later. Missing events is worse than having too many.

### Source Types

**ICS feeds** (type `ics_url`) are preferred when available. Many venues and organizations publish standard iCalendar feeds.

**Scrapers** (type `scraper`) are a fallback for sources that don't provide ICS feeds. Generic/reusable scrapers work across multiple sites:
- `maxpreps.py` - High school athletics
- `growthzone.py` - Chamber of Commerce sites
- `squarespace.py` - Squarespace event pages
- `songkick.py` - Music venue calendars
- `ticketmaster.py` - Ticketmaster venues
- `eventbrite.py` - Eventbrite organizers

**Curator feeds** (type `curator`) are curated picks from community members via the `my-picks` edge function.

### The `feeds` Table

All sources are stored in the Supabase `feeds` table — the single source of truth. Columns:
- `city`, `url`, `name`, `status` (active/pending/removed), `feed_type` (ics_url/scraper/curator), `scraper_cmd`

The Manage Feeds dialog (admin-only) reads and writes this table for ICS URL feeds. Scrapers are added via `add_scraper.py` and the workflow YAML.

`feeds.txt` files are **generated** from the `feeds` table during each build (by `export_feeds_txt.py`) for fork compatibility. Do not edit feeds.txt manually.

## Adding a Feed (ICS URL)

Use the **Manage Feeds** dialog in the app (admin calendar icon):

1. Enter the feed URL and source name
2. Click **Validate Feed** — checks for valid ICS, URL overlap with existing feeds, previews events
3. Click **Add Feed** — saves to `feeds` table with `status=pending`
4. Next build picks it up, downloads it, marks it `active`

Feeds with recurring events (RRULE) show a note that the build will expand them.

## Deleting a Feed

Use the **Manage Feeds** dialog:

1. Find the feed in the scrollable list
2. Click **Delete** — confirms, then deletes events from DB and removes the `feeds` row
3. Next build will not include it; `feeds.txt` will be regenerated without it

## Adding a Scraper

Use the `add_scraper.py` script:

```bash
python scripts/add_scraper.py myscraper santarosa "My Source Name"
```

This adds the scraper to the workflow YAML, adds a display name comment to `feeds.txt`, and adds an entry to the `feeds` table. The `feeds.txt` entry provides the display name that `combine_ics.py` uses for the `X-SOURCE` header.

## Build Pipeline

The workflow in `.github/workflows/generate-calendar.yml` runs daily or on manual trigger.

**Per-city steps:**

1. **Run scrapers** — hardcoded commands in the workflow YAML
2. **Download live feeds** — `download_feeds.py` queries the `feeds` table for active+pending `ics_url`/`curator` feeds, downloads each, injects `X-SOURCE` headers. Falls back to `feeds.txt` if DB not available (forks). Marks pending feeds as `active` after download.
3. **Export feeds.txt** — `export_feeds_txt.py` regenerates `feeds.txt` from the `feeds` table for fork compatibility
4. **Combine ICS** — `combine_ics.py` merges all `.ics` files, deduplicates, applies geo filtering. Display names come from `feeds.txt` (parsed at runtime) for scrapers, and from `X-SOURCE` headers (injected by `download_feeds.py`) for live feeds.
5. **Convert to JSON** — `ics_to_json.py` converts combined ICS to JSON with fuzzy title clustering
6. **Classify events** — `classify_events_anthropic.py` categorizes uncategorized events via Claude Haiku
7. **Upload to Supabase** — `load-events` edge function upserts events
8. **Refresh source names** — `refresh_source_names()` RPC updates the `source_names` cache (legacy, being replaced by `get_source_counts()` RPC)
9. **Commit metadata** — auto-commits `feeds.txt`, `cities.json`, version info

## Source Attribution

Source names flow through the pipeline as `X-SOURCE` ICS headers → `source` column in the events table → displayed by EventCard in the app.

Display names are determined by:
- **Scrapers with `--name` arg**: scraper sets `X-SOURCE` directly
- **Scrapers without `--name`**: `combine_ics.py` parses `feeds.txt` for the `# Display Name` comment above the `.ics` file entry
- **Live feeds**: `download_feeds.py` injects `X-SOURCE` from the `feeds` table `name` column
- **Legistar scrapers**: `--source` arg sets `X-SOURCE` directly

The old `SOURCE_NAMES` dict in `combine_ics.py` has been removed. `feeds.txt` (generated from the `feeds` table) is the source of truth for display names.

## Deduplication

Two rounds:

1. **Cross-source dedup** — Events with identical title + date from different sources are merged. The non-aggregator version is kept, and `X-SOURCE` headers are merged (e.g., "North Bay Bohemian, Press Democrat").

2. **Fuzzy dedup** — Clusters events within the same timeslot using token-set string similarity (threshold 0.85). Events at different locations are never clustered. Uses union-find to assign a shared `cluster_id`.

## Cities

- `santarosa` - Santa Rosa, CA (America/Los_Angeles)
- `bloomington` - Bloomington, IN (America/Indiana/Indianapolis)
- `davis` - Davis, CA (America/Los_Angeles)
- `petaluma` - Petaluma, CA (America/Los_Angeles)
- `toronto` - Toronto, ON (America/Toronto)
- `raleighdurham` - Raleigh-Durham, NC (America/New_York)
- `montclair` - Montclair, NJ (America/New_York)
- `lancaster` - Lancaster, PA (America/New_York)
