-- Lock down SECURITY DEFINER RPCs that any anonymous caller could execute.
--
-- Reported by the B-Square fork (2026-10-24); also flagged by Supabase's
-- database linter as 0028 anon_security_definer_function_executable.
-- Postgres grants EXECUTE to PUBLIC by default, so these functions, which
-- run as their owner and bypass RLS, were callable with the publishable key:
--
--   delete_stale_events          delete events in any city (50% guard per call)
--   remove_feed                  delete any feed and its events, no caller check
--   refresh_deduplicated_events  expensive matview refresh, statement_timeout 0
--
-- Callers after this migration:
--   delete_stale_events          load-events edge function (service key)
--   remove_feed                  Manage Feeds dialog (admin JWT), maintenance
--                                scripts (service key)
--   refresh_deduplicated_events  nightly workflow (service key)
--
-- refresh_source_names is deliberately untouched: the nightly workflow's
-- "Refresh source names" step calls it with the anon key.
--
-- Function bodies are unchanged apart from schema-qualified names, needed
-- because search_path is now pinned to ''.

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

CREATE OR REPLACE FUNCTION public.remove_feed(feed_id bigint)
RETURNS TABLE (events_deleted bigint, feed_deleted boolean)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  f record;
  ev_count bigint;
BEGIN
  -- Admin JWT (Manage Feeds) or service key (maintenance scripts) only.
  IF coalesce(auth.role(), '') <> 'service_role' AND NOT EXISTS (
    SELECT 1 FROM public.admin_users WHERE user_id = auth.uid()
  ) THEN
    RAISE EXCEPTION 'remove_feed: admin required' USING ERRCODE = '42501';
  END IF;

  SELECT city, name INTO f FROM public.feeds WHERE id = feed_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'remove_feed: no feed row with id %', feed_id;
  END IF;

  DELETE FROM public.events e WHERE e.city = f.city AND e.source = f.name;
  GET DIAGNOSTICS ev_count = ROW_COUNT;

  DELETE FROM public.feeds WHERE id = feed_id;

  RETURN QUERY SELECT ev_count, true;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.remove_feed(bigint) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.remove_feed(bigint) TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.refresh_deduplicated_events()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
SET statement_timeout TO '0'
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.deduplicated_events;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.refresh_deduplicated_events() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_deduplicated_events() TO service_role;
