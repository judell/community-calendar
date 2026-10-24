-- feeds: all calendar sources (ICS URLs, scrapers, curators) per city
-- Source of truth for what feeds are in the system.
-- Replaces feeds.txt and pending_feeds.

CREATE TABLE feeds (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  city text NOT NULL,
  url text NOT NULL,
  name text NOT NULL,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'pending', 'removed')),
  feed_type text NOT NULL CHECK (feed_type IN ('ics_url', 'scraper', 'curator')),
  scraper_cmd text,
  fallback_url text,
  source_ids text[] NOT NULL DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  UNIQUE(city, url)
);

ALTER TABLE feeds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read feeds" ON feeds FOR SELECT USING (true);

CREATE POLICY "Admin users can manage feeds" ON feeds FOR ALL
  USING (auth.uid() IN (SELECT user_id FROM admin_users));

-- Used by the Manage Feeds delete button (SECURITY DEFINER bypasses RLS).
-- Atomic since 20260807170000_atomic_remove_feed.sql: deletes the feed's
-- events and the feed row in one transaction, returns what it deleted, and
-- raises for an unknown id.
--
-- Admin-only and unreachable by anon since
-- 20261024130000_secure_definer_functions.sql (GHSA-69r3-3gxw-fm4g): the body
-- requires an admin_users row for auth.uid(), and EXECUTE is revoked from
-- PUBLIC and anon. The Manage Feeds dialog passes with the admin's JWT; a
-- direct SQL session must set the claim first:
--   select set_config('request.jwt.claims', '{"sub":"<admin-user-uuid>"}', true);
--   select remove_feed(<feed-id>);
--
-- Ownership is `events.source_id = ANY(feeds.source_ids)` — the history of
-- .ics stems the build produced for this feed. A merge survivor's `source` is
-- the comma-joined member names, so only source_id identifies which feed owns
-- it; matching it by name would delete a survivor owned by another feed and
-- cascade away that event's saved picks (ADR 0017). The exact-name arm keeps
-- rows built before the mapping existed (20261021120000_feed_source_ids.sql)
-- and skips rows that another same-city feed's history already owns, so two
-- feeds that share a display name cannot delete each other's events once both
-- have recorded a history.
CREATE FUNCTION remove_feed(feed_id bigint)
RETURNS TABLE (events_deleted bigint, feed_deleted boolean)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  f record;
  has_history boolean;
  shared_ids text[];
  ev_count bigint;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM public.admin_users WHERE user_id = auth.uid()
  ) THEN
    RAISE EXCEPTION 'remove_feed: admin required' USING ERRCODE = '42501';
  END IF;

  SELECT city, name, source_ids INTO f FROM public.feeds WHERE id = feed_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'remove_feed: no feed row with id %', feed_id;
  END IF;

  has_history := cardinality(f.source_ids) > 0;
  IF NOT has_history THEN
    RAISE WARNING
      'remove_feed: feed % (id %) has no recorded source_id; matching by name only',
      f.name, feed_id;
  END IF;

  -- A stem that two same-city feeds both claim identifies neither exclusively,
  -- so rows carrying it are left in place. Bloomington's two events.in.gov
  -- rows shared one (both slugged to events_search_events_ics) until #240
  -- retired the duplicate feed; the guard covers any future pair.
  shared_ids := ARRAY(
    SELECT unnest(f.source_ids)
    INTERSECT
    SELECT unnest(o.source_ids)
    FROM public.feeds o
    WHERE o.city = f.city
      AND o.id <> feed_id
  );
  IF cardinality(shared_ids) > 0 THEN
    RAISE WARNING
      'remove_feed: feed % (id %) shares source_id(s) % with another feed; those rows are kept',
      f.name, feed_id, array_to_string(shared_ids, ', ');
  END IF;

  DELETE FROM public.events e
  WHERE e.city = f.city
    AND (
      (has_history AND e.source_id = ANY(f.source_ids) AND NOT e.source_id = ANY(shared_ids))
      OR (
        e.source = f.name
        AND NOT EXISTS (
          SELECT 1 FROM public.feeds o
          WHERE o.city = f.city
            AND o.id <> feed_id
            AND e.source_id = ANY(o.source_ids)
        )
      )
    );
  GET DIAGNOSTICS ev_count = ROW_COUNT;

  DELETE FROM public.feeds WHERE id = feed_id;

  RETURN QUERY SELECT ev_count, true;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.remove_feed(bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.remove_feed(bigint) TO authenticated;

-- Insert-time validation for scraper rows
-- (since 20260807171000_insert_time_scraper_validation.sql):
-- a BEFORE INSERT OR UPDATE trigger (feeds_validate_scraper_row →
-- validate_scraper_row()) rejects non-removed scraper rows whose url is
-- not an output path (cities/<city>/<file>.ics — never an http(s) URL),
-- whose scraper_cmd is missing/empty, or whose scraper_cmd does not
-- start with "python scrapers/" or "python scripts/". Removed-status
-- tombstones are exempt. This enforces cleanup-plan item 4 on every
-- write path (Manage Feeds, pending-feeds processing, backfill sync,
-- ad hoc SQL) ahead of DB-first scraper execution.
CREATE OR REPLACE FUNCTION validate_scraper_row()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.feed_type = 'scraper' AND coalesce(NEW.status, 'active') <> 'removed' THEN
    IF NEW.url IS NULL OR NEW.url !~ '^cities/[a-z0-9-]+/[A-Za-z0-9._-]+\.ics$' THEN
      RAISE EXCEPTION
        'scraper row rejected: url must be an output path like cities/<city>/<file>.ics, got %',
        coalesce(NEW.url, '<null>');
    END IF;
    IF NEW.scraper_cmd IS NULL OR btrim(NEW.scraper_cmd) = '' THEN
      RAISE EXCEPTION
        'scraper row rejected: scraper_cmd is required for non-removed scraper rows (url %)',
        NEW.url;
    END IF;
    IF NEW.scraper_cmd !~ '^python (scrapers|scripts)/' THEN
      RAISE EXCEPTION
        'scraper row rejected: scraper_cmd must start with "python scrapers/" or "python scripts/", got %',
        left(NEW.scraper_cmd, 80);
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER feeds_validate_scraper_row
BEFORE INSERT OR UPDATE ON feeds
FOR EACH ROW EXECUTE FUNCTION validate_scraper_row();


-- Append one source_id without a read-modify-write. Scheduled and manually
-- dispatched builds have no concurrency group, so a PATCH built from an older
-- read would otherwise erase a stem another run just recorded.
CREATE OR REPLACE FUNCTION record_feed_source(p_feed_id bigint, p_source_id text)
RETURNS void
LANGUAGE sql
AS $$
  UPDATE feeds
  SET source_ids = array_append(source_ids, p_source_id)
  WHERE id = p_feed_id
    AND p_source_id <> ''
    AND NOT p_source_id = ANY(source_ids);
$$;
