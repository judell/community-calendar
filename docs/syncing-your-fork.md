# Syncing Your Fork (April 2026)

If you forked community-calendar recently and hit the DDL ordering bug ([#52](https://github.com/judell/community-calendar/issues/52)), this guide explains what changed upstream and how to get your fork up to date.

## What changed

Two big things landed on April 7-8:

### 1. Manage Feeds: a new way to add and remove sources

Previously, adding a feed meant editing `feeds.txt` by hand and pushing a commit. Now there's a **Manage Feeds** dialog in the app (the RSS icon in the header, visible to admins). It lets you:

- **Add a feed** — paste an ICS URL, give it a name, validate it (the app fetches and parses the feed to show a preview), then save. The feed goes into the `feeds` table with `status=pending` and gets picked up by the next build.
- **Delete a feed** — removes all its events from the database immediately and marks the feed as removed.

This is backed by:

- A new **`feeds` table** (`supabase/ddl/16_feeds.sql`) that stores all calendar sources (ICS URLs, scrapers, curators) with city, name, status, and feed type.
- A new **`validate-feed` edge function** that fetches an ICS URL server-side, parses it, and returns a preview of upcoming events. It also detects recurring events (RRULE) and warns that the build will expand them.
- Two new **RPC functions**: `get_source_counts` (used by the sources dialog) and `remove_feed` (used by the delete button).

### 2. Build pipeline: feeds table is now the source of truth

The build pipeline no longer depends on `feeds.txt` as its primary input. Instead:

- **`download_feeds.py`** now queries the `feeds` table for active ICS URLs and curator feeds. It falls back to reading `feeds.txt` if `SUPABASE_URL` isn't set (so forks without a feeds table still work).
- A new **`export_feeds_txt.py`** script runs during the build and regenerates `feeds.txt` from the database. This keeps `feeds.txt` in sync as a human-readable record and ensures `combine_ics.py` (which parses feeds.txt for display names) works correctly.
- The workflow gained an **"Export feeds.txt from DB"** step that runs after downloading feeds and before combining ICS files.

### 3. Other improvements

- **Unauthenticated source toggling** — users who aren't signed in can now hide/show sources via localStorage.
- **DDL ordering fix** — `08_admin_users.sql` was renamed to `01a_admin_users.sql` so the `admin_users` table exists before the events table's RLS policy references it. This is the fix for [#52](https://github.com/judell/community-calendar/issues/52).

## Fixing the JWT error

If you see this in the browser console:

```
[xmlui] Expected 3 parts in JWT; got 1
```

Your app is still using the upstream **publishable key** (`sb_publishable_...`) instead of your project's **anon key** (a long `eyJ...` JWT string). The publishable key isn't a JWT, so PostgREST rejects it.

Find your anon key in the Supabase dashboard: **Settings > API > Project API keys > `anon` `public`**.

Update it in two places:

**`xmlui/config.json`** — replace the `supabasePublishableKey` value:
```json
{
  "appGlobals": {
    "supabaseUrl": "https://YOUR_PROJECT_REF.supabase.co",
    "supabasePublishableKey": "eyJ...your-anon-key..."
  }
}
```

**`xmlui/index.html`** — replace both constants (~line 116-117):
```javascript
const SUPABASE_URL = 'https://YOUR_PROJECT_REF.supabase.co';
const SUPABASE_KEY = 'eyJ...your-anon-key...';
```

## Syncing with upstream

### Step 1: Pull upstream changes

```bash
git remote add upstream https://github.com/judell/community-calendar.git
git fetch upstream
git merge upstream/main
```

You'll likely get a merge conflict in `.github/workflows/generate-calendar.yml` because the upstream workflow has city-specific scraper blocks that don't apply to forks. Resolve it by keeping your version of scraper-related sections, but make sure you pick up the new "Export feeds.txt from DB" step. It goes right before "Combine ICS files":

```yaml
    - name: Export feeds.txt from DB
      env:
        SUPABASE_URL: ${{ vars.SUPABASE_URL }}
        SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
      run: |
        IFS=',' read -ra CITIES <<< "${{ steps.locations.outputs.list }}"
        for city in "${CITIES[@]}"; do
          city=$(echo "$city" | xargs)
          python scripts/export_feeds_txt.py "$city"
        done
```

For conflicts in `config.json` or `index.html`, keep **your** values (your Supabase URL and anon key).

### Step 2: Create the feeds table

Run this in your Supabase SQL Editor (Dashboard > SQL Editor > New query):

```sql
-- feeds table
CREATE TABLE IF NOT EXISTS feeds (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  city text NOT NULL,
  url text NOT NULL,
  name text NOT NULL,
  status text NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'pending', 'removed')),
  feed_type text NOT NULL
    CHECK (feed_type IN ('ics_url', 'scraper', 'curator')),
  scraper_cmd text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(city, url)
);

ALTER TABLE feeds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read feeds" ON feeds
  FOR SELECT USING (true);

CREATE POLICY "Admin users can manage feeds" ON feeds
  FOR ALL USING (auth.uid() IN (SELECT user_id FROM admin_users));
```

### Step 3: Create the RPC functions

Still in the SQL Editor, run:

```sql
-- Used by the sources dialog to show event counts per source
CREATE OR REPLACE FUNCTION get_source_counts(target_city text)
RETURNS TABLE(name text, event_count bigint)
LANGUAGE sql STABLE
AS $$
  SELECT source AS name, COUNT(*) AS event_count
  FROM events
  WHERE city = target_city
    AND source IS NOT NULL
    AND source NOT LIKE '%,%'
  GROUP BY source
  ORDER BY source;
$$;

-- Used by the Manage Feeds delete button (SECURITY DEFINER bypasses RLS)
CREATE OR REPLACE FUNCTION remove_feed(feed_id bigint)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
  DELETE FROM feeds WHERE id = feed_id;
END;
$$;
```

### Step 4: Seed the feeds table from your feeds.txt

If you already have feeds in `feeds.txt`, run the seed script to populate the table so the Manage Feeds dialog shows them:

```bash
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co \
SUPABASE_SERVICE_KEY=your-service-role-key \
python scripts/seed_feeds_from_txt.py yourcity
```

This parses `cities/yourcity/feeds.txt`, extracts feed names from the comment lines above each URL, and inserts them into the `feeds` table. Duplicates are skipped automatically.

### Step 5: Deploy the validate-feed edge function

The Manage Feeds dialog needs the `validate-feed` edge function to preview feeds before adding them. Deploy it using the Supabase CLI:

```bash
supabase functions deploy validate-feed --project-ref YOUR_PROJECT_REF
```

Or if you don't have the Supabase CLI installed, you can deploy it from the Supabase dashboard: **Edge Functions > Deploy a new function**, name it `validate-feed`, and paste the contents of `supabase/functions/validate-feed/index.ts`.

After deploying, go to **Edge Functions > validate-feed > Details** and make sure "Require JWT" is **disabled** (the function handles auth itself via the Authorization header).

### Step 6: Push and build

```bash
git add -A
git commit -m "Sync with upstream: feeds table, manage feeds, build pipeline"
git push origin main
```

Then trigger a build: go to your repo's **Actions** tab, select the **generate-calendar** workflow, and click **Run workflow**. Or use the CLI:

```bash
cc-cli build
```

## Verifying it works

After the build completes:

1. Visit your calendar site and sign in
2. Click the RSS icon (Manage Feeds) in the header — you should see your feeds listed
3. Try adding a test feed: paste any public ICS URL, give it a name, click Validate, then Add Feed
4. The feed will appear in the next build
