# Supabase Configuration

This directory contains all Supabase-related code and configuration.

## Schema Change Policy

This repo is now **migration-first** for database changes.

- `supabase/migrations/` is the operational history of schema changes.
- Every future schema change should be captured as a migration file.
- `supabase/ddl/` remains useful, but only as a snapshot of the current expected database state.
- Do not make production-only SQL changes unless the same change also lands in `supabase/migrations/`.

Use this distinction:

- `migrations/` answers: "How does an older instance get to the current schema?"
- `ddl/` answers: "What should the schema look like now?"

### Rules for future schema work

1. Add a migration for every schema change.
2. Apply migrations to the main instance and to forks.
3. Update the corresponding `ddl/` file(s) after the migration is finalized.
4. Prefer additive migrations first, then backfill, then cleanup/removal in a later migration.
5. Avoid destructive one-step changes when forks may be behind.

### Recommended pattern for risky changes

For renames, type changes, and removals, use an expand/migrate/contract pattern:

1. Expand: add new columns, tables, policies, functions, or views alongside the old ones.
2. Migrate: backfill data and update code to use the new shape.
3. Contract: remove the old structure in a later migration.

## Directory Structure

```
supabase/
├── ddl/                           # Database schema (documentation of live state)
│   ├── 01_extensions.sql          # pg_net, pg_cron extensions
│   ├── 02_events.sql              # Events table with RLS
│   ├── 03_picks.sql               # User picks with RLS
│   ├── 04_feed_tokens.sql         # Feed tokens with RLS
│   ├── 06_event_enrichments.sql   # Curator overrides per event
│   ├── 07_source_suggestions.sql  # Anonymous source suggestions
│   ├── 08_admin_users.sql         # Server-side admin allowlist (UUID-based)
│   └── 09_admin_github_users.sql  # Server-side admin allowlist (preapproval by GitHub username)
│
├── migrations/                    # Ordered schema changes for existing instances
│   ├── 20260330191500_add_city_column.sql
│   └── 20260421182300_optimize_deduplicated_events_index.sql
│
└── functions/                     # Edge Functions (Deno/TypeScript)
    ├── load-events/               # Upserts CI's events payload (secret-gated)
    ├── my-picks/                  # Returns user's picks as ICS or JSON feed
    └── capture-event/             # Extracts event from poster image or audio via Claude API
```

**Note:** DDL files document the live database state. They are not migration scripts — keep them in sync with what actually exists in Supabase. Migration files are the upgrade path for existing instances.

## API Keys and Security Model

This app embeds a **publishable key** (`sb_publishable_...`) in `config.json` and `index.html`. This is safe by design — Supabase publishable keys are meant to be public, just like the legacy `anon` key they replace.

The publishable key identifies the *application* (not the user) and provides only basic access. The actual security comes from **Row Level Security (RLS)** policies on each table:

| Table | Anonymous access (no login) | Authenticated access (logged-in user) |
|-------|----------------------------|--------------------------------------|
| `events` | SELECT (read all) | SELECT (read all) |
| `picks` | None | SELECT/INSERT/DELETE own rows only |
| `feed_tokens` | None | SELECT/INSERT own row only |
| `event_enrichments` | SELECT (read all) | SELECT all, INSERT/UPDATE/DELETE own rows only |
| `source_suggestions` | SELECT/INSERT (anyone can suggest) | SELECT/INSERT (anyone can suggest) |
| `admin_users` | None | SELECT own row only (admin marker) |
| `admin_github_users` | None | SELECT own GitHub username row only |

So anyone with the publishable key can read events (which is the whole point — it's a public calendar). But only authenticated users can manage their own picks, and RLS ensures they can't see or modify other users' data.

**What would be dangerous:** The `service_role` key (or `sb_secret_...`) bypasses all RLS. It must never appear in frontend code. Edge functions use it server-side via the `SUPABASE_SERVICE_ROLE_KEY` environment variable, which Supabase injects automatically.

For the full explanation, see: https://supabase.com/docs/guides/api/api-keys

### Key types in this project

| Key | Format | Where used | Purpose |
|-----|--------|-----------|---------|
| Publishable | `sb_publishable_...` | `config.json`, `index.html` | Frontend API calls, auth initiation |
| Legacy anon | `eyJ...` (JWT) | Workflow | Edge Function invocation via `Authorization: Bearer` header |
| Service role | `eyJ...` (JWT) | Edge functions (auto-injected env var) | Server-side DB writes bypassing RLS |

**Why both publishable and legacy anon?** Edge Functions only support JWT verification, so the GitHub Actions workflow uses the legacy anon key in the `Authorization` header. The frontend uses the publishable key. Both have the same low-privilege access level. That JWT check is not an authorization boundary — the publishable key is public — so `load-events` additionally requires the `x-load-events-secret` header.

Find keys in: Dashboard > Settings > API > API Keys tab (publishable) and Legacy API Keys tab (anon, service_role).

## GitHub OAuth Setup

Authentication uses GitHub OAuth, coordinated between a GitHub OAuth App and Supabase Auth. Here's what you need on each side:

### Step 1: Create a GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: e.g. `Community Calendar`
   - **Homepage URL**: `https://judell.github.io/community-calendar/`
   - **Authorization callback URL**: `https://dzpdualvwspgqghrysyz.supabase.co/auth/v1/callback`
4. Click **Register application**
5. Copy the **Client ID**
6. Click **Generate a new client secret**, copy the **Client Secret**

The callback URL is the critical piece — it points to *Supabase*, not your app. GitHub redirects the user there after they authorize, and Supabase handles the token exchange.

### Step 2: Configure Supabase Auth

1. Go to Supabase Dashboard > Authentication > Providers
2. Click **GitHub**, toggle it ON
3. Paste the **Client ID** and **Client Secret** from step 1
4. Click **Save**

### Step 3: Configure redirect URLs

1. Go to Supabase Dashboard > Authentication > URL Configuration
2. Set **Site URL** to `https://judell.github.io/community-calendar/` — this is the default redirect target after OAuth
3. Under **Redirect URLs**, add your app's URL(s):
   - `https://judell.github.io/community-calendar/**`
   - `http://localhost:3000/**` (for local dev via `npx serve`)
   - `http://localhost:8080/**` (for local XMLUI dev server)

These are the URLs Supabase is allowed to redirect *back to* after authentication completes. The `redirect_to` parameter in the auth URL must match one of these patterns, otherwise Supabase falls back to the Site URL.

**Important:** The Site URL must not have leading/trailing whitespace — Supabase will fail to parse it with a cryptic "first path segment cannot contain colon" error.

### How the OAuth flow works

```
User clicks Sign In
       │
       ▼
App redirects to Supabase auth endpoint
  (SUPABASE_URL/auth/v1/authorize?provider=github&redirect_to=APP_URL)
       │
       ▼
Supabase redirects to GitHub
  (github.com/login/oauth/authorize?client_id=...)
       │
       ▼
User authorizes on GitHub
       │
       ▼
GitHub redirects to Supabase callback
  (SUPABASE_URL/auth/v1/callback?code=...)
       │
       ▼
Supabase exchanges code for token, creates/updates user record
       │
       ▼
Supabase redirects back to app with session in URL hash
  (APP_URL#access_token=...&refresh_token=...)
       │
       ▼
App's onAuthStateChange handler fires, stores session in localStorage
```

The app initiates this in `index.html`:
```js
window.signIn = () => {
  const returnTo = window.location.origin + window.location.pathname + window.location.search;
  window.location.href = SUPABASE_URL +
    '/auth/v1/authorize?provider=github&redirect_to=' + encodeURIComponent(returnTo);
};
```

Session is stored in `localStorage` as `sb-<project-ref>-auth-token`. To test with a different GitHub identity, use an incognito window or revoke the app at GitHub > Settings > Applications.

## Setup

### 1. Run DDL Scripts

Execute the SQL files in the Supabase SQL Editor in order:

```bash
# Or use psql if you have direct database access
psql $DATABASE_URL -f ddl/01_extensions.sql
psql $DATABASE_URL -f ddl/02_events.sql
psql $DATABASE_URL -f ddl/03_picks.sql
psql $DATABASE_URL -f ddl/04_feed_tokens.sql
psql $DATABASE_URL -f ddl/06_event_enrichments.sql
psql $DATABASE_URL -f ddl/08_admin_users.sql
psql $DATABASE_URL -f ddl/09_admin_github_users.sql

### Admin access management

Admin features (for example Manage Feeds and category overrides) are gated by server-side tables, not by hardcoded GitHub usernames in frontend code. Poster and audio capture are available to any signed-in user.

For preapproval before first sign-in, use `admin_github_users`.

Preapprove by GitHub username:
```sql
insert into admin_github_users (github_user)
values ('judell'), ('gvwilson')
on conflict (github_user) do nothing;
```

Revoke admin:
```sql
delete from admin_github_users where github_user = 'judell';
```
```

### 2. Deploy Edge Functions

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to project
supabase link --project-ref dzpdualvwspgqghrysyz

# load-events rejects every call without this secret, so set it before deploying
supabase secrets set LOAD_EVENTS_SECRET=...

# Deploy functions (all need --no-verify-jwt)
supabase functions deploy load-events --no-verify-jwt
supabase functions deploy my-picks --no-verify-jwt
supabase functions deploy capture-event --no-verify-jwt
```

**JWT gotcha:** Redeploying any edge function via the Supabase MCP tool resets "Require JWT" to ON. After redeploying, manually turn off "Require JWT" in the Supabase dashboard (Edge Functions > function-name > Settings). The `load-events` function is called by the workflow with a shared secret, and `my-picks` is called by calendar apps with a feed token — neither uses a JWT. `capture-event` does check the caller's user JWT in the function body, but the gateway check stays off for the reason in the next paragraph.

**`capture-event` auth:** Both extract and commit require `Authorization: Bearer <user access token>`. The gateway check stays off because the publishable key satisfies it; the function verifies the user with `auth.getUser()` before reading the body or calling Anthropic/OpenAI (GHSA-qq24-wmxg-hrgv). Uploads over 10 MiB return 413.

**`load-events` gotcha:** JWT verification is not an authorization boundary for this function — the publishable key is public, so anyone can satisfy it. Writes are gated by the `x-load-events-secret` header instead. CI reads it from the `LOAD_EVENTS_SECRET` Actions secret, which must match the function secret. If the function secret is unset the function returns 500 and writes nothing; that is intentional (GHSA-qmc5-6cfg-38p7).

### 3. Set Edge Function Secrets

The `capture-event` function needs an Anthropic API key:

Supabase Dashboard > Edge Functions > capture-event > Secrets, or:
```bash
supabase secrets set ANTHROPIC_API_KEY=sk-ant-...
```

`load-events` needs `LOAD_EVENTS_SECRET` (see above). Rotate it by setting the new value in both the Supabase project and the GitHub Actions secret; no redeploy is needed.

## Edge Functions

### load-events (v17)

Upserts one city's events into the events table and sweeps stale rows for the sources that ran. CI sends the payload directly; there is no longer a GitHub-fetch fallback, and only callers holding `LOAD_EVENTS_SECRET` are accepted.

```bash
curl -X POST 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events' \
  -H "x-load-events-secret: $LOAD_EVENTS_SECRET" \
  -H 'Content-Type: application/json' \
  --data-binary @payload.json
```

`payload.json` is `{city, events, ran_sources}`; see the upload step in `.github/workflows/generate-calendar.yml` for how it is built.

### my-picks (v10)

Returns a user's picked events as an ICS calendar feed (default) or JSON.

```
GET https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/my-picks?token=<feed_token>
GET https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/my-picks?token=<feed_token>&format=json
```

Merges event data with curator enrichments (rrule, categories, notes, etc.) from the `event_enrichments` table.

### capture-event (v24)

Extracts event details from a poster image or audio recording using Claude API. Two modes:
- **Extract**: Upload image or audio, get back structured event JSON. Audio is first transcribed via Whisper, then Claude extracts event details from the transcript.
- **Commit**: Save extracted event to database and create a pick. For audio: appends transcript to description, saves transcript in dedicated column.

Requires `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` secrets configured in Supabase dashboard.
