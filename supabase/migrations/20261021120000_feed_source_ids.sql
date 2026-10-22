-- Feeds remember every source_id (output .ics stem) they have produced, so a
-- retired feed can delete the merge survivors it owns (#232, ADR 0017).
--
-- The build records the value: download_feeds.py for ics_url/curator rows and
-- run_scrapers_from_db.py for scraper rows. The array is a history because a
-- feed's url can change (see the convert_*_feed_to_scraper migrations) and
-- rows built under the older stem must still be attributable.
ALTER TABLE feeds ADD COLUMN source_ids text[] NOT NULL DEFAULT '{}';

-- remove_feed now matches by source_id (the feed's own rows, including a merge
-- survivor whose comma-joined `source` hides its owner) and keeps the old
-- exact-name match for rows built before the mapping existed. The name arm
-- skips rows another same-city feed's history already owns, so feeds that
-- share a display name cannot delete each other's events once both have
-- recorded a history. A feed with no recorded history falls back to the name
-- match with a warning.
CREATE OR REPLACE FUNCTION remove_feed(feed_id bigint)
RETURNS TABLE (events_deleted bigint, feed_deleted boolean)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  f record;
  has_history boolean;
  shared_ids text[];
  ev_count bigint;
BEGIN
  SELECT city, name, source_ids INTO f FROM feeds WHERE id = feed_id;
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
  -- rows share one (both slug to events_search_events_ics).
  shared_ids := ARRAY(
    SELECT unnest(f.source_ids)
    INTERSECT
    SELECT unnest(o.source_ids)
    FROM feeds o
    WHERE o.city = f.city
      AND o.id <> feed_id
  );
  IF cardinality(shared_ids) > 0 THEN
    RAISE WARNING
      'remove_feed: feed % (id %) shares source_id(s) % with another feed; those rows are kept',
      f.name, feed_id, array_to_string(shared_ids, ', ');
  END IF;

  DELETE FROM events e
  WHERE e.city = f.city
    AND (
      (has_history AND e.source_id = ANY(f.source_ids) AND NOT e.source_id = ANY(shared_ids))
      OR (
        e.source = f.name
        AND NOT EXISTS (
          SELECT 1 FROM feeds o
          WHERE o.city = f.city
            AND o.id <> feed_id
            AND e.source_id = ANY(o.source_ids)
        )
      )
    );
  GET DIAGNOSTICS ev_count = ROW_COUNT;

  DELETE FROM feeds WHERE id = feed_id;

  RETURN QUERY SELECT ev_count, true;
END;
$$;


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
