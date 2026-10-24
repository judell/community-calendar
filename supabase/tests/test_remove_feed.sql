-- Test suite for remove_feed() (pgTAP)
-- remove_feed deletes the rows a feed owns: rows whose source_id is one the
-- feed has produced (feeds.source_ids), plus rows whose source is exactly the
-- feed's name (rows built before the feed-to-source_id mapping existed). A
-- merge survivor carries the comma-joined member names, so source_id is the
-- only way to tell which feed owns it (ADR 0017).
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(11);

INSERT INTO feeds (city, url, name, status, feed_type, source_ids)
VALUES
('test_rf', 'https://example.invalid/test_rf_a.ics', 'Feed A', 'active', 'ics_url', ARRAY['feed_a']),
('test_rf', 'https://example.invalid/test_rf_b.ics', 'Feed B', 'active', 'ics_url', ARRAY['feed_b']),
('test_rf', 'https://example.invalid/test_rf_c.ics', 'Feed C', 'active', 'ics_url', ARRAY[]::text[]),
('test_rf', 'https://example.invalid/test_rf_d.ics', 'Shared Name', 'active', 'ics_url', ARRAY['feed_d']),
('test_rf', 'https://example.invalid/test_rf_e.ics', 'Shared Name', 'active', 'ics_url', ARRAY['feed_e']),
('test_rf', 'https://example.invalid/test_rf_f.ics', 'Feed F', 'active', 'ics_url', ARRAY['shared_stem']),
('test_rf', 'https://example.invalid/test_rf_g.ics', 'Feed G', 'active', 'ics_url', ARRAY['shared_stem']);

INSERT INTO events (city, title, start_time, source, source_id, source_uid, source_names)
VALUES
('test_rf', 'Survivor owned by A', now(), 'Feed A, Feed B', 'feed_a', 'uid-a-owns', ARRAY['Feed A', 'Feed B']),
('test_rf', 'Survivor owned by B', now(), 'Feed A, Feed B', 'feed_b', 'uid-b-owns', ARRAY['Feed A', 'Feed B']),
('test_rf', 'Feed B only', now(), 'Feed B', 'feed_b', 'uid-b-only', ARRAY['Feed B']),
('test_rf', 'Legacy Feed C row', now(), 'Feed C', 'legacy_c_stem', 'uid-c-legacy', ARRAY['Feed C']),
('test_rf', 'Shared-name row owned by D', now(), 'Shared Name', 'feed_d', 'uid-d-shared', ARRAY['Shared Name']),
('test_rf', 'Shared-name row owned by E', now(), 'Shared Name', 'feed_e', 'uid-e-shared', ARRAY['Shared Name']),
('test_rf', 'Shared-stem row owned by F', now(), 'Feed F', 'shared_stem', 'uid-f-shared', ARRAY['Feed F']),
('test_rf', 'Shared-stem row owned by G', now(), 'Feed G', 'shared_stem', 'uid-g-shared', ARRAY['Feed G']);

INSERT INTO auth.users (id, instance_id, aud, role, email)
VALUES (
    '00000000-0000-0000-0000-000000000232',
    '00000000-0000-0000-0000-000000000000',
    'authenticated', 'authenticated', 'pgtap@example.invalid'
);

INSERT INTO picks (user_id, event_id)
VALUES
('00000000-0000-0000-0000-000000000232', (SELECT id FROM events WHERE source_uid = 'uid-a-owns')),
('00000000-0000-0000-0000-000000000232', (SELECT id FROM events WHERE source_uid = 'uid-b-owns')),
('00000000-0000-0000-0000-000000000232', (SELECT id FROM events WHERE source_uid = 'uid-g-shared'));

-- Remove Feed A: the survivor it won must go; Feed B's survivor must stay.
SELECT remove_feed((SELECT id FROM feeds WHERE city = 'test_rf' AND name = 'Feed A'));

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-a-owns'
    ),
    0,
    'a merged survivor the feed owns is deleted'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-b-owns'
    ),
    1,
    'a merged survivor owned by another feed is untouched'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-b-only'
    ),
    1,
    'rows owned only by another feed are untouched'
);

SELECT is(
    (
        SELECT count(*)::int FROM picks
        WHERE user_id = '00000000-0000-0000-0000-000000000232'
    ),
    2,
    'the other feeds'' saved picks survive and the retired event''s pick is gone'
);

-- Feed C has no recorded source_id: the name fallback still clears its rows.
SELECT remove_feed((SELECT id FROM feeds WHERE city = 'test_rf' AND name = 'Feed C'));

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-c-legacy'
    ),
    0,
    'a feed without source_ids still deletes its rows by name'
);

-- Two feeds share a display name: the name arm must not touch the other
-- feed's rows, whose source_id belongs to its history.
SELECT remove_feed(
    (
        SELECT id FROM feeds
        WHERE city = 'test_rf' AND name = 'Shared Name'
          AND url LIKE '%_d.ics'
    )
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-d-shared'
    ),
    0,
    'the retiring feed''s shared-name row is deleted'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-e-shared'
    ),
    1,
    'a same-name feed''s row is left to the feed that owns it'
);

-- Two feeds can produce the same stem (bloomington's two events.in.gov rows
-- both slugged to events_search_events_ics until #240 retired the duplicate).
-- That stem identifies neither feed exclusively, so neither feed's rows may be
-- deleted through it.
SELECT remove_feed(
    (
        SELECT id FROM feeds
        WHERE city = 'test_rf' AND name = 'Feed F'
    )
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-f-shared'
    ),
    1,
    'rows under a shared source_id are left in place when their feed retires'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_rf' AND source_uid = 'uid-g-shared'
    ),
    1,
    'the other feed keeps the rows it built under the shared source_id'
);

SELECT is(
    (
        SELECT count(*)::int FROM picks
        WHERE user_id = '00000000-0000-0000-0000-000000000232'
    ),
    2,
    'saved picks on shared-source_id events survive the retirement'
);

SELECT is(
    (
        SELECT count(*)::int FROM feeds
        WHERE city = 'test_rf'
    ),
    3,
    'each removal deletes only its own feed row'
);

SELECT * FROM finish();  -- noqa: AM04
ROLLBACK;
