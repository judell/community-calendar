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
  source_urls jsonb,        -- per-source URLs for aggregator attribution links
  category text,            -- auto-classified bucket (e.g., 'Music & Concerts', 'Arts & Culture')
  ics_categories text[],    -- CATEGORIES values from ICS source
  image_url text,           -- event image URL from ICS ATTACH or scraper
  all_day boolean DEFAULT false,  -- true for all-day events (VALUE=DATE in ICS)
  cluster_id text,             -- legacy compatibility field; removed after the transition build
  duplicate_group text,     -- opaque route group id; NULL = Separate (one row is one group)
  source_names text[],      -- structured, priority-ordered source names from the route
  duplicate_group_representative text, -- route's canonical member source_uid for the group
  created_at timestamptz DEFAULT now()
);

-- RPC for stale event cleanup (used by load-events edge function;
-- replaces URL-based NOT IN filter that exceeded PostgREST URL length limits)
--
-- Scoped by the ran-source manifest (20261022120000_ran_source_sweep.sql):
-- load-events passes p_sources = the source_ids whose ingestion succeeded this
-- build, so a source that ran and emptied is swept while a failed one keeps
-- its rows. p_sources IS NULL falls back to the old whole-city sweep.
--
-- The per-source 50% check is a signal, not a skip: a source that loses more
-- than half its rows is swept anyway and named in a WARNING, because the
-- manifest says it ran. A truncated scraper run looks the same as real churn
-- at this layer (ADR 0017). The aggregate guard on the legacy whole-city path
-- (20260722210000_guard_delete_stale_events.sql) is unchanged.
--
-- Uses NOT EXISTS (unnest) instead of != ALL() because != ALL() with 3000+ items
-- hits Postgres statement timeout. The unnest pattern is index-friendly and
-- works with the composite events_city_source_uid_idx index.
DROP FUNCTION IF EXISTS delete_stale_events(text, text[]);

CREATE FUNCTION delete_stale_events(
    p_city text, p_source_uids text[], p_sources text[] DEFAULT NULL
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  current_count bigint;
  would_delete bigint;
  incoming_count bigint;
  shrinking_sources text[] := ARRAY[]::text[];
  deleted_count bigint;
BEGIN
  IF p_sources IS NULL THEN
    SELECT count(*) INTO current_count
    FROM events
    WHERE city = p_city;

    SELECT count(*) INTO would_delete
    FROM events e
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
  ELSE
    SELECT coalesce(array_agg(s.source_id), ARRAY[]::text[])
      INTO shrinking_sources
    FROM (
      SELECT e.source_id,
             count(*) AS current_s,
             count(*) FILTER (
               WHERE NOT EXISTS (
                 SELECT 1 FROM unnest(p_source_uids) AS u(uid)
                 WHERE u.uid = e.source_uid
               )
             ) AS stale_s
      FROM events e
      WHERE e.city = p_city
        AND e.source_uid IS NOT NULL
        AND e.source_id = ANY(p_sources)
      GROUP BY e.source_id
    ) s
    WHERE s.stale_s * 2 > s.current_s;

    IF array_length(shrinking_sources, 1) IS NOT NULL THEN
      RAISE WARNING
        'delete_stale_events swept % source(s) for city % after losing more '
        'than half their rows: %',
        array_length(shrinking_sources, 1), p_city,
        array_to_string(shrinking_sources, ', ');
    END IF;
  END IF;

  DELETE FROM events e
  WHERE e.city = p_city
    AND e.source_uid IS NOT NULL
    AND (p_sources IS NULL OR e.source_id = ANY(p_sources))
    AND NOT EXISTS (
      SELECT 1 FROM unnest(p_source_uids) AS u(uid)
      WHERE u.uid = e.source_uid
    );
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;

-- Only load-events (service role) may sweep. Without this the default PUBLIC
-- EXECUTE grant let anonymous callers delete events directly through
-- PostgREST, bypassing the edge function (GHSA-qmc5-6cfg-38p7).
REVOKE EXECUTE ON FUNCTION public.delete_stale_events(text, text[], text[])
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.delete_stale_events(text, text[], text[])
  TO service_role;

-- Unique index on source_uid for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS events_source_uid_unique ON events (source_uid);

-- Index for city filtering
CREATE INDEX IF NOT EXISTS events_city_idx ON events (city);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS events_category_idx ON events (category);

-- Composite index for delete_stale_events (city + source_uid filter)
CREATE INDEX IF NOT EXISTS events_city_source_uid_idx ON events (city, source_uid);

-- Index for source filtering (kept for general source-column lookups;
-- refresh_source_names() prefers structured source_names, then falls back to source)
CREATE INDEX IF NOT EXISTS events_source_idx ON events (source);

-- Enable Row Level Security (public read access)
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read events
CREATE POLICY "Anyone can read events"
  ON events FOR SELECT
  USING (true);

-- Only the service role inserts events. The policy previously applied to
-- PUBLIC, so anonymous REST callers could inject rows and bypass the edge
-- function (GHSA-qmc5-6cfg-38p7).
CREATE POLICY "service_role inserts events"
  ON events FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Allow admin users to delete events
CREATE POLICY "Admin users can delete events"
  ON events FOR DELETE
  USING (auth.uid() IN (SELECT user_id FROM admin_users));
