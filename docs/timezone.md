# Timezone Handling

## The two ICS timezone conventions

ICS files declare timezones in two ways. We accept both because external feeds use both.

### X-WR-TIMEZONE (calendar-level default)

```
X-WR-TIMEZONE:America/Los_Angeles

DTSTART:20250321T190000
```

The datetime `20250321T190000` is bare — no timezone info attached. The calendar-level `X-WR-TIMEZONE` header says "interpret all bare datetimes as Pacific." This is a Google Calendar convention, not part of RFC 5545. Our scraper-generated ICS files use this format because scrapers already resolve times to the correct local wall-clock time.

### VTIMEZONE + TZID (per-event)

```
BEGIN:VTIMEZONE
TZID:America/Los_Angeles
BEGIN:STANDARD
...offset rules...
END:STANDARD
BEGIN:DAYLIGHT
...offset rules...
END:DAYLIGHT
END:VTIMEZONE

DTSTART;TZID=America/Los_Angeles:20250321T190000
```

Each event carries a `TZID` parameter pointing to a timezone definition embedded in the file. This is the RFC 5545 standard. Live feeds from Google Calendar, Meetup, Eventbrite, etc. typically use this format.

### Why both matter

A single city calendar can contain events from many sources with different conventions. Santa Rosa's `feeds.txt` pulls from ~80 sources. Most use `X-WR-TIMEZONE` or `TZID=America/Los_Angeles`, but some — especially Eventbrite and Meetup — emit `TZID=America/New_York` because their platform defaults to Eastern time. If we ignore that TZID and stamp everything as Pacific, those events display 3 hours wrong.

Real TZID diversity from our feeds (via `report.py` TZID inventory):

- **Bloomington** (city tz: `America/Indiana/Indianapolis`): 10,482 events with `America/New_York`, 1,767 with `America/Indiana/Indianapolis`, 120 with `America/Los_Angeles`
- **Toronto**: 13 distinct TZIDs including `America/Halifax`, `Europe/Berlin`, `Australia/Sydney`, `UTC`
- **Santa Rosa**: `America/New_York`, `America/Dawson`, `America/Vancouver` alongside the expected `America/Los_Angeles`

## The pipeline, step by step

Here's what happens to a datetime as it flows from source to screen:

### Step 1: Source → ICS file

**Scrapers** (`scrapers/lib/base.py`): Each scraper has a `timezone` class attribute (e.g., `timezone = "America/New_York"`). BaseScraper strips `tzinfo` from datetime objects and sets `TZID` as a string parameter. Output looks like:

```
DTSTART;TZID=America/New_York:20250321T190000
```

**Live feeds** (`scripts/download_feeds.py`): Downloaded as-is. No timezone processing. Whatever the source emits is what we get.

**Static feeds** (e.g., `cities/santarosa/new_world_ballet.ics`): Hand-crafted with VTIMEZONE block + TZID parameters. These can use RRULE for recurring events.

### Step 2: ICS files → combined.ics

`scripts/combine_ics.py` merges all `.ics` files in a city directory into `combined.ics`.

**RRULE expansion**: `recurring_ical_events.of(cal).between(today, window_end)` expands recurring events into individual instances within a 90-day window. This library correctly reads both VTIMEZONE/TZID and X-WR-TIMEZONE, so a weekly 7pm class stays at 7pm local even across DST transitions. After expansion, RRULE/EXDATE/RDATE properties are stripped and UIDs are mutated to make each instance standalone.

**Cutoff filtering**: Events with DTSTART before yesterday are discarded. The comparison uses `.replace(tzinfo=timezone.utc)` on naive datetimes, which is technically wrong (it labels local time as UTC) but the 24-hour buffer masks the error.

**Output**: Raw VEVENT text passes through, preserving whatever TZID parameters were on the input. No timezone conversion happens here.

### Step 3: combined.ics → events.json

`scripts/ics_to_json.py` converts the combined ICS into JSON for the database.

This is where timezone resolution happens. `extract_raw_datetime` pulls the full DTSTART/DTEND property line from each VEVENT, preserving any TZID parameter. Then `parse_ics_datetime` handles three cases:

| ICS input | What happens | Example output |
|---|---|---|
| `DTSTART;TZID=America/New_York:20250115T190000` | Uses the TZID from the property | `2025-01-15T19:00:00-05:00` |
| `DTSTART:20250115T190000` (bare) | Stamps with city timezone from `city.conf` | `2025-01-15T19:00:00-08:00` (if city is Pacific) |
| `DTSTART:20250115T200000Z` (UTC) | Converts UTC to city local time | `2025-01-15T12:00:00-08:00` (if city is Pacific) |

The output is always an ISO 8601 string with an explicit UTC offset. This is what goes into `events.json`.

### Step 4: events.json → PostgreSQL

The `load-events` edge function (`supabase/functions/load-events/index.ts`) fetches `events.json` from GitHub Pages and upserts to Supabase. No timezone processing — ISO 8601 strings pass through as-is.

PostgreSQL's `timestamptz` columns accept the offset-qualified strings and store them internally as UTC. `2025-01-15T19:00:00-05:00` and `2025-01-15T16:00:00-08:00` both become the same UTC instant.

### Step 5: PostgreSQL → browser

The database returns timestamps as UTC (with `+00:00` offset). The frontend converts for display using the city timezone from `cities.json`:

```javascript
function getCityTimezone() {
  var city = window.cityFilter;
  if (city && window._cities && window._cities[city]) {
    return window._cities[city].timezone;
  }
  return undefined;
}

// All display functions pass timeZone to Intl.DateTimeFormat:
new Date(isoString).toLocaleDateString('en-US', {
  weekday: 'short',
  timeZone: getCityTimezone()
});
```

The frontend never uses the browser's local timezone — always the city's configured timezone.

### Step 6: Manual event capture → PostgreSQL

When a user captures an event from a photo or audio (`supabase/functions/capture-event/index.ts`):

1. Frontend passes `?timezone=America/Los_Angeles` (from `cities.json`)
2. Claude extracts a naive datetime like `2025-03-23T19:00:00`
3. `applyTimezoneOffset()` computes the UTC offset for that wall-clock time in that timezone and appends it: `2025-03-23T19:00:00-07:00`
4. PostgreSQL stores it correctly

### Step 7: Enrichment (curator recurrence) → PostgreSQL

When a curator adds recurrence to an event via PickEditor, the form shows times in city-local (via `utcToLocal()`). On submit, `applyTimezoneOffset()` in `helpers.js` appends the city timezone offset before sending to the Supabase REST API. This ensures the naive form values like `2025-01-15T19:00:00` become `2025-01-15T19:00:00-08:00` before PostgreSQL sees them.

### Step 8: My Picks ICS feed

The `my-picks` edge function (`supabase/functions/my-picks/index.ts`) generates an ICS feed of a user's bookmarked events.

For **non-recurring events**: outputs UTC times with Z suffix (`DTSTART:20250327T010000Z`). The subscribing calendar app handles conversion to the user's local timezone.

For **recurring events** (those with an RRULE): outputs local times with TZID (`DTSTART;TZID=America/Los_Angeles:20250326T180000`). This is critical because RRULE `BYDAY` expansion happens relative to the DTSTART timezone. A Wednesday 6pm Pacific event stored as Thursday 1am UTC would expand `BYDAY=WE` on the wrong day if the calendar app uses UTC for expansion.

The city timezone comes from `cities.json` fetched at runtime from the repo (via `GITHUB_REPO` env var, same pattern as `load-events`), not hardcoded. The event's `city` column in the database maps to the timezone.

### Step 9: Capture-event day-of-week computation

The `capture-event` edge function (`supabase/functions/capture-event/index.ts`) pre-computes a day-of-week lookup table in the prompt:

```
Today is Sunday, 2026-03-22. The next 7 days are: Sunday = 2026-03-22, Monday = 2026-03-23, ...
```

This prevents Claude from doing day-of-week arithmetic (which it gets wrong — e.g., computing "next Wednesday" as Thursday). The model uses the lookup table directly.

## City timezone configuration

Each city's IANA timezone is stored in two places:

- `cities/<city>/city.conf` — used by Python scripts: `# timezone: America/Los_Angeles`
- `cities.json` — used by the frontend: `{ "santarosa": { "timezone": "America/Los_Angeles" } }`

`scripts/generate_cities_json.py` generates `cities.json` from the `city.conf` files.

## TZID inventory in report.json

`scripts/report.py` scans all ICS files per city and records every distinct TZID found, with event counts and source files. This surfaces cross-timezone feeds so we can verify the pipeline handles them correctly.

## Tests

`tests/test_timezone_pipeline.py` covers:

- `parse_ics_datetime`: bare, UTC, TZID-matching, TZID-mismatched, DST transitions, all-day events
- `extract_raw_datetime`: preserves TZID vs `extract_field` which strips it
- RRULE expansion: TZID preservation, DST wall-clock stability
- Full pipeline: Eastern event in Pacific city produces correct UTC instant
- `applyTimezoneOffset`: all city timezones, DST, idempotency, edge cases
- Enrichment round-trip: naive datetime bug demonstration and fix verification
- Real ICS files: parses actual feeds from Santa Rosa, Bloomington, Montclair, Toronto and validates cross-timezone correctness

Run: `python3 -m pytest tests/test_timezone_pipeline.py -v`
