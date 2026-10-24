-- Lockdown tests for anonymous writes that bypass the edge function.
--
-- load-events is gated by a shared secret (GHSA-qmc5-6cfg-38p7; the Deno tests
-- in supabase/functions/load-events/auth_test.ts cover the gate). These
-- assertions cover the database paths a REST caller reaches directly: the
-- events INSERT policy and EXECUTE on the SECURITY DEFINER write functions.
--
-- remove_feed's admin gate is exercised in test_remove_feed.sql.
--
-- The insert case needs a role switch: pgTAP runs as a superuser, which
-- bypasses RLS. has_table_privilege would still report INSERT for anon because
-- the GRANT remains; RLS is what denies.
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(6);

SELECT is(
    has_function_privilege('anon', 'public.delete_stale_events(text,text[],text[])', 'EXECUTE'),
    false,
    'anon cannot execute delete_stale_events'
);

SELECT ok(
    has_function_privilege('service_role', 'public.delete_stale_events(text,text[],text[])', 'EXECUTE'),
    'service_role can execute delete_stale_events'
);

-- GHSA-69r3-3gxw-fm4g: the dedupe refresh is CI-only.
SELECT is(
    has_function_privilege('anon', 'public.refresh_deduplicated_events()', 'EXECUTE'),
    false,
    'anon cannot execute refresh_deduplicated_events'
);

SELECT is(
    has_function_privilege('authenticated', 'public.refresh_deduplicated_events()', 'EXECUTE'),
    false,
    'authenticated cannot execute refresh_deduplicated_events'
);

SELECT ok(
    has_function_privilege('service_role', 'public.refresh_deduplicated_events()', 'EXECUTE'),
    'service_role can execute refresh_deduplicated_events'
);

SET LOCAL ROLE anon;

SELECT throws_ok(
    $$ INSERT INTO events (city, title, start_time, source_uid)
       VALUES ('test_lockdown', 'Forged', now(), 'lockdown-uid') $$,
    '42501',
    NULL,
    'anon cannot insert events'
);

RESET ROLE;

SELECT * FROM finish();
ROLLBACK;
