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
-- replaces URL-based NOT IN filter that exceeded PostgREST URL length limits).
-- Uses NOT EXISTS (unnest) instead of != ALL() because != ALL() with 3000+ items
-- hits Postgres statement timeout (57014). The unnest pattern is index-friendly
-- and works with the composite events_city_source_uid_idx index.
-- Guarded since 20260722210000_guard_delete_stale_events.sql (refuses a
-- >50% deletion driven by a short uid list). Service-role only, with a
-- pinned search_path, since 20261024140000_lock_down_definer_rpcs.sql.
CREATE OR REPLACE FUNCTION public.delete_stale_events(p_city text, p_source_uids text[])
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  current_count bigint;
  would_delete bigint;
  incoming_count bigint;
  deleted_count bigint;
BEGIN
  SELECT count(*) INTO current_count
  FROM public.events
  WHERE city = p_city;

  SELECT count(*) INTO would_delete
  FROM public.events e
  WHERE e.city = p_city
    AND e.source_uid IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM unnest(p_source_uids) AS u(uid)
      WHERE u.uid = e.source_uid
    );

  incoming_count := coalesce(array_length(p_source_uids, 1), 0);

  IF current_count > 0
     AND would_delete * 2 > current_count
     AND incoming_count < would_delete THEN
    RAISE EXCEPTION
      'delete_stale_events refused for city %: would delete % of % events '
      'with only % incoming source_uids (>50%% deletion driven by a short '
      'uid list looks like a partial load, not real churn)',
      p_city, would_delete, current_count, incoming_count;
  END IF;

  DELETE FROM public.events e
  WHERE e.city = p_city
    AND e.source_uid IS NOT NULL
    AND NOT EXISTS (
      SELECT 1 FROM unnest(p_source_uids) AS u(uid)
      WHERE u.uid = e.source_uid
    );
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.delete_stale_events(text, text[]) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.delete_stale_events(text, text[]) TO service_role;

-- Unique index on source_uid for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS events_source_uid_unique ON events (source_uid);

-- Index for city filtering
CREATE INDEX IF NOT EXISTS events_city_idx ON events (city);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS events_category_idx ON events (category);

-- Composite index for delete_stale_events (city + source_uid filter)
CREATE INDEX IF NOT EXISTS events_city_source_uid_idx ON events (city, source_uid);

-- Index for source filtering (kept for general source-column lookups;
-- refresh_source_names() now splits sources with string_to_array, not LIKE)
CREATE INDEX IF NOT EXISTS events_source_idx ON events (source);

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
