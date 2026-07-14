-- Test suite for delete_stale_events() function (pgTAP)
-- Tests the performance fix: NOT EXISTS (unnest) instead of != ALL()
-- which was hitting Postgres statement timeout with 3500+ source_uids.
--
-- Run: supabase test db supabase/tests/
-- Or:  make test-sql

BEGIN;
SELECT plan(8);

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
-- Cleanup
-- ============================================================================
DELETE FROM events
WHERE city = 'test_dse';

SELECT * FROM finish();  -- noqa: AM04
ROLLBACK;
