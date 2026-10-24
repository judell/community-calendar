-- Test suite for delete_stale_events() function (pgTAP)
-- Tests the performance fix: NOT EXISTS (unnest) instead of != ALL()
-- which was hitting Postgres statement timeout with 3500+ source_uids.
--
-- Tests 1-4 call the 2-arg form (p_sources defaulted to NULL = legacy
-- whole-city sweep). Tests 5-9 cover source-aware behavior (issues #227, #233).
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(19);

-- ============================================================================
-- Test 1: Basic stale event deletion
-- ============================================================================
-- Seed test events
INSERT INTO events (city, title, start_time, source, source_uid)
VALUES
('test_dse', 'Event A', now(), 'Source A', 'uid-a'),
('test_dse', 'Event B', now(), 'Source B', 'uid-b'),
('test_dse', 'Event C', now(), 'Source C', 'uid-c'),
('test_dse', 'Event D', now(), 'Source D', 'uid-d');

SELECT is(
    delete_stale_events('test_dse', ARRAY['uid-a', 'uid-b', 'uid-c']),
    bigint '1',
    'Test 1: Deletes 1 stale event (uid-d not in keep list)'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse'
    ),
    3,
    'Test 1b: 3 events remain after stale deletion'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse' AND source_uid = 'uid-a'
    ),
    1,
    'Test 1c: uid-a is still present'
);

-- Cleanup for next test
DELETE FROM events
WHERE city = 'test_dse';

-- ============================================================================
-- Test 2: Keep all events (empty stale set)
-- ============================================================================
INSERT INTO events (city, title, start_time, source, source_uid)
VALUES
('test_dse', 'Event A', now(), 'Source A', 'uid-a'),
('test_dse', 'Event B', now(), 'Source B', 'uid-b');

SELECT is(
    delete_stale_events('test_dse', ARRAY['uid-a', 'uid-b']),
    bigint '0',
    'Test 2: No events deleted when all are in keep list'
);

-- Cleanup
DELETE FROM events
WHERE city = 'test_dse';

-- ============================================================================
-- Test 3: Delete all events when keep list is empty-adjacent (all stale)
-- ============================================================================
INSERT INTO events (city, title, start_time, source, source_uid)
VALUES
('test_dse', 'Event A', now(), 'Source A', 'uid-old-1'),
('test_dse', 'Event B', now(), 'Source B', 'uid-old-2');

SELECT is(
    delete_stale_events('test_dse', ARRAY['uid-new-1', 'uid-new-2']),
    bigint '2',
    'Test 3: All old events deleted when keep list has entirely new UIDs'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse'
    ),
    0,
    'Test 3b: No events remain'
);

-- ============================================================================
-- Test 4: Large array performance — 3500 source_uids
-- ============================================================================
-- Insert one event that should survive
INSERT INTO events (city, title, start_time, source, source_uid)
VALUES ('test_dse', 'Survivor', now(), 'Source X', 'uid-survivor');

-- Call with 3500-element array (the survivor should NOT be deleted)
SELECT is(
    delete_stale_events('test_dse', array(
        SELECT 'uid-' || generate_series(1, 3500)::text
    ) || ARRAY['uid-survivor']),
    bigint '0',
    'Test 4: With 3500-element array, survivor is kept (no timeout)'
);

-- Verify survivor still exists
SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse' AND source_uid = 'uid-survivor'
    ),
    1,
    'Test 4b: Survivor event present after large-array delete_stale_events'
);

-- ============================================================================
-- Test 5: A source absent from the payload keeps its rows (issue #227)
-- ============================================================================
-- test_dse now has src-a and src-b. The payload only carries src-a, so the
-- sweep must leave src-b's rows alone (a failed scraper/feed).
DELETE FROM events
WHERE city = 'test_dse';

INSERT INTO events (city, title, start_time, source, source_id, source_uid)
VALUES
('test_dse', 'Event A', now(), 'Source A', 'src-a', 'uid-a'),
('test_dse', 'Event B', now(), 'Source B', 'src-b', 'uid-b');

SELECT is(
    delete_stale_events('test_dse', ARRAY['uid-a'], ARRAY['src-a']),
    bigint '0',
    'Test 5: absent source (src-b) is not swept'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse'
    ),
    2,
    'Test 5b: src-b row survives even though src-b is absent from the payload'
);

-- Cleanup
DELETE FROM events
WHERE city = 'test_dse';

-- ============================================================================
-- Test 6: A present source loses only the uids it dropped
-- ============================================================================
-- Ten rows for src-a; the payload keeps nine. That is under the 50% guard, so
-- the sweep proceeds and drops exactly the one missing uid.
INSERT INTO events (city, title, start_time, source, source_id, source_uid)
SELECT 'test_dse', 'Event A' || g, now(), 'Source A', 'src-a', 'uid-a' || g
FROM generate_series(1, 10) g;

INSERT INTO events (city, title, start_time, source, source_id, source_uid)
VALUES ('test_dse', 'Event B1', now(), 'Source B', 'src-b', 'uid-b1');

SELECT is(
    delete_stale_events(
        'test_dse',
        ARRAY(SELECT 'uid-a' || g FROM generate_series(1, 9) g),
        ARRAY['src-a']
    ),
    bigint '1',
    'Test 6: present source drops its missing uids only'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse'
    ),
    10,
    'Test 6b: uid-a10 gone, uid-a1..a9 and src-b kept'
);

-- ============================================================================
-- Test 7: a source over the threshold is swept, with a warning (#233)
-- ============================================================================
-- Four src-a rows and a payload with one uid: src-a is over the threshold, but
-- the manifest says it ran, so the sweep proceeds instead of preserving it.
DELETE FROM events
WHERE city = 'test_dse';

INSERT INTO events (city, title, start_time, source, source_id, source_uid)
SELECT 'test_dse', 'Event A' || g, now(), 'Source A', 'src-a', 'uid-a' || g
FROM generate_series(1, 4) g;

SELECT is(
    delete_stale_events('test_dse', ARRAY['uid-a1'], ARRAY['src-a']),
    bigint '3',
    'Test 7: a source over the threshold is swept anyway'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse'
    ),
    1,
    'Test 7b: only the uid carried by the payload survives'
);

-- ============================================================================
-- Test 8: both a shrinking and a healthy source are swept
-- ============================================================================
-- src-a is over the threshold (4 rows, sends 1) and src-b is healthy (100
-- rows, sends 99). Both ran, so both are swept.
DELETE FROM events
WHERE city = 'test_dse';

INSERT INTO events (city, title, start_time, source, source_id, source_uid)
SELECT 'test_dse', 'Event A' || g, now(), 'Source A', 'src-a', 'uid-a' || g
FROM generate_series(1, 4) g;

INSERT INTO events (city, title, start_time, source, source_id, source_uid)
SELECT 'test_dse', 'Event B' || g, now(), 'Source B', 'src-b', 'uid-b' || g
FROM generate_series(1, 100) g;

SELECT is(
    delete_stale_events(
        'test_dse',
        ARRAY['uid-a1'] || ARRAY(SELECT 'uid-b' || g FROM generate_series(1, 99) g),
        ARRAY['src-a', 'src-b']
    ),
    bigint '4',
    'Test 8: both sources are swept'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse' AND source_id = 'src-a'
    ),
    1,
    'Test 8b: over-threshold source keeps only its carried uid'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse' AND source_id = 'src-b'
    ),
    99,
    'Test 8c: healthy source lost only its stale row'
);

-- ============================================================================
-- Test 9: a ran-and-empty source is swept; a failed source keeps its rows
-- ============================================================================
-- src-quiet ran and produced no events, so it is in the manifest with an empty
-- keep list. src-failed is absent from the manifest and keeps its rows.
DELETE FROM events
WHERE city = 'test_dse';

INSERT INTO events (city, title, start_time, source, source_id, source_uid)
SELECT 'test_dse', 'Event Q' || g, now(), 'Source Q', 'src-quiet', 'uid-q' || g
FROM generate_series(1, 3) g;

INSERT INTO events (city, title, start_time, source, source_id, source_uid)
SELECT 'test_dse', 'Event F' || g, now(), 'Source F', 'src-failed', 'uid-f' || g
FROM generate_series(1, 2) g;

SELECT is(
    delete_stale_events('test_dse', ARRAY[]::text[], ARRAY['src-quiet']),
    bigint '3',
    'Test 9: a source that ran and emptied is swept'
);

SELECT is(
    (
        SELECT count(*)::int FROM events
        WHERE city = 'test_dse' AND source_id = 'src-failed'
    ),
    2,
    'Test 9b: a source absent from the manifest keeps its rows'
);

-- ============================================================================
-- Cleanup
-- ============================================================================
DELETE FROM events
WHERE city = 'test_dse';

SELECT * FROM finish();  -- noqa: AM04
ROLLBACK;
