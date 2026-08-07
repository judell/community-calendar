-- Guard delete_stale_events against destructive partial loads.
--
-- delete_stale_events(p_city, p_source_uids) deletes every event in the
-- city whose source_uid is not in the supplied list. With no sanity check
-- on the list, any load-events POST with a short events array (a feed
-- outage that empties combined.ics, a partial build, a manual single-event
-- test) mass-deletes the rest of the city and cascades away picks,
-- category_overrides links, and event_enrichments. A one-event bloomington
-- POST nearly deleted ~5,700 events during the 2026-07-22 override test.
--
-- Guard rule (conservative; normal nightly churn observed is well under
-- 10%): refuse when the deletion would remove more than 50% of the city's
-- events AND the incoming uid list is smaller than the would-delete count.
-- The RAISE surfaces in load-events errorDetails, so a bad build fails
-- loudly instead of silently gutting a city. A legitimate mass removal
-- still has explicit paths (remove_feed, direct maintenance SQL).

CREATE OR REPLACE FUNCTION delete_stale_events(
    p_city text, p_source_uids text []
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  current_count bigint;
  would_delete bigint;
  incoming_count bigint;
  deleted_count bigint;
BEGIN
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

  DELETE FROM events e
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
