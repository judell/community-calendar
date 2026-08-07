-- Make feed removal atomic (cleanup-plan items 5-6, DB-first prerequisite).
--
-- remove_feed(feed_id) previously deleted only the feeds row; every caller
-- (the Manage Feeds dialog, agents following its sequence) had to delete
-- the source's events first by source name + city — a two-step
-- client-orchestrated flow that could half-complete: events deleted but
-- the row still active, or the row gone with its events orphaned.
--
-- Now the RPC looks up the feed's city + name, deletes its events and the
-- row inside one transaction (the function body), and reports what it
-- deleted. It raises for an unknown id so callers can report truthfully
-- instead of treating a no-op as success. Backward compatible: callers
-- that still pre-delete events simply leave 0 rows for the RPC to delete.
--
-- DROP + CREATE because the return type changes (void -> counts); the
-- name and argument list are unchanged, so the PostgREST RPC path
-- (/rest/v1/rpc/remove_feed with {"feed_id": N}) is unaffected.

DROP FUNCTION IF EXISTS remove_feed(bigint);

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
