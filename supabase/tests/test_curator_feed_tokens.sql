-- Test suite for the curator-feed capability constraints (pgTAP)
-- A picks feed's ?token= is its only credential, and feeds.url is world-readable
-- and re-exported to cities/<city>/feeds.txt (GHSA-3pg8-w4j4-6wv8). Curator
-- rows name the curator instead; download_feeds mints the URL from feed_tokens.
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(8);

-- One real user, so every rejection below fails on a CHECK, not on the FK.
INSERT INTO auth.users (id, instance_id, aud, role, email)
VALUES ('11111111-1111-1111-1111-111111111111', '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'curator@example.invalid');

-- A capability URL may not be stored, whichever feed_type claims it.
SELECT throws_ok(
    $$ INSERT INTO feeds (city, url, name, status, feed_type)
       VALUES ('test_cur', 'https://ref.supabase.co/functions/v1/my-picks?token=abc', 'Leak', 'active', 'ics_url') $$,
    '23514',
    NULL,
    'rejects a my-picks URL as an ics_url'
);

-- The display name is exported to feeds.txt, and fallback_url is copied into
-- X-SOURCE-URL, so a token in either is public too.
SELECT throws_ok(
    $$ INSERT INTO feeds (city, url, name, status, feed_type)
       VALUES ('test_cur', 'https://example.com/events.ics', 'Leak https://ref.supabase.co/functions/v1/my-picks?token=abc', 'active', 'ics_url') $$,
    '23514',
    NULL,
    'rejects a my-picks URL in the display name'
);

SELECT throws_ok(
    $$ INSERT INTO feeds (city, url, name, status, feed_type, fallback_url)
       VALUES ('test_cur', 'https://example.com/events.ics', 'Plain', 'active', 'ics_url', 'https://ref.supabase.co/functions/v1/my-picks?token=abc') $$,
    '23514',
    NULL,
    'rejects a my-picks URL in the source page URL'
);

SELECT throws_ok(
    $$ INSERT INTO feeds (city, url, name, status, feed_type, curator_user_id)
       VALUES ('test_cur', 'https://ref.supabase.co/functions/v1/my-picks?token=abc', 'Leak', 'active', 'curator', '11111111-1111-1111-1111-111111111111') $$,
    '23514',
    NULL,
    'rejects a my-picks URL as a curator row too'
);

-- curator_user_id and feed_type are two halves of one fact.
SELECT throws_ok(
    $$ INSERT INTO feeds (city, url, name, status, feed_type)
       VALUES ('test_cur', 'curator://no-user', 'Untied', 'active', 'curator') $$,
    '23514',
    NULL,
    'rejects a curator row with no curator_user_id'
);

-- The url must name the same person, or the build cannot mint a token for it.
SELECT throws_ok(
    $$ INSERT INTO feeds (city, url, name, status, feed_type, curator_user_id)
       VALUES ('test_cur', 'curator://22222222-2222-2222-2222-222222222222', 'Typo', 'active', 'curator', '11111111-1111-1111-1111-111111111111') $$,
    '23514',
    NULL,
    'rejects a curator row whose url names someone else'
);

SELECT lives_ok(
    $$ INSERT INTO feeds (city, url, name, status, feed_type, curator_user_id)
       VALUES ('test_cur', 'curator://11111111-1111-1111-1111-111111111111', 'Curator Picks', 'active', 'curator', '11111111-1111-1111-1111-111111111111') $$,
    'accepts a curator row that names its curator'
);

-- Deleting the account must not drop the feed row behind remove_feed() and
-- strand the events it imported; retire the feed first.
SELECT throws_ok(
    $$ DELETE FROM auth.users WHERE id = '11111111-1111-1111-1111-111111111111' $$,
    '23503',
    NULL,
    'refuses to delete a curator account before its feed is retired'
);

SELECT * FROM finish();
ROLLBACK;
