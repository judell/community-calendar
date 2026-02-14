# Community Calendar

A community event aggregator that scrapes events from multiple sources, combines them into ICS feeds, and displays them via an XMLUI web app backed by Supabase.

## Table of Contents

- [Live App](#live-app)
- [Architecture](#architecture)
- [Components](#components)
- [Deployment Workflow](#deployment-workflow)
- [Supabase Setup Notes](#supabase-setup-notes)
- [Recent Updates](#recent-updates-feb-2026)
- [XMLUI Resources](#xmlui-resources)
- [Testing](#testing)
- [Legacy HTML Generation](#legacy-html-generation)
- [Adding a New City](#adding-a-new-city)
- [Recurrence and Enrichment](#recurrence-and-enrichment)
- [Planned Improvements](#planned-improvements)
- [File Structure](#file-structure)

## Live App

**XMLUI App**: https://judell.github.io/community-calendar/ (city picker)
- Santa Rosa: `index.html?city=santarosa`
- Bloomington: `index.html?city=bloomington`
- Davis: `index.html?city=davis`

**Subscribable ICS Feeds**:
- Santa Rosa: https://judell.github.io/community-calendar/cities/santarosa/combined.ics
- Bloomington: https://judell.github.io/community-calendar/cities/bloomington/combined.ics
- Davis: https://judell.github.io/community-calendar/cities/davis/combined.ics

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Scrapers      │────▶│   ICS Files     │────▶│  combined.ics   │
│ (various sites) │     │ (per source)    │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   XMLUI App     │◀────│    Supabase     │◀────│  events.json    │
│  (GitHub Pages) │     │   (database)    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Components

### 1. Event Sources

#### Discovery Philosophy

**We want COMPLETE coverage, not curated coverage.** This means:

- **Long-tail events matter** - A book club with 5 members, a small craft meetup, a neighborhood cleanup - these ARE our target. Don't skip sources just because they seem niche or low-volume.

- **Schools are gold mines** - High schools and colleges have athletics, theater productions, band concerts, art shows, parent nights, and graduations.

- **Churches and community centers** - Special events like concerts, fundraisers, and community dinners are valuable even if weekly services aren't.

- **Youth sports leagues** - Little League, youth soccer, swim teams often have public calendars.

- **If in doubt, add it** - We can always filter later. Missing events is worse than having too many.

#### Source Types

**ICS feeds are preferred** when available. Many venues and organizations publish standard iCalendar feeds that we consume directly:
- Luther Burbank Center
- Schulz Museum
- GoLocal Coop
- Sonoma County AA
- City calendars (Google Calendar)
- And more...

**Scraping is a fallback** for sources that don't provide ICS feeds:
- Press Democrat (event listings)
- Bohemian (event listings)
- Sonoma County Library (via API interception)
- Cal Theatre
- Copperfield's Books

**Generic/reusable scrapers** work across multiple sites:
- `maxpreps.py` - High school athletics (any school)
- `growthzone.py` - Chamber of Commerce sites
- `eventbrite_scraper.py` - Eventbrite events by location
- `library_intercept.py` - Library event calendars

Scrapers are in `scrapers/` and per-city data lives in `cities/<name>/`.

### 2. ICS Combination

**`scripts/combine_ics.py`** - Combines multiple ICS files into a single subscribable feed:

```bash
python scripts/combine_ics.py -i cities/santarosa -o cities/santarosa/combined.ics --name "Santa Rosa Community Calendar"
```

### 3. ICS to JSON Conversion

**`scripts/ics_to_json.py`** - Converts ICS to JSON format for Supabase ingestion:

```bash
python scripts/ics_to_json.py cities/santarosa/combined.ics -o cities/santarosa/events.json
```

Output format:
```json
{
  "title": "Event Name",
  "start_time": "2026-02-01T14:00:00",
  "end_time": "2026-02-01T16:00:00",
  "location": "Venue, Address",
  "description": "Event description",
  "url": "https://...",
  "source": "Source Name",
  "source_uid": "unique-id@source.com"
}
```

### 4. XMLUI Frontend

**`Main.xmlui`** - Declarative UI that fetches events from Supabase:

```xml
<App name="Community Calendar">
  <DataSource
    id="events"
    url="{appGlobals.supabaseUrl + '/rest/v1/events?...'}"
    headers="{{ apikey: appGlobals.supabasePublishableKey }}"
  />
  <List data="{events}">
    <!-- Event display -->
  </List>
</App>
```

**`config.json`** - XMLUI configuration with Supabase credentials:
```json
{
  "appGlobals": {
    "supabaseUrl": "https://dzpdualvwspgqghrysyz.supabase.co",
    "supabasePublishableKey": "sb_publishable_..."
  }
}
```

**`index.html`** - Loads XMLUI, reads `?city=` URL param, defines helper functions for date formatting.

### 5. Supabase Backend

#### Database Schema

```sql
CREATE TABLE events (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  title text NOT NULL,
  start_time timestamptz NOT NULL,
  end_time timestamptz,
  location text,
  description text,
  url text,
  city text,           -- e.g., 'santarosa', 'davis'
  source text,         -- e.g., 'bohemian', 'yolo_library'
  source_uid text UNIQUE,
  transcript text,     -- Whisper transcript for audio-captured events
  created_at timestamptz DEFAULT now()
);
```

#### Edge Function: `load-events`

Fetches `events.json` from GitHub and upserts into the database:

```bash
curl -L -X POST 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events' \
  -H 'Authorization: Bearer <LEGACY_ANON_KEY>' \
  -H 'Content-Type: application/json'
```

Returns:
```json
{"success":true,"fetched":9338,"unique":6404,"inserted":6404,"errors":0}
```

#### Scheduled Refresh (pg_cron)

The Edge Function is scheduled to run daily at 6am UTC:

```sql
SELECT cron.schedule(
  'load-events-daily',
  '0 6 * * *',
  $$ SELECT net.http_post(...) $$
);
```

See `supabase/ddl/05_cron_jobs.sql` for the full setup.

## Deployment Workflow

### Adding a New Scraper

When you create a new scraper, use the `add_scraper.py` script to integrate it into the pipeline:

```bash
# After creating scrapers/myscraper.py, run:
python scripts/add_scraper.py myscraper santarosa "My Source Name"

# This automatically:
# 1. Verifies the scraper exists
# 2. Adds it to .github/workflows/generate-calendar.yml
# 3. Adds the source name to scripts/combine_ics.py

# Options:
#   --test      Run the scraper first to verify it works
#   --dry-run   Preview changes without applying them
```

**All three steps are required** — if you skip the workflow or source name, events won't appear in the calendar.

### Manual Update

```bash
# 1. Run scrapers (produces individual ICS files)
# (varies by scraper)

# 2. Combine ICS files
python scripts/combine_ics.py -i cities/santarosa -o cities/santarosa/combined.ics

# 3. Convert to JSON
python scripts/ics_to_json.py cities/santarosa/combined.ics -o cities/santarosa/events.json

# 4. Commit and push
git add cities/santarosa/events.json cities/santarosa/combined.ics
git commit -m "Update events"
git push

# 5. Trigger Supabase ingestion
curl -L -X POST 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events' \
  -H 'Authorization: Bearer <LEGACY_ANON_KEY>'
```

### Automated (GitHub Actions)

The workflow in `.github/workflows/generate-calendar.yml` runs automatically.

**Schedule**: Daily at midnight UTC (`0 0 * * *`)

**Cities processed**:
- `santarosa` - Santa Rosa, CA (America/Los_Angeles)
- `bloomington` - Bloomington, IN (America/Indiana/Indianapolis)
- `davis` - Davis, CA (America/Los_Angeles)

**Time range**: Current month + next 2 months

**Per-city workflow**:
1. Run scrapers for sources without ICS feeds
2. Download live ICS feeds from venues that provide them
3. Update `feeds.txt` with all sources (live URLs + local scraped files)
4. Generate legacy HTML calendars via `cal.py`
5. Combine all ICS files into `combined.ics`
6. Commit and push changes

**Manual trigger**: Can also be triggered manually via GitHub Actions UI with options:
- `locations`: Comma-separated list (e.g., `santarosa,bloomington`) or `all`
- `regenerate_only`: Skip scraping, just regenerate from existing ICS files

## Supabase Setup Notes

### API Keys

Supabase has two key formats:
- **New format**: `sb_publishable_...` - Used in `config.json` for XMLUI
- **Legacy format**: `eyJ...` (JWT) - Required for Edge Function auth

Find legacy keys in Supabase Dashboard: **Settings → API → Legacy anon, service_role API keys**

### Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS pg_net;    -- HTTP requests
CREATE EXTENSION IF NOT EXISTS pg_cron;   -- Scheduled jobs
```

### Unique Constraint

Required for upsert operations:
```sql
ALTER TABLE events ADD CONSTRAINT events_source_uid_unique UNIQUE (source_uid);
```

## Recent Updates (Feb 2026)

### Search Functionality

The app now includes client-side search that filters events as you type:

- **Search icon** in header toggles search box with auto-focus
- **Searches** title, location, source, and description fields
- **Description snippets**: When a match is found in description (not displayed), shows a context window with the search term **highlighted**

### List Virtualization and Search Performance

The List uses three key props:
```xmlui
<List data="{window.filterEvents(window.dedupeEvents([...]), filterTerm)}"
      fixedItemSize="true" limit="50">
```

#### How the search chain works

Data flows through several stages on every keystroke:

1. **DataSource fetch** — up to 5000 events from Supabase (one-time)
2. **`dedupeEvents()`** — O(n) grouping pass with a simple cache (`helpers.js:141`)
3. **`filterEvents()`** — O(n) scan across title, location, source, and description (`helpers.js:46`). Runs on **every keystroke** because `filterTerm` is a reactive var
4. **`limit="50"`** — XMLUI truncates the filtered result to 50 items before handing them to the virtualizer
5. **Virtualization** — only the ~10-15 items visible in the viewport get DOM nodes; the other 35-40 are "virtual" (no DOM cost)
6. **`fixedItemSize="true"`** — lets the virtualizer measure one card and assume all are that height

Search gets snappier as you type because the filter output shrinks, so the List receives fewer items and React diffs less. The `limit` is **not** about DOM nodes — virtualization handles that. It's about **React's virtual DOM diffing**: each item, even if not rendered to the DOM, is a React element that must be created, diffed, and reconciled on every keystroke.

#### Why limit=50

Measured data shows limit=50 delivers a 38% improvement on the first keystroke vs limit=100 (859ms → 531ms). The tradeoff — users can only scroll 50 events before searching — is barely a tradeoff in practice. Search is one click (the magnifying glass) and one keystroke away.

| Limit | Pros | Cons |
|-------|------|------|
| **50** (current) | 38% faster search; best responsiveness | Users scroll 50 events before needing to search |
| **100** | More scrollable | ~100 virtual elements tracked; first keystroke ~859ms |
| **200+** | More browsable | Heavier reconciliation on each keystroke; noticeable lag |

#### fixedItemSize tradeoffs

EventCards have **variable actual heights** (wrapping titles, conditional location/description). `fixedItemSize="true"` tells the virtualizer to measure the first card and assume all match.

| | `fixedItemSize="true"` (current) | `fixedItemSize="false"` |
|---|---|---|
| **Scroll perf** | Best — no per-item measurement | Slightly worse |
| **Scrollbar accuracy** | May drift with variable heights | Accurate (progressively) |
| **Visual correctness** | Cards may clip or show extra whitespace | Each card gets its true height |

At limit=50, measurement shows **no performance difference** between true and false. We could switch to `false` for accurate scrollbar positioning with no cost.

#### Fetch size vs. virtualization

These are independent concerns. Whether Supabase returns 200 or 5000 events, the virtualizer always sees at most 50. The fetch size affects the JS filter scan cost (2-3ms — negligible), not the rendering cost.

#### Measurement and optimization

App-level measurement using [trace-tools](https://github.com/xmlui-org/trace-tools) confirms that `filterEvents` takes 2-3ms — the bottleneck is engine-internal reactive overhead and React reconciliation, not app-level code. The only effective app-level lever is `limit` (lowering from 100 to 50 gave a 38% improvement). See the [xsTrace case study](https://github.com/xmlui-org/trace-tools#xstrace-case-study-community-calendar-search) for the full investigation, measurement methodology, and engine analysis.

XMLUI List docs: [List](https://docs.xmlui.org/components/List) | [Items](https://docs.xmlui.org/components/Items) (non-virtualized alternative)

### XMLUI Inspector

Added debugging tool accessible via cog icon:
- Opens `xs-diff.html` in modal (relative path for GitHub Pages compatibility)
- Shows event traces, state changes, API calls
- Requires `xsVerbose: true` in config.json

### Personal Picks (Implemented)

Users can now authenticate and save personal event picks:

```
┌─────────────────────────────────────────────────────────┐
│  User authenticates via GitHub OAuth (user icon)        │
│                    ↓                                    │
│  Browse events, click checkbox to add to picks          │
│                    ↓                                    │
│  Click calendar icon to view My Picks dialog            │
│                    ↓                                    │
│  Personal ICS feed URL with unique token                │
│                    ↓                                    │
│  Subscribe in Google Calendar / Apple Calendar          │
└─────────────────────────────────────────────────────────┘
```

**OAuth flow:** App → Supabase → GitHub → Supabase → App. Identity comes from the GitHub account the user is logged into. Session stored in localStorage (`sb-*-auth-token`), not cookies. To test with a different identity, use incognito or revoke the app at GitHub → Settings → Applications.

**Database tables:**
- `picks` - user_id + event_id with joined events data (RLS-protected)
- `feed_tokens` - unique token per user for ICS feed URL

**Implementation details:**
- Feed token created automatically on first sign-in (page reloads to sync DataSource)
- Picking: checkbox opens PickEditor modal for confirmation + optional recurrence enrichment
- Unpicking: one-click checkbox remove (no modal), deletes pick + any associated enrichment
- "all" / "my picks" radio group toggles between full feed and personal picks view
- DataSource refresh via `refreshCounter` in Globals.xs + ChangeListener in Main.xmlui

**Edge function:**
- `my-picks` - validates token, returns user's picks as ICS (default) or JSON (`?format=json`)
- Deploy with `--no-verify-jwt` to allow calendar app subscriptions (token provides auth)
- Example: `https://<project>.supabase.co/functions/v1/my-picks?token=<feed_token>`
- Note: Calendar apps poll ICS feeds periodically (Google: 12-24h, Apple: 15min-1h)

**Cross-source duplicate handling:**
- Same event from different sources (e.g., GoLocal + Cal Theatre) gets merged in display
- Dedupe tracks `mergedIds` array for all source variants
- Picks work across sources: checking/unchecking normalizes to the primary ID

**Responsive UI:**
- Modal dialog uses `minWidth="70vw"` for mobile compatibility
- Text uses `overflowMode="flow"` for proper wrapping

### Event Capture (Image + Audio)

Users can photograph an event poster or speak/upload audio to capture events:

```
┌─────────────────────────────────────────────────────────┐
│  Click camera icon (image) or play icon (audio)         │
│                    ↓                                    │
│  Image: select photo of event poster                    │
│  Audio: record from microphone or select audio file     │
│                    ↓                                    │
│  Image → Claude API extracts event details              │
│  Audio → Whisper transcribes → Claude extracts details  │
│                    ↓                                    │
│  Review/edit extracted details in PickEditor form       │
│  (recurrence auto-detected from text, city auto-set)    │
│                    ↓                                    │
│  "Add to My Picks" saves event + pick + enrichment      │
│  Transcript appended to description with attribution    │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- `components/CaptureDialog.xmlui` — image selection → Claude API → PickEditor
- `components/AudioCaptureDialog.xmlui` — audio file/microphone → Whisper + Claude → PickEditor
- `supabase/functions/capture-event/index.ts` (v23) — edge function with two modes:
  - **Extract mode**: Receives image or audio via multipart upload. Images go to Claude directly. Audio goes to Whisper for transcription, then Claude extracts event JSON from the transcript.
  - **Commit mode**: Receives edited event JSON, inserts into `events` table with `source='poster_capture'`, creates pick. For audio: appends transcript to description ("Transcribed audio from {username}:"), saves transcript in dedicated column, saves city from client.

**Audio-specific features:**
- Provenance URLs: Saying "check Facebook for it" generates a search URL (`facebook.com/search/top/?q=...`)
- Day inference: "Tuesday ride" → next upcoming Tuesday
- End time estimation: Unknown durations get reasonable guesses (1hr meetup, 2-3hr concert)
- Recurrence detection: "weekly" or "on Tuesdays" auto-populates recurrence in PickEditor
- See [docs/audio-capture.md](docs/audio-capture.md) for the full development history

**XMLUI patterns learned:**
- `Actions.upload` returns result synchronously (callbacks don't fire)
- `Actions.upload` uses filename as form field name (not "file") — see [issue #2741](https://github.com/xmlui-org/xmlui/issues/2741)
- TextBox/TextArea require `initialValue` + `id` + `setValue()` for dynamic updates (not `value` binding)
- APICall needs `body="{$param}"` to send `execute()` parameter as request body
- CORS must include `x-ue-client-tx-id` header for XMLUI uploads — see [issue #1942](https://github.com/xmlui-org/xmlui/issues/1942)

**Secrets required:**
- `ANTHROPIC_API_KEY` — Claude extraction (image and audio text)
- `OPENAI_API_KEY` — Whisper transcription (audio only)

**Technical notes:**
- Base64 encoding uses chunked processing (8KB chunks) to avoid stack overflow — spreading 184K+ bytes as function arguments exceeds JavaScript's call stack limit
- iOS Safari debugging tip: when client shows a server error, check Supabase Dashboard → Edge Functions → Logs first
- Browser MediaRecorder produces WebM (Chrome) or MP4 (Safari), both handled by Whisper

### Component Architecture

The app uses XMLUI's `Globals.xs` for cross-component state and functions:

```
Globals.xs                            # Shared vars (pickEvent, picksData, enrichmentsData, refreshCounter)
                                      # and functions (togglePick, removePick)
Main.xmlui                            # App shell with DataSources + ChangeListeners for reactive sync
helpers.js                            # Pure functions (filter, dedupe, format, detectRecurrence, expandEnrichments, buildGoogleCalendarUrl)

components/
├── EventCard.xmlui                   # Event display card with pick checkbox
├── PickItem.xmlui                    # Pick item in My Picks view
├── PickEditor.xmlui                  # Modal for confirming picks + optional recurrence enrichment
├── AddToCalendar.xmlui               # ICS download button (includes RRULE when available)
├── CaptureDialog.xmlui               # Poster capture: image → Claude API → PickEditor
├── AudioCaptureDialog.xmlui          # Audio capture: mic/file → Whisper → Claude → PickEditor
└── SourcesDialog.xmlui               # Sources modal (uses method.open pattern)
```

**Globals.xs pattern:**
```javascript
// Globals.xs — vars and functions accessible from all components
var pickEvent = null;       // set to event object to open PickEditor
var picksData = null;       // synced from picks DataSource via ChangeListener
var enrichmentsData = null; // synced from enrichments DataSource via ChangeListener
var refreshCounter = 0;     // increment to trigger DataSource refetch

function togglePick(event) { ... }
function removePick(pickId) { ... }
```

**DataSource refresh pattern:** Globals.xs functions can't reference DataSource IDs directly (they're XMLUI context variables, not JS scope). Instead, incrementing `refreshCounter` triggers a `ChangeListener` in Main.xmlui that calls `refetch()` in XMLUI context where DataSource IDs are valid.

**Key patterns:**
- `Globals.xs` for shared state and functions — no prop drilling needed
- ChangeListeners sync DataSource values to Globals.xs vars (`picksData`, `enrichmentsData`)
- ChangeListener on `refreshCounter` triggers `picks.refetch(); events.refetch(); enrichments.refetch()`
- `method.open` on Component exposes internal dialog's open method
- Inline `tooltip` prop on Icon instead of Tooltip wrapper

## XMLUI Resources

- [XMLUI Documentation](https://xmlui.org)
- [DataSource Component](https://docs.xmlui.org/components/DataSource)
- [Supabase + XMLUI Quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/xmlui)
- [Supabase + XMLUI Blog Post](https://blog.xmlui.org/blog/supabase-and-xmlui) - Auth pattern reference

## Testing

Browser-based tests for the JavaScript helper functions. Open `test.html` in a browser to run.

**Test structure:**
- `helpers.js` - Extracted pure functions (filterEvents, dedupeEvents, formatTime, etc.)
- `test.html` - Test runner with assertions

**Test coverage:**
- `filterEvents` - search by title, location, source, description
- `getDescriptionSnippet` - context extraction and highlighting
- `formatTime`, `formatDayOfWeek`, `formatMonthDay` - date formatting
- `truncate` - text truncation
- `getSourceCounts` - source aggregation
- `dedupeEvents` - cross-source duplicate merging, mergedIds tracking, RRULE carry-through
- `isEventPicked` - pick detection with merged IDs
- `detectRecurrence` - recurrence pattern detection (numeric ordinals, word-form ordinals, multi-arg)
- `getNextOccurrence` - next occurrence computation from RRULE enrichments
- `formatPickDate` - pick date display with next-occurrence fallback

**Real data tests:**
After mock tests, `test.html` fetches 500 live events from Supabase and validates:
- All events have required fields
- Helpers don't crash on real data edge cases
- Deduplication finds actual duplicates (~9% reduction)
- Long descriptions, null fields, and special characters handled correctly

## Legacy HTML Generation

The original HTML calendar generation lives in `legacy/`:

```bash
python legacy/cal.py --generate --location santarosa --year 2026 --month 2
```

See the legacy calendars at `/cities/bloomington/2026-02.html` etc.

---

## Adding a New City

See the detailed guides:
- **[docs/curator-guide.md](docs/curator-guide.md)** — Human curator workflow for discovering and adding event sources
- **[AGENTS.md](AGENTS.md)** — Technical reference for AI agents and developers

Quick overview:
1. Create city directory with `feeds.txt`, `SOURCES_CHECKLIST.md`, `allowed_cities.txt`
2. Run geo-filtering setup: `python scripts/geocode_cities.py --city {name}`
3. Discover sources (Meetup, Eventbrite, local venues)
4. Add to GitHub Actions workflow
5. Update UI (`index.html`, `Main.xmlui`)
6. Add to Supabase edge function

## Recurrence and Enrichment

Curators (signed-in users) can attach recurrence rules to events, making them visible to all users as recurring virtual events.

### How it works

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Curator clicks checkbox on a feed event (e.g., "Circus jam")   │
│                         ↓                                          │
│  2. PickEditor modal opens, pre-populated from the event           │
│     - Title, date, time, location, description                     │
│     - Recurrence section (auto-expands if text says "every Wed")   │
│                         ↓                                          │
│  3. Curator sets frequency (Weekly/Monthly) + days                 │
│                         ↓                                          │
│  4. "Add to My Picks" creates:                                     │
│     - A pick (picks table) — personal                              │
│     - An enrichment (event_enrichments table) — public             │
│       with RRULE, title, start_time, city, curator_name            │
│                         ↓                                          │
│  5. Client-side RRULE expansion generates virtual events           │
│     visible to ALL users in the main feed                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Recurrence detection

`detectRecurrence()` in `helpers.js` scans event text for recurrence language. It accepts multiple arguments (description, title) and returns the first match:

- `"every Wednesday"` → `{ frequency: 'WEEKLY', days: ['WE'] }`
- `"weekly"` / `"every week"` → `{ frequency: 'WEEKLY', days: [] }`
- `"1st Tuesday of every month"` → `{ frequency: 'MONTHLY', ordinal: 1, monthDay: 'TU' }`
- `"monthly"` → `{ frequency: 'MONTHLY' }`

When the PickEditor opens, if recurrence is detected, the recurrence section auto-expands with frequency and days pre-selected.

### Self-standing enrichments

The `event_enrichments` table stores enrichment data that can survive independently of the original event:

| Column | Purpose |
|--------|---------|
| `event_id` | Links to original event (nullable — enrichment survives if event is deleted) |
| `curator_id` | User who created the enrichment |
| `rrule` | RFC 5545 recurrence rule (e.g., `FREQ=WEEKLY;BYDAY=WE`) |
| `title`, `start_time`, `city` | Copied from event at enrichment time |
| `curator_name` | GitHub username for source attribution |

### Client-side RRULE expansion

`expandEnrichments()` in `helpers.js` uses the [rrule.js](https://github.com/jakubroztocil/rrule) library to generate virtual events:

1. For each enrichment with an `rrule`, parse it via `rrule.RRule.fromString()`
2. Set `dtstart` from the enrichment's `start_time`
3. Call `rule.between(fromDate, toDate)` to get occurrences in the visible date range
4. Create virtual event objects with `source: 'Picks: ' + curator_name`

### Merging with feed events

Virtual events from enrichments merge with feed events via `dedupeEvents()`:

- **Key**: `title.toLowerCase() + start_time` — same event from different sources merges into one card
- **Source attribution**: Sources are joined with `, ` — e.g., `"Bohemian, Picks: Jon"`
- **RRULE carry-through**: When an enrichment event merges with a feed event, the RRULE is preserved on the merged result so ICS downloads include recurrence

Example scenarios:
- "Circus jam" from Bohemian feed + enrichment on same date → source shows `"Bohemian, Picks: Jon"`
- "Circus jam" from enrichment only (no feed event that week) → source shows `"Picks: Jon"`
- User downloads ICS for a merged event → RRULE is included in the VEVENT

### Pinning in My Picks

Recurring picks stay pinned in the "my picks" view regardless of whether the original event date has passed. The `PickItem` component uses `getNextOccurrence()` to display the next upcoming occurrence date instead of the original (possibly past) date.

### Pick/unpick flow

- **Picking**: Click checkbox → PickEditor modal opens → confirm with optional recurrence → pick + enrichment created
- **Unpicking**: Click checkbox on already-picked event → one-click remove (no modal), deletes both the pick and any associated enrichment
- **DataSource refresh**: Both paths increment a `refreshCounter` var in `Globals.xs`, which triggers a `ChangeListener` in `Main.xmlui` to call `refetch()` on the events, picks, and enrichments DataSources

### Three capture paths, one editor

All paths converge on the same `PickEditor` component:

| Path | Entry point | Pre-population |
|------|-------------|----------------|
| **Feed pick** | Checkbox on EventCard | Event data from feed |
| **Photo capture** | Camera icon → CaptureDialog | Claude API extraction from poster image |
| **Audio capture** | Play icon → AudioCaptureDialog | Whisper transcription → Claude extraction from audio |

### ICS download

The `AddToCalendar` component generates a downloadable `.ics` file for any event. If the event has an RRULE (from enrichment), it's included in the VEVENT so calendar apps that support recurrence (Google Calendar, Apple Calendar, Outlook) will create recurring entries.

## Planned Improvements

- **my-picks edge function**: Update to handle self-standing enrichments. When a curator adds an RRULE enrichment and the original event is later deleted, the enrichment's own `title`/`start_time`/`location` fields should be used as fallback in the ICS feed.

## File Structure

```
community-calendar/
├── Main.xmlui              # XMLUI app shell (DataSources, ChangeListeners, layout)
├── Globals.xs              # Shared vars + functions (togglePick, removePick, refreshCounter)
├── helpers.js              # Pure helper functions (filter, dedupe, format, detectRecurrence, etc.)
├── components/
│   ├── EventCard.xmlui     # Event display card with pick checkbox
│   ├── PickItem.xmlui      # Pick item in My Picks view
│   ├── PickEditor.xmlui    # Pick confirmation modal with recurrence enrichment
│   ├── AddToCalendar.xmlui # ICS download button (includes RRULE when available)
│   ├── CaptureDialog.xmlui # Poster capture: image → Claude API → PickEditor
│   ├── AudioCaptureDialog.xmlui # Audio capture: mic/file → Whisper → Claude → PickEditor
│   └── SourcesDialog.xmlui # Sources modal dialog
├── config.json             # Supabase credentials + xsVerbose for inspector
├── index.html              # XMLUI loader + auth setup + ?city= param routing
├── test.html               # Browser-based test runner
├── xs-diff.html            # XMLUI Inspector UI
├── xmlui/                  # Local XMLUI engine
├── cities/                 # Per-city data (ICS files, events.json, feeds.txt)
│   ├── santarosa/
│   ├── bloomington/
│   └── davis/
├── scripts/                # Build scripts
│   ├── combine_ics.py      # Combines ICS files into combined.ics
│   ├── ics_to_json.py      # Converts ICS to JSON for Supabase
│   ├── library_intercept.py # Sonoma County Library scraper
│   └── report.py           # Feed health report
├── scrapers/               # Event scrapers (Eventbrite, CitySpark, RSS, etc.)
├── supabase/
│   ├── ddl/                # Database schema documentation (01-06)
│   └── functions/          # Edge Functions (load-events, my-picks, capture-event)
└── legacy/                 # Legacy HTML calendar generator (cal.py, templates)
```
