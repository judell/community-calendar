# Setting Up a Fork

This guide covers everything needed to run your own instance of Community Calendar.

## Overview

You need:
1. A **Supabase** project (database + edge functions)
2. A **GitHub** repo (this fork) with GitHub Pages enabled
3. A **GitHub OAuth App** for user authentication
4. API keys for **Anthropic** (event classification + poster capture) and **OpenAI** (audio transcription, optional)

---

## Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your **project URL** (e.g. `https://abcdefgh.supabase.co`) and **project ref** (the `abcdefgh` part)
3. From **Settings → API**:
   - Copy the **publishable key** (`sb_publishable_...`) from the API Keys tab
   - Copy the **legacy anon key** (`eyJ...`) from the Legacy API Keys tab — needed for edge function invocation
4. Enable required extensions in the SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_net;
   CREATE EXTENSION IF NOT EXISTS pg_cron;
   ```

---

## Step 2: Set Up the Database

Run the DDL files in order in the Supabase SQL Editor (or via `psql`):

```bash
psql $DATABASE_URL -f supabase/ddl/01_extensions.sql
psql $DATABASE_URL -f supabase/ddl/02_events.sql
psql $DATABASE_URL -f supabase/ddl/03_picks.sql
psql $DATABASE_URL -f supabase/ddl/04_feed_tokens.sql
psql $DATABASE_URL -f supabase/ddl/06_event_enrichments.sql
psql $DATABASE_URL -f supabase/ddl/07_source_suggestions.sql
psql $DATABASE_URL -f supabase/ddl/08_admin_users.sql
psql $DATABASE_URL -f supabase/ddl/09_admin_github_users.sql
```

Then set up the scheduled cron job — edit `supabase/ddl/05_cron_jobs.sql`, replacing `YOUR_SUPABASE_URL` with your actual project URL, then run it.

To grant yourself admin access:
```sql
INSERT INTO admin_github_users (github_user) VALUES ('your-github-username');
```

---

## Step 3: Configure the Frontend

Edit these two files with your Supabase project details:

**`config.json`** — used by the XMLUI frontend:
```json
{
  "appGlobals": {
    "supabaseUrl": "https://YOUR_PROJECT_REF.supabase.co",
    "supabasePublishableKey": "sb_publishable_..."
  }
}
```

**`index.html`** — update lines ~41-42 with the same values:
```js
const SUPABASE_URL = 'https://YOUR_PROJECT_REF.supabase.co';
const SUPABASE_KEY = 'sb_publishable_...';
```

Also update `report.html`, `test.html`, and `embed.html` — each has the same two lines near the top of their `<script>` block.

---

## Step 4: Set Up GitHub OAuth

1. Go to [github.com/settings/developers](https://github.com/settings/developers) → **New OAuth App**
   - **Homepage URL**: `https://YOUR_ORG.github.io/community-calendar/`
   - **Authorization callback URL**: `https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback`
2. Copy the **Client ID** and generate a **Client Secret**
3. In Supabase Dashboard → **Authentication → Providers → GitHub**:
   - Paste Client ID and Client Secret, click Save
4. In Supabase Dashboard → **Authentication → URL Configuration**:
   - **Site URL**: `https://YOUR_ORG.github.io/community-calendar/`
   - **Redirect URLs**: add `https://YOUR_ORG.github.io/community-calendar/**` and `http://localhost:8080/**`

---

## Step 5: Deploy Edge Functions

Install the [Supabase CLI](https://supabase.com/docs/guides/cli), then:

```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF

supabase functions deploy load-events --no-verify-jwt
supabase functions deploy my-picks --no-verify-jwt
supabase functions deploy capture-event --no-verify-jwt
```

Set the required secrets:
```bash
# Tell load-events where to fetch events.json from (your fork)
supabase secrets set GITHUB_REPO=YOUR_ORG/community-calendar

# For event capture features
supabase secrets set ANTHROPIC_API_KEY=sk-ant-...
supabase secrets set OPENAI_API_KEY=sk-...       # optional, for audio transcription
```

**Note:** After deploying, verify "Require JWT" is OFF for all three functions in the Supabase Dashboard (Edge Functions → function name → Settings). Redeploying resets this to ON.

---

## Step 6: Configure GitHub Actions

In your GitHub repo, go to **Settings → Secrets and variables → Actions**:

**Secrets** (sensitive):
| Name | Value |
|------|-------|
| `SUPABASE_ANON_KEY` | Your legacy anon key (`eyJ...`) |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |

**Variables** (non-sensitive):
| Name | Value |
|------|-------|
| `SUPABASE_URL` | `https://YOUR_PROJECT_REF.supabase.co` |
| `SUPABASE_KEY` | Your publishable key (`sb_publishable_...`) |

The workflow also uses `${{ github.repository }}` (automatically set to your fork's `owner/repo`) — no configuration needed for that.

---

## Step 7: Enable GitHub Pages

In your repo → **Settings → Pages**:
- Source: **Deploy from a branch**
- Branch: `main`, folder: `/ (root)`

Your app will be live at `https://YOUR_ORG.github.io/community-calendar/`.

---

## Step 8: Trigger the First Data Load

Once GitHub Actions runs (or trigger it manually via **Actions → Generate Calendar → Run workflow**), events will be pushed to GitHub Pages. Then trigger the Supabase ingestion manually:

```bash
curl -X POST 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/load-events' \
  -H 'Authorization: Bearer YOUR_LEGACY_ANON_KEY'
```

---

## Local Development

```bash
python3 -m http.server 8080
# Visit http://localhost:8080/?city=santarosa
```

For Python scripts that talk to Supabase, set env vars locally:
```bash
export SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
export SUPABASE_KEY=sb_publishable_...
export ANTHROPIC_API_KEY=sk-ant-...
python3 scripts/classify_events_anthropic.py --limit 50 --dry-run
```

Or create a `.env` file (never commit this):
```
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_KEY=sb_publishable_...
ANTHROPIC_API_KEY=sk-ant-...
```
Then `export $(cat .env | xargs)` before running scripts.
