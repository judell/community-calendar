-- Test suite for record_feed_source() (pgTAP)
-- The recorder appends server-side so two overlapping builds cannot erase each
-- other's stems from feeds.source_ids (#232).
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(3);

INSERT INTO feeds (city, url, name, status, feed_type)
VALUES ('test_rfs', 'https://example.invalid/test_rfs.ics', 'Feed X', 'active', 'ics_url');

SELECT record_feed_source((SELECT id FROM feeds WHERE city = 'test_rfs'), 'stem_a');

SELECT is(
    (SELECT source_ids FROM feeds WHERE city = 'test_rfs'),
    ARRAY['stem_a']::text[],
    'records the first stem'
);

SELECT record_feed_source((SELECT id FROM feeds WHERE city = 'test_rfs'), 'stem_a');

SELECT is(
    (SELECT source_ids FROM feeds WHERE city = 'test_rfs'),
    ARRAY['stem_a']::text[],
    'a repeated stem is appended once'
);

SELECT record_feed_source((SELECT id FROM feeds WHERE city = 'test_rfs'), 'stem_b');

SELECT is(
    (SELECT source_ids FROM feeds WHERE city = 'test_rfs'),
    ARRAY['stem_a', 'stem_b']::text[],
    'a later build appends without erasing the earlier stem'
);

SELECT * FROM finish();  -- noqa: AM04
ROLLBACK;
