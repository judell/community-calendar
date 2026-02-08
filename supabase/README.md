# Supabase Configuration

This directory contains all Supabase-related code and configuration.

## Directory Structure

```
supabase/
├── ddl/                           # Database schema (documentation of live state)
│   ├── 01_extensions.sql          # pg_net, pg_cron extensions
│   ├── 02_events.sql              # Events table with RLS
│   ├── 03_picks.sql               # User picks with RLS
│   ├── 04_feed_tokens.sql         # Feed tokens with RLS
│   ├── 05_cron_jobs.sql           # Scheduled event loading
│   └── 06_event_enrichments.sql   # Curator overrides per event
│
├── migrations/                    # One-off migrations (already applied)
│   └── 001_add_city_column.sql
│
└── functions/                     # Edge Functions (Deno/TypeScript)
    ├── load-events/               # Fetches events.json and upserts to database
    ├── my-picks/                  # Returns user's picks as ICS or JSON feed
    └── capture-event/             # Extracts event from poster image via Claude API
```

**Note:** DDL files document the live database state. They are not migration scripts — keep them in sync with what actually exists in Supabase.

## Setup

### 1. Run DDL Scripts

Execute the SQL files in the Supabase SQL Editor in order:

```bash
# Or use psql if you have direct database access
psql $DATABASE_URL -f ddl/01_extensions.sql
psql $DATABASE_URL -f ddl/02_events.sql
psql $DATABASE_URL -f ddl/03_picks.sql
psql $DATABASE_URL -f ddl/04_feed_tokens.sql
psql $DATABASE_URL -f ddl/05_cron_jobs.sql
psql $DATABASE_URL -f ddl/06_event_enrichments.sql
```

### 2. Deploy Edge Functions

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to project
supabase link --project-ref dzpdualvwspgqghrysyz

# Deploy functions (all need --no-verify-jwt)
supabase functions deploy load-events --no-verify-jwt
supabase functions deploy my-picks --no-verify-jwt
supabase functions deploy capture-event --no-verify-jwt
```

**JWT gotcha:** Redeploying any edge function via the Supabase MCP tool resets "Require JWT" to ON. After redeploying, manually turn off "Require JWT" in the Supabase dashboard (Edge Functions > function-name > Settings). The `load-events` function is called by the workflow with the anon key, and `my-picks` is called by calendar apps with a feed token — neither uses a JWT.

### 3. Configure GitHub OAuth

In Supabase Dashboard > Authentication > Providers > GitHub:
- Enable GitHub provider
- Add Client ID and Client Secret from GitHub OAuth App
- Set callback URL: `https://dzpdualvwspgqghrysyz.supabase.co/auth/v1/callback`

## Edge Functions

### load-events (v14)

Fetches `cities/*/events.json` from GitHub Pages and upserts into the events table. Processes all 6 cities.

```bash
curl -X POST 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events' \
  -H 'Authorization: Bearer <ANON_KEY>'
```

### my-picks (v10)

Returns a user's picked events as an ICS calendar feed (default) or JSON.

```
GET https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/my-picks?token=<feed_token>
GET https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/my-picks?token=<feed_token>&format=json
```

Merges event data with curator enrichments (rrule, categories, notes, etc.) from the `event_enrichments` table.

### capture-event (v13)

Extracts event details from a poster image using Claude API. Two modes:
- **Extract**: Upload image, get back structured event JSON
- **Commit**: Save extracted event to database and create a pick

Requires `ANTHROPIC_API_KEY` secret configured in Supabase dashboard.

## API Keys

Supabase has two key formats:
- **New format**: `sb_publishable_...` - Use in frontend code
- **Legacy format**: `eyJ...` (JWT) - Required for Edge Function auth and cron jobs

Find legacy keys in: Dashboard > Settings > API > Legacy anon, service_role API keys
