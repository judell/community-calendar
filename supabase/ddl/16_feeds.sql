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
  created_at timestamptz DEFAULT now(),
  UNIQUE(city, url)
);

ALTER TABLE feeds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read feeds" ON feeds FOR SELECT USING (true);

CREATE POLICY "Admin users can manage feeds" ON feeds FOR ALL
  USING (auth.uid() IN (SELECT user_id FROM admin_users));

-- Used by the Manage Feeds delete button (SECURITY DEFINER bypasses RLS).
-- Atomic since 20260807170000_atomic_remove_feed.sql: deletes the feed's
-- events (matched by the feed's city + name) and the feed row in one
-- transaction, returns what it deleted, and raises for an unknown id.
-- Callers that still pre-delete events by source+city simply leave 0
-- rows for the RPC to delete — backward compatible.
CREATE FUNCTION remove_feed(feed_id bigint)
RETURNS TABLE (events_deleted bigint, feed_deleted boolean)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  f record;
  ev_count bigint;
BEGIN
  SELECT city, name INTO f FROM feeds WHERE id = feed_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'remove_feed: no feed row with id %', feed_id;
  END IF;

  DELETE FROM events e WHERE e.city = f.city AND e.source = f.name;
  GET DIAGNOSTICS ev_count = ROW_COUNT;

  DELETE FROM feeds WHERE id = feed_id;

  RETURN QUERY SELECT ev_count, true;
END;
$$;

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
