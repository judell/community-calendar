-- Test suite for remove_feed() (pgTAP)
-- remove_feed deletes only rows whose source equals the feed's name. A merge
-- survivor carries the comma-joined member names, so it is left for the next
-- build to re-attribute; deleting it would cascade away saved picks on an event
-- owned by another feed (ADR 0017).
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(3);

INSERT INTO feeds (city, url, name, status, feed_type)
VALUES
('test_rf', 'https://example.invalid/test_rf_a.ics', 'Feed A', 'active', 'ics_url'),
('test_rf', 'https://example.invalid/test_rf_b.ics', 'Feed B', 'active', 'ics_url');

INSERT INTO events (city, title, start_time, source, source_id, source_uid, source_names)
VALUES
('test_rf', 'Merged survivor', now(), 'Feed A, Feed B', 'feed_a', 'uid-merged', ARRAY['Feed A', 'Feed B']),
('test_rf', 'Feed B only', now(), 'Feed B', 'feed_b', 'uid-b-only', ARRAY['Feed B']);

-- Remove the member feed, not the survivor's owner.
SELECT remove_feed((SELECT id FROM feeds WHERE city = 'test_rf' AND name = 'Feed B'));

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-b-only'
    ),
    0,
    'remove_feed deletes rows the feed owns (source = feed name)'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-merged'
    ),
    1,
    'remove_feed leaves a merge survivor owned by another feed intact (picks preserved)'
);

SELECT is(
    (
        SELECT count(*)::int FROM feeds
        WHERE city = 'test_rf'
    ),
    1,
    'remove_feed deletes only the feed row'
);

SELECT * FROM finish();  -- noqa: AM04
ROLLBACK;
