-- Lockdown tests for anonymous event writes (GHSA-qmc5-6cfg-38p7).
--
-- The edge function gate is covered by the Deno tests in
-- supabase/functions/load-events/auth_test.ts. These two assertions cover the
-- paths that bypass the function entirely: PostgREST insert and RPC execute.
--
-- The insert case needs a role switch: pgTAP runs as a superuser, which
-- bypasses RLS. has_table_privilege would still report INSERT for anon because
-- the GRANT remains; RLS is what denies.
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(3);

SELECT is(
    has_function_privilege('anon', 'public.delete_stale_events(text,text[],text[])', 'EXECUTE'),
    false,
    'anon cannot execute delete_stale_events'
);

SELECT ok(
    has_function_privilege('service_role', 'public.delete_stale_events(text,text[],text[])', 'EXECUTE'),
    'service_role can execute delete_stale_events'
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
