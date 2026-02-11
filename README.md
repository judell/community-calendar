# Community Calendar

A community event aggregator that scrapes events from multiple sources, combines them into ICS feeds, and displays them via an XMLUI web app backed by Supabase.

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

### Performance Optimizations

Rendering 900+ events required optimization:

- **`fixedItemSize="true"`** - List skips per-item height measurement
- **`limit="100"`** - Caps rendered items for faster updates
- **Deduplication caching** - Avoids recomputing on every render

Result: Specific searches like "cotati" now take ~80ms (down from 750ms).

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

### Poster Capture (New)

Users can photograph an event poster and add it to their picks:

```
┌─────────────────────────────────────────────────────────┐
│  Click camera icon (when signed in)                     │
│                    ↓                                    │
│  Select image of event poster                           │
│                    ↓                                    │
│  Claude API extracts: title, date, time, location       │
│                    ↓                                    │
│  Review/edit extracted details in form                  │
│                    ↓                                    │
│  "Add to My Picks" saves event + creates pick           │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- `components/CaptureDialog.xmlui` - UI for image selection and event review
- `supabase/functions/capture-event/index.ts` - Edge function with two modes:
  - **Extract mode**: Receives image via `Actions.upload`, calls Claude API, returns event JSON
  - **Commit mode**: Receives edited event, inserts into `events` table with `source='poster_capture'`, creates pick

**XMLUI patterns learned:**
- `Actions.upload` returns result synchronously (callbacks don't fire)
- `Actions.upload` uses filename as form field name (not "file") - see [issue #2741](https://github.com/xmlui-org/xmlui/issues/2741)
- TextBox/TextArea require `initialValue` + `id` + `setValue()` for dynamic updates (not `value` binding)
- APICall needs `body="{$param}"` to send `execute()` parameter as request body
- CORS must include `x-ue-client-tx-id` header for XMLUI uploads - see [issue #1942](https://github.com/xmlui-org/xmlui/issues/1942)

**Deploy edge function:**
```bash
supabase functions deploy capture-event --no-verify-jwt
supabase secrets set ANTHROPIC_API_KEY=<key>  # Set via Dashboard for deployed functions
```

**API Key configuration:**
- Currently uses a shared Anthropic API key configured as a Supabase secret
- **Future**: Could support "bring your own key" (BYOK) where users provide their own Anthropic API key via the UI, passed in the request body

**Technical notes:**
- Base64 encoding uses chunked processing (8KB chunks) to avoid stack overflow - spreading 184K+ bytes as function arguments exceeds JavaScript's call stack limit
- iOS Safari debugging tip: when client shows a server error, check Supabase Dashboard → Edge Functions → Logs first

### Component Architecture

The app uses XMLUI's `Globals.xs` for cross-component state and functions:

```
Globals.xs                            # Shared vars (pickEvent, picksData, enrichmentsData, refreshCounter)
                                      # and functions (togglePick, removePick)
Main.xmlui                            # App shell with DataSources + ChangeListeners for reactive sync
helpers.js                            # Pure functions (filter, dedupe, format, detectRecurrence, expandEnrichments)

components/
├── EventCard.xmlui                   # Event display card with pick checkbox
├── PickItem.xmlui                    # Pick item in My Picks view
├── PickEditor.xmlui                  # Modal for confirming picks + optional recurrence enrichment
├── AddToCalendar.xmlui               # ICS download button (includes RRULE when available)
├── CaptureDialog.xmlui               # Poster capture: image → Claude API → PickEditor
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

## Adding a New City (with an AI Agent)

Source discovery is a collaboration between you and an AI coding agent (like Claude Code). You bring local knowledge — what venues, organizations, and activities matter in your city. The agent brings technical ability — probing URLs for feeds, testing ICS files, writing scrapers, and updating config. Here's how to guide the process.

### 1. Set up the city

> "Add a new city called {cityname} to the community calendar."

The agent creates `cities/{cityname}/`, adds a `feeds.txt` and `SOURCES_CHECKLIST.md`, adds the city to the `cityNames` map in `index.html`, and adds a button to the city picker in `Main.xmlui`.

### 2. Run the search pattern playbook

Before seeding with local knowledge, run these web searches to discover feeds systematically. These patterns work across any city.

**High-value feed searches** (platforms that have ICS feeds):
```
{city} {state} site:meetup.com              # Meetup groups → ICS feeds
{city} site:tockify.com                      # Tockify calendars → ICS feeds
{city} {state} inurl:/localist/             # University/govt calendars → API + ICS
"add to calendar" events {city} {state}     # Sites with calendar export → ICS/Google Calendar feeds
```

**Discovery searches** (identify sources, may need scrapers):
```
{city} {state} events site:eventbrite.com   # Eventbrite (needs scraper)
{city} {state} "community calendar"         # Local aggregators
```

**Test each discovery:**
- **Tockify**: `curl -sL "https://tockify.com/api/feeds/ics/{name}" | grep -c "BEGIN:VEVENT"`
- **Meetup**: `curl -sL "https://www.meetup.com/{group}/events/ical/" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"`
- **LiveWhale** (colleges): `curl -sL "https://{domain}/live/ical/events" -A "Mozilla/5.0" | grep -c "BEGIN:VEVENT"`
- **Localist**: `curl -sL "https://{domain}/api/2/events" | head -50`

**Platform feed availability:**

| Platform | Has Feed? | Notes |
|----------|-----------|-------|
| Tockify | Yes | `tockify.com/api/feeds/ics/{name}` |
| Meetup | Yes | `meetup.com/{group}/events/ical/` |
| LiveWhale | Yes | `{domain}/live/ical/events` — common at colleges |
| Localist | Yes | `/api/2/events` or ICS export |
| CampusGroups | Yes | `/ical/{school}/ical_{school}.ics` |
| CitySpark | Scraper | Local media calendars (Bohemian, Press Democrat, etc.) |
| Eventbrite | Scraper | JSON-LD structured data per event page |
| Facebook | Limited | No API; browser-only search finds individual events, not feeds |
| Squarespace/Wix | No | No calendar export |
| Simpleview | No | Tourism sites, no public feed |

See `docs/search-pattern-tests.md` for detailed test results by city.

### 3. Seed with what you know

You know your city. The agent doesn't. List the venues, organizations, and calendars you're aware of:

> "Here are some event sources in {cityname}:
> - The public library at {url}
> - {Venue name} at {url}
> - The city government calendar at {url}
> - {College name} events at {url}
> - A Google Calendar I know about: {url or name}"

The agent probes each URL looking for ICS feeds, RSS feeds, Google Calendar embeds, or scrapeable HTML, and reports what it finds. Expect a mix — some sites have feeds, some need scrapers, some are dead ends. Here's how to read the results:

- **"Found ICS feed"** — Goes straight into the workflow
- **"Found Google Calendar embed"** — Agent can extract the calendar ID and build an ICS URL
- **"Site returns 403/406"** — Blocked; ask the agent to try a User-Agent header, or look for the same events elsewhere
- **"Cloudflare challenge"** — Usually a dead end; move on
- **"Uses WordPress with Tribe Events"** — Ask the agent to try appending `?ical=1`
- **"Found JSON-LD / Schema.org Event markup"** — Scrapeable, but needs a custom scraper

### 4. Meetup discovery

Meetup groups are high-value because they always have ICS feeds. Discovering them requires a browser — the agent can't browse Meetup's search page directly.

**You do this part:**

1. Go to `https://www.meetup.com/find/?keywords=&location=us--{state}--{City}&source=GROUPS`
2. Scroll to load more groups
3. Open browser console (F12) and paste:
   ```javascript
   const links = Array.from(document.querySelectorAll('a')).filter(a =>
     a.href.match(/meetup\.com\/[^\/]+\/?$/) && !a.href.includes('/find'));
   copy([...new Set(links.map(a =>
     a.href.match(/meetup\.com\/([^\/\?]+)/)?.[1]).filter(Boolean))].join('\n'));
   ```
4. This copies group URL names to your clipboard

Then tell the agent:

> "Here are Meetup groups near {cityname}. Test their ICS feeds, check which ones have upcoming events, verify they're actually in {cityname}, and exclude travel groups whose events are at international destinations."

Paste the group list. The agent tests each one and produces a table. You decide which to include.

### 5. Eventbrite

> "Run the Eventbrite scraper for {cityname}."

If the city area includes neighboring towns:

> "Include events from {nearby town 1} and {nearby town 2} too."

Eventbrite results also reveal venues you might not have known about — check the output for surprises.

### 6. Topic-based discovery

Think about what people do in your city:

> "Search for {cityname} groups related to: hiking, birding, astronomy, book clubs, running, cycling, gardening, board games, coding."

The agent web-searches and may find more Meetup groups, organization websites with calendars, or niche sources (parks departments, nature centers, makerspaces). Facebook groups are usually dead ends (no public API since 2018).

### 7. Wire it up

Once you've agreed on sources:

> "Add these sources to the workflow."

The agent adds curl commands to the GitHub Actions workflow, adds Eventbrite scraper commands, updates `scripts/combine_ics.py` with source names, updates `cities/{cityname}/feeds.txt`, adds the city to the `load-events` edge function, and updates `SOURCES_CHECKLIST.md`.

### 8. Review and iterate

After the first run, check results:

> "Run the workflow for {cityname} and let's see what we get."

Common issues:
- **Too many events from one source** — might need date filtering (e.g., a Google Calendar with years of history)
- **Duplicate events** — same event from multiple sources (the app deduplicates, but verify)
- **Wrong city** — a Meetup group nearby but events are actually in another town
- **Stale feeds** — ICS feed exists but hasn't been updated in months

Then iterate:

> "Remove {source} — it's all duplicates of {other source}."
> "That library feed has events from all branches statewide. Can we filter to just {cityname}?"
> "I found another venue: {url}. Can you check if it has a feed?"

### Tips

- **Be specific about geography.** "Santa Rosa" could be California or Florida. Give the state and region.
- **Share what you know about the local scene.** "The main music venues are X, Y, and Z" saves guessing.
- **Don't expect 100% coverage.** Some venues (Facebook-only, Cloudflare-protected, no web presence) can't be scraped.
- **Check SOURCES_CHECKLIST.md first** when returning to a city — it records what was already tried, so you don't repeat dead ends.
- **Meetup and Eventbrite are the two biggest wins** for any new city. Start there, then fill in with local sources.
- **The technical details are in `AGENTS.md`** — feed URL patterns, scraping strategies, platform-specific APIs, anti-scraping workarounds, and the full validation checklist.

---

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

### Two capture paths, one editor

Both paths converge on the same `PickEditor` component:

| Path | Entry point | Pre-population |
|------|-------------|----------------|
| **Feed pick** | Checkbox on EventCard | Event data from feed |
| **Photo capture** | Camera icon → CaptureDialog | Claude API extraction from poster image |

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
