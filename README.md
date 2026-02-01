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

### 1. Event Scrapers

Individual Python scrapers in `scrapers/` and location folders that produce ICS files from various sources:
- Press Democrat
- Bohemian
- GoLocal Coop
- Sonoma County Library
- Luther Burbank Center
- And more...

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

The workflow in `.github/workflows/generate-calendar.yml` automates scraping and ICS generation.

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

## XMLUI Resources

- [XMLUI Documentation](https://xmlui.org)
- [DataSource Component](https://docs.xmlui.org/components/DataSource)
- [Supabase + XMLUI Quickstart](https://supabase.com/docs/guides/getting-started/quickstarts/xmlui)

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
├── config.json             # Supabase credentials for XMLUI
├── index.html              # XMLUI loader + helper functions
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
