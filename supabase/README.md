# Supabase Configuration

This directory contains all Supabase-related code and configuration.

## Directory Structure

```
supabase/
├── ddl/                    # Database schema (run in order)
│   ├── 01_extensions.sql   # pg_net, pg_cron extensions
│   ├── 02_events.sql       # Events table
│   ├── 03_picks.sql        # User picks with RLS
│   ├── 04_feed_tokens.sql  # Feed tokens with RLS
│   └── 05_cron_jobs.sql    # Scheduled event loading
│
└── functions/              # Edge Functions (Deno/TypeScript)
    ├── load-events/        # Fetches events.json and upserts to database
    └── my-picks/           # Returns user's picks as ICS feed
```

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
```

### 2. Deploy Edge Functions

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to project
supabase link --project-ref dzpdualvwspgqghrysyz

# Deploy functions
supabase functions deploy load-events
supabase functions deploy my-picks
```

### 3. Configure GitHub OAuth

In Supabase Dashboard → Authentication → Providers → GitHub:
- Enable GitHub provider
- Add Client ID and Client Secret from GitHub OAuth App
- Set callback URL: `https://dzpdualvwspgqghrysyz.supabase.co/auth/v1/callback`

## Edge Functions

### load-events

Fetches `events.json` from GitHub Pages and upserts into the events table.

```bash
curl -X POST 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events' \
  -H 'Authorization: Bearer <ANON_KEY>'
```

### my-picks

Returns a user's picked events as an ICS calendar feed.

```
GET https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/my-picks?token=<feed_token>
```

## API Keys

Supabase has two key formats:
- **New format**: `sb_publishable_...` - Use in frontend code
- **Legacy format**: `eyJ...` (JWT) - Required for Edge Function auth and cron jobs

Find legacy keys in: Dashboard → Settings → API → Legacy anon, service_role API keys
