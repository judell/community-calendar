# Community Calendar

A community event aggregator that scrapes events from multiple sources, combines them into ICS feeds, and displays them via an XMLUI web app backed by Supabase.

## Live App

**XMLUI App**: https://judell.github.io/community-calendar/

**Subscribable ICS Feed**: https://judell.github.io/community-calendar/santarosa/combined.ics

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

Scrapers are in `scrapers/` and per-location folders (e.g., `santarosa/`).

### 2. ICS Combination

**`combine_ics.py`** - Combines multiple ICS files into a single subscribable feed:

```bash
python combine_ics.py -i santarosa -o santarosa/combined.ics --name "Santa Rosa Community Calendar"
```

### 3. ICS to JSON Conversion

**`ics_to_json.py`** - Converts ICS to JSON format for Supabase ingestion:

```bash
python ics_to_json.py santarosa/combined.ics -o santarosa/events.json
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

**`index.html`** - Loads XMLUI and defines helper functions for date formatting.

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
  source text,
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

See `supabase_cron.sql` for the full setup.

## Deployment Workflow

### Manual Update

```bash
# 1. Run scrapers (produces individual ICS files)
# (varies by scraper)

# 2. Combine ICS files
python combine_ics.py -i santarosa -o santarosa/combined.ics

# 3. Convert to JSON
python ics_to_json.py santarosa/combined.ics -o santarosa/events.json

# 4. Commit and push
git add santarosa/events.json santarosa/combined.ics
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
- `sebastopol` - Sebastopol, CA (America/Los_Angeles)
- `cotati` - Cotati, CA (America/Los_Angeles)
- `sonoma` - Sonoma, CA (America/Los_Angeles)
- `bloomington` - Bloomington, IN (America/Indiana/Indianapolis)

**Time range**: Current month + next 2 months

**Per-city workflow**:
1. Run scrapers for sources without ICS feeds
2. Download live ICS feeds from venues that provide them
3. Update `feeds.txt` with all sources (live URLs + local scraped files)
4. Generate legacy HTML calendars via `cal.py`
5. Combine all ICS files into `combined.ics`
6. Commit and push changes

**Manual trigger**: Can also be triggered manually via GitHub Actions UI with options:
- `locations`: Comma-separated list (e.g., `santarosa,sebastopol`) or `all`
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
- Opens `xs-diff.html` in modal
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
│  Personal ICS feed URL with unique token (planned)      │
│                    ↓                                    │
│  Subscribe in Google Calendar / Apple Calendar          │
└─────────────────────────────────────────────────────────┘
```

**Database tables:**
- `picks` - user_id + event_id (RLS-protected)
- `feed_tokens` - unique token per user for ICS feed URL

**Implementation details:**
- Feed token created automatically on first sign-in
- APICall components used for pick operations (traced by XMLUI Inspector)
- Checkbox UI shows pick state per event card

**Edge function (TODO):**
- `my-picks` - validates token, returns user's picks as ICS

## XMLUI Resources

- [XMLUI Documentation](https://xmlui.org)
- [DataSource Component](https://docs.xmlui.org/components/DataSource)
- [Supabase + XMLUI Quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/xmlui)
- [Supabase + XMLUI Blog Post](https://blog.xmlui.org/blog/supabase-and-xmlui) - Auth pattern reference

## Legacy HTML Generation

The original HTML calendar generation is still available:

```bash
python cal.py --generate --location santarosa --year 2026 --month 2
```

See the legacy calendars at `/santarosa/2026-02.html` etc.

---

## File Structure

```
community-calendar/
├── Main.xmlui              # XMLUI app definition
├── config.json             # Supabase credentials + xsVerbose for inspector
├── index.html              # XMLUI loader + helper functions (auth, filter, dedupe, etc.)
├── xs-diff.html            # XMLUI Inspector UI
├── xmlui/
│   └── 0.11.33-inspector.js  # Local XMLUI engine with inspector support
├── combine_ics.py          # Combines ICS files
├── ics_to_json.py          # Converts ICS to JSON
├── supabase_cron.sql       # Scheduled job setup
├── cal.py                  # Legacy HTML generator
├── santarosa/
│   ├── combined.ics        # Subscribable calendar feed
│   ├── events.json         # JSON for Supabase ingestion
│   ├── feeds.txt           # List of ICS sources
│   └── *.ics               # Individual source feeds
└── scrapers/               # Event scrapers
```
