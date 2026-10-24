-- Close anonymous access to the remaining SECURITY DEFINER write functions
-- (GHSA-69r3-3gxw-fm4g).
--
-- remove_feed deletes a feed row, the events it owns, and those events' picks
-- by cascade. It had the default PUBLIC EXECUTE grant and no caller check, so
-- the publishable key was enough to delete any feed by its small sequential id.
-- Its only app caller is the Manage Feeds dialog, which sends the admin's JWT,
-- so the grant stays on `authenticated` and the body requires an admin_users
-- row. A direct SQL session sets the claim first (see ddl/16_feeds.sql).
--
-- refresh_deduplicated_events writes a large materialized view with
-- statement_timeout = 0 and was explicitly granted to anon. Only the nightly
-- build calls it, and it already holds the service key.

CREATE OR REPLACE FUNCTION public.remove_feed(feed_id bigint)
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
  -- so rows carrying it are left in place (see ddl/16_feeds.sql).
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

CREATE OR REPLACE FUNCTION public.refresh_deduplicated_events()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout TO '0'
SET search_path = ''
AS $function$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.deduplicated_events;
END;
$function$;

REVOKE EXECUTE ON FUNCTION public.refresh_deduplicated_events() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_deduplicated_events() TO service_role;
