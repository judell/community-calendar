-- Migration: Retire Bloomington's duplicate events.in.gov feed (issue #240)
--
-- Bloomington registers two feeds on one events.in.gov search endpoint:
-- "Indiana State Events" (no browse_type) and "Monroe County Government"
-- (browse_type=school). Both serve the same calendar: on 2026-10-23 the two
-- URLs returned byte-identical ICS — 133 UIDs, all Monroe County Government
-- meetings (courthouse, commissioners, plan commission), differing only in
-- DTSTAMP. browse_type=school filters nothing, so "Indiana State Events" is a
-- mislabeled duplicate, not a statewide source.
--
-- They also share one stem (events_search_events_ics) because slugify() drops
-- the query string, so download_feeds.py wrote both to one .ics file and the
-- second fetch overwrote the first. Retiring the duplicate removes the
-- collision without changing any source_id: the surviving row keeps that stem
-- and owns the events, which the second fetch already stamped as its own.
--
-- The row becomes a status='removed' tombstone rather than being deleted, so
-- the UNIQUE(city, url) row makes process_pending_feeds ignore a re-add via
-- resolution=ignore-duplicates; a deleted row would let the same URL return as
-- a new feed and recreate the collision. Removing the row's source_ids clears
-- a stem it no longer produces, so remove_feed's shared-stem guard does not
-- treat the survivor's stem as shared with a feed that has no build.
--
-- No events are deleted. Every row belongs to the survivor and the next build
-- re-stamps it through the source_uid upsert; matching the retired feed's name
-- would drop rows whose picks must stay.
--
-- Idempotent, and a no-op on a fork that carries neither row. Retiring only
-- when the survivor is present keeps a fork from losing its only events.in.gov
-- coverage.
DO $$
DECLARE
  survivor_url text := 'https://events.in.gov/search/events.ics?browse_type=school&event_types%5B%5D=49056849667840';
  retired_url text := 'https://events.in.gov/search/events.ics?event_types%5B%5D=49056849667840';
  retired int;
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM feeds
    WHERE city = 'bloomington'
      AND url = survivor_url
      AND status <> 'removed'
  ) THEN
    RAISE NOTICE 'events.in.gov duplicate not retired: survivor row absent';
    RETURN;
  END IF;

  UPDATE feeds
  SET status = 'removed', source_ids = '{}'
  WHERE city = 'bloomington'
    AND url = retired_url
    AND status <> 'removed';
  GET DIAGNOSTICS retired = ROW_COUNT;

  IF retired = 0 THEN
    RAISE NOTICE 'events.in.gov duplicate not retired: row absent or already removed';
  END IF;
END $$;
