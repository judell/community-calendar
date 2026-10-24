-- Close the two anonymous write doors the load-events secret gate cannot see
-- (GHSA-qmc5-6cfg-38p7).
--
-- load-events writes with the service role, which bypasses RLS, so scoping the
-- INSERT policy to service_role is invisible to it. Anonymous REST callers lose
-- both paths: POST /rest/v1/events (the policy applied to PUBLIC with
-- WITH CHECK (true)) and POST /rest/v1/rpc/delete_stale_events (SECURITY
-- DEFINER with the default PUBLIC EXECUTE grant).
--
-- delete_stale_events stays callable by the service role, which is the only
-- caller. refresh_source_names and refresh_deduplicated_events are deliberately
-- untouched: the workflow calls them with the anon key.

DROP POLICY IF EXISTS "Service function can insert events" ON events;
DROP POLICY IF EXISTS "service_role inserts events" ON events;

CREATE POLICY "service_role inserts events"
  ON events FOR INSERT
  TO service_role
  WITH CHECK (true);

REVOKE EXECUTE ON FUNCTION public.delete_stale_events(text, text[], text[])
  FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.delete_stale_events(text, text[], text[])
  TO service_role;

-- The legacy load-events mode (and the cron job that called it with `{}`) is
-- retired; a surviving schedule would only produce daily 401s.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'load-events-daily') THEN
    PERFORM cron.unschedule('load-events-daily');
  END IF;
END
$$;
