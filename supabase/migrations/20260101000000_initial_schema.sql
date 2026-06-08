-- Initial schema for Community Calendar
-- This represents the base schema before incremental migrations were added.
-- DO NOT modify this file - subsequent migrations build on top of it.

-- Enable required extensions

-- HTTP requests from database (for scheduled jobs)
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Scheduled jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Admin users table - server-authorized access for privileged UI/actions

CREATE TABLE IF NOT EXISTS admin_users (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Users can only view their own admin row (presence means admin)
CREATE POLICY "Users can view own admin status"
  ON admin_users FOR SELECT
  USING (auth.uid() = user_id);

-- Service role manages admin grants/revokes
CREATE POLICY "Service role can manage admin users"
  ON admin_users FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Events table - stores calendar events from all sources

CREATE TABLE IF NOT EXISTS events (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  title text NOT NULL,
  start_time timestamptz NOT NULL,
  end_time timestamptz,
  location text,
  description text,
  url text,
  city text,                -- e.g., 'santarosa', 'sebastopol', 'cotati'
  source text,              -- e.g., 'bohemian', 'pressdemocrat' (no date suffix)
  source_id text,           -- filename-derived source identifier for curator reference
  source_uid text UNIQUE,   -- unique ID from source for deduplication
  transcript text,          -- Whisper transcript for audio-captured events
  cluster_id text,          -- groups similar events within same timeslot for UI display
  source_urls jsonb,        -- per-source URLs for aggregator attribution links
  category text,            -- auto-classified bucket (e.g., 'Music & Concerts', 'Arts & Culture')
  ics_categories text[],    -- CATEGORIES values from ICS source
  image_url text,           -- event image URL from ICS ATTACH or scraper
  all_day boolean DEFAULT false,  -- true for all-day events (VALUE=DATE in ICS)
  created_at timestamptz DEFAULT now()
);

-- RPC for stale event cleanup (used by load-events edge function;
-- replaces URL-based NOT IN filter that exceeded PostgREST URL length limits)
CREATE OR REPLACE FUNCTION delete_stale_events(p_city text, p_source_uids text[])
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  deleted_count bigint;
BEGIN
  DELETE FROM events
  WHERE city = p_city
    AND source_uid IS NOT NULL
    AND source_uid != ALL(p_source_uids)
  ;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;

-- Unique index on source_uid for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS events_source_uid_unique ON events (source_uid);

-- Index for city filtering
CREATE INDEX IF NOT EXISTS events_city_idx ON events (city);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS events_category_idx ON events (category);

-- NOTE: events_source_idx added in migration 20260606012632

-- Enable Row Level Security (public read access)
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read events
CREATE POLICY "Anyone can read events"
  ON events FOR SELECT
  USING (true);

-- Allow service functions to insert events
CREATE POLICY "Service function can insert events"
  ON events FOR INSERT
  WITH CHECK (true);

-- Allow admin users to delete events
CREATE POLICY "Admin users can delete events"
  ON events FOR DELETE
  USING (auth.uid() IN (SELECT user_id FROM admin_users));

-- Picks table - stores user's saved/favorited events

CREATE TABLE IF NOT EXISTS picks (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  event_id bigint NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, event_id)
);

-- Enable Row Level Security
ALTER TABLE picks ENABLE ROW LEVEL SECURITY;

-- Users can only see their own picks
CREATE POLICY "Users can view own picks"
  ON picks FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own picks
CREATE POLICY "Users can insert own picks"
  ON picks FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can delete their own picks
CREATE POLICY "Users can delete own picks"
  ON picks FOR DELETE
  USING (auth.uid() = user_id);

-- Feed tokens table - unique token per user for ICS feed access

CREATE TABLE IF NOT EXISTS feed_tokens (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
  token uuid DEFAULT gen_random_uuid() NOT NULL UNIQUE,
  created_at timestamptz DEFAULT now()
);

-- Note: token column is UNIQUE, which auto-creates feed_tokens_token_key index.
-- No additional index needed for token lookups.

-- Enable Row Level Security
ALTER TABLE feed_tokens ENABLE ROW LEVEL SECURITY;

-- Users can only view their own feed token
CREATE POLICY "Users can view own feed token"
  ON feed_tokens FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own feed token (created on first sign-in)
CREATE POLICY "Users can insert own feed token"
  ON feed_tokens FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Event enrichments table - curator overrides/additions per event
-- Self-standing: enrichments store their own title/start_time/city so they
-- survive even if the original event row is deleted.

CREATE TABLE IF NOT EXISTS event_enrichments (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,  -- nullable
  curator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  rrule text,
  url text,
  description text,
  location text,
  end_time timestamptz,
  categories text[],
  notes text,
  title text,            -- copied from event at creation
  start_time timestamptz, -- copied from event at creation
  city text,             -- copied from event at creation
  curator_name text,     -- display name for source attribution
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(event_id, curator_id)
);

-- Index for event lookups
CREATE INDEX IF NOT EXISTS idx_event_enrichments_event_id ON event_enrichments (event_id);

-- Index for curator lookups
CREATE INDEX IF NOT EXISTS idx_event_enrichments_curator_id ON event_enrichments (curator_id);

-- Enable Row Level Security
ALTER TABLE event_enrichments ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read enrichments
CREATE POLICY "Enrichments are publicly readable"
  ON event_enrichments FOR SELECT
  USING (true);

-- Users can insert their own enrichments
CREATE POLICY "Users can insert own enrichments"
  ON event_enrichments FOR INSERT
  WITH CHECK (auth.uid() = curator_id);

-- Users can update their own enrichments
CREATE POLICY "Users can update own enrichments"
  ON event_enrichments FOR UPDATE
  USING (auth.uid() = curator_id);

-- Users can delete their own enrichments
CREATE POLICY "Users can delete own enrichments"
  ON event_enrichments FOR DELETE
  USING (auth.uid() = curator_id);

-- View for distinct city names (used by city picker UI)
-- security_invoker so the view runs with the querying user's RLS, not the owner's
CREATE OR REPLACE VIEW distinct_cities WITH (security_invoker = true) AS
SELECT DISTINCT city FROM events WHERE city IS NOT NULL ORDER BY city;

REVOKE ALL ON distinct_cities FROM anon, authenticated;
GRANT SELECT ON distinct_cities TO anon, authenticated;

-- Admin GitHub users table - allows preapproval before first sign-in

CREATE TABLE IF NOT EXISTS admin_github_users (
  github_user text PRIMARY KEY,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE admin_github_users ENABLE ROW LEVEL SECURITY;

-- Helper function: reads GitHub username from server-side auth.users record
-- (not from the client-writable JWT user_metadata claim)
CREATE OR REPLACE FUNCTION public.get_my_github_username()
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT raw_user_meta_data->>'user_name'
  FROM auth.users
  WHERE id = auth.uid();
$$;

-- Authenticated users can only read their own GitHub username row
CREATE POLICY "Users can view own github admin status"
  ON admin_github_users FOR SELECT
  TO authenticated
  USING (github_user = coalesce(public.get_my_github_username(), ''));

-- Service role manages admin grants/revokes
CREATE POLICY "Service role can manage github admin users"
  ON admin_github_users FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- User settings table - per-user, per-city preferences (e.g., hidden sources)

CREATE TABLE IF NOT EXISTS user_settings (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  city text NOT NULL,
  hidden_sources text[] DEFAULT '{}',
  one_click_pick boolean NOT NULL DEFAULT false,
  layout_mode text DEFAULT 'list',
  image_mode text DEFAULT 'everywhere',
  dashboard jsonb DEFAULT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id, city)
);

-- Enable Row Level Security
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- Users can only view their own settings
CREATE POLICY "Users can view own settings"
  ON user_settings FOR SELECT
  USING (auth.uid() = user_id);

-- Users can only insert their own settings
CREATE POLICY "Users can insert own settings"
  ON user_settings FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can only update their own settings
CREATE POLICY "Users can update own settings"
  ON user_settings FOR UPDATE
  USING (auth.uid() = user_id);

-- Admin Google users table - allows preapproval before first sign-in

CREATE TABLE IF NOT EXISTS admin_google_users (
  google_email text PRIMARY KEY,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE admin_google_users ENABLE ROW LEVEL SECURITY;

-- Helper function: reads email from server-side auth.users record
-- (not from the client-writable JWT claims)
CREATE OR REPLACE FUNCTION public.get_my_google_email()
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT email
  FROM auth.users
  WHERE id = auth.uid();
$$;

-- Authenticated users can only read their own Google email row
CREATE POLICY "Users can view own google admin status"
  ON admin_google_users FOR SELECT
  TO authenticated
  USING (google_email = coalesce(public.get_my_google_email(), ''));

-- Service role manages admin grants/revokes
CREATE POLICY "Service role can manage google admin users"
  ON admin_google_users FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Source suggestions table - anonymous community submissions for new calendar sources

CREATE TABLE IF NOT EXISTS source_suggestions (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  city text NOT NULL,
  name text NOT NULL,
  url text,
  feed_type text,
  notes text,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE source_suggestions ENABLE ROW LEVEL SECURITY;

-- Anyone can insert suggestions (anonymous, no auth required)
CREATE POLICY "Anyone can insert suggestions"
  ON source_suggestions FOR INSERT
  WITH CHECK (true);

-- Anyone can read suggestions
CREATE POLICY "Anyone can read suggestions"
  ON source_suggestions FOR SELECT
  USING (true);

-- Category overrides: curator corrections to LLM-assigned event categories
-- These feed back as few-shot examples to improve future classifications

CREATE TABLE IF NOT EXISTS category_overrides (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,
  category text NOT NULL,
  original_category text,
  curator_id uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  UNIQUE(event_id)
);

ALTER TABLE category_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read overrides" ON category_overrides FOR SELECT USING (true);
CREATE POLICY "Auth users can insert overrides" ON category_overrides FOR INSERT WITH CHECK (auth.uid() = curator_id);
CREATE POLICY "Auth users can update own overrides" ON category_overrides FOR UPDATE USING (auth.uid() = curator_id);

-- Trigger: store original category then propagate override to events.category
CREATE OR REPLACE FUNCTION apply_category_override()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.original_category IS NULL THEN
    SELECT category INTO NEW.original_category FROM events WHERE id = NEW.event_id;
  END IF;
  UPDATE events SET category = NEW.category WHERE id = NEW.event_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_category_override
  BEFORE INSERT OR UPDATE ON category_overrides
  FOR EACH ROW EXECUTE FUNCTION apply_category_override();

-- SECURITY DEFINER function to resolve curator name without exposing auth.users
CREATE OR REPLACE FUNCTION public.get_curator_name(curator_uuid uuid)
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT raw_user_meta_data->>'user_name'
  FROM auth.users
  WHERE id = curator_uuid;
$$;

-- View for report: uses function instead of direct auth.users join
CREATE OR REPLACE VIEW category_overrides_view WITH (security_invoker = true) AS
SELECT
  co.id,
  co.category,
  co.original_category,
  co.created_at,
  co.event_id,
  public.get_curator_name(co.curator_id) AS curator_name
FROM category_overrides co;

REVOKE ALL ON category_overrides_view FROM anon, authenticated;
GRANT SELECT ON category_overrides_view TO anon, authenticated;

-- Source names table - aggregated source counts per city

CREATE TABLE IF NOT EXISTS source_names (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  city text NOT NULL,
  name text NOT NULL,
  event_count integer DEFAULT 0,
  UNIQUE(city, name)
);

-- Enable Row Level Security (public read)
ALTER TABLE source_names ENABLE ROW LEVEL SECURITY;

-- Anyone can read source names
CREATE POLICY "source_names_read" ON source_names FOR SELECT USING (true);

-- Original refresh_source_names() implementation
-- (Rewritten in migration 20260606013000)
CREATE OR REPLACE FUNCTION refresh_source_names(target_city text)
RETURNS void
SET statement_timeout TO '0'
AS $$
BEGIN
  -- Upsert distinct non-comma sources for this city
  INSERT INTO source_names (city, name, event_count)
  SELECT city, source, COUNT(*)
  FROM events
  WHERE city = target_city
    AND source IS NOT NULL
    AND source NOT LIKE '%,%'
  GROUP BY city, source
  ON CONFLICT (city, name) DO UPDATE SET event_count = EXCLUDED.event_count;

  -- Update counts for sources that also appear in comma-separated merged sources
  UPDATE source_names sn
  SET event_count = (
    SELECT COUNT(DISTINCT e.id)
    FROM events e
    WHERE e.city = sn.city
      AND (e.source = sn.name
        OR e.source LIKE sn.name || ', %'
        OR e.source LIKE '%, ' || sn.name
        OR e.source LIKE '%, ' || sn.name || ', %')
  )
  WHERE sn.city = target_city;

  -- Remove sources that no longer have events
  DELETE FROM source_names
  WHERE city = target_city AND event_count = 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Feeds table - all calendar sources (ICS URLs, scrapers, curators) per city
-- Source of truth for what feeds are in the system. Replaces feeds.txt and pending_feeds.
-- NOTE: fallback_url column added in migration 20260510180000

CREATE TABLE IF NOT EXISTS feeds (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  city text NOT NULL,
  url text NOT NULL,
  name text NOT NULL,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'pending', 'removed')),
  feed_type text NOT NULL CHECK (feed_type IN ('ics_url', 'scraper', 'curator')),
  scraper_cmd text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(city, url)
);

ALTER TABLE feeds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read feeds" ON feeds FOR SELECT USING (true);

CREATE POLICY "Admin users can manage feeds" ON feeds FOR ALL
  USING (auth.uid() IN (SELECT user_id FROM admin_users));

-- Used by the Manage Feeds delete button (SECURITY DEFINER bypasses RLS)
CREATE OR REPLACE FUNCTION remove_feed(feed_id bigint)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
  DELETE FROM feeds WHERE id = feed_id;
END;
$$;

-- Deduplicated events materialized view
-- Server-side deduplication of events by city + normalized title + start_time.
-- Refreshed after load-events runs so the app can query pre-deduplicated rows.

CREATE MATERIALIZED VIEW IF NOT EXISTS deduplicated_events AS
SELECT
    min(id) AS id,
    (array_agg(title ORDER BY e.id))[1] AS title,
    start_time,
    (array_agg(end_time ORDER BY e.id) FILTER (WHERE end_time IS NOT NULL))[1] AS end_time,
    (array_agg(url ORDER BY e.id) FILTER (WHERE url IS NOT NULL AND url <> ''))[1] AS url,
    (array_agg(location ORDER BY e.id) FILTER (WHERE location IS NOT NULL))[1] AS location,
    (array_agg(description ORDER BY e.id) FILTER (WHERE description IS NOT NULL))[1] AS description,
    string_agg(DISTINCT source, ', ') AS source,
    (array_agg(source_uid ORDER BY e.id))[1] AS source_uid,
    min(created_at) AS created_at,
    (array_agg(city ORDER BY e.id))[1] AS city,
    (array_agg(transcript ORDER BY e.id) FILTER (WHERE transcript IS NOT NULL))[1] AS transcript,
    (array_agg(source_id ORDER BY e.id))[1] AS source_id,
    (array_agg(cluster_id ORDER BY e.id) FILTER (WHERE cluster_id IS NOT NULL))[1] AS cluster_id,
    (array_agg(source_urls ORDER BY e.id) FILTER (WHERE source_urls IS NOT NULL))[1] AS source_urls,
    (array_agg(category ORDER BY e.id) FILTER (WHERE category IS NOT NULL))[1] AS category,
    (SELECT ic.ics_categories
       FROM events ic
      WHERE ic.ics_categories IS NOT NULL AND ic.id = min(e.id)) AS ics_categories,
    (array_agg(image_url ORDER BY e.id) FILTER (WHERE image_url IS NOT NULL))[1] AS image_url,
    bool_or(all_day) AS all_day,
    array_agg(id ORDER BY e.id) AS merged_ids
FROM events e
WHERE source <> 'poster_capture'
GROUP BY city, lower(TRIM(BOTH FROM title)), start_time
ORDER BY start_time;

-- Unique index required for REFRESH MATERIALIZED VIEW CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS deduplicated_events_id_idx ON deduplicated_events (id);

-- NOTE: separate city/start_time indexes replaced by a compound index in
-- migration 20260421182300 (deduplicated_events_city_start_time_idx)
CREATE INDEX IF NOT EXISTS deduplicated_events_city_idx ON deduplicated_events (city);
CREATE INDEX IF NOT EXISTS deduplicated_events_start_time_idx ON deduplicated_events (start_time);

GRANT SELECT ON deduplicated_events TO anon, authenticated, service_role;

-- RPC used by the nightly build after load-events completes.
CREATE OR REPLACE FUNCTION public.refresh_deduplicated_events()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout TO '0'
AS $function$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY deduplicated_events;
END;
$function$;

GRANT EXECUTE ON FUNCTION public.refresh_deduplicated_events() TO anon, authenticated, service_role;
