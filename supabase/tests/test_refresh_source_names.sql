-- Test suite for refresh_source_names() function (pgTAP)
-- Tests the set-based rewrite (Option B in issue #12) that fixes
-- performance + comma-only source bug.
--
-- Run: supabase test db supabase/tests/

BEGIN;
SELECT plan(11);

-- Use a test-only city to avoid collisions with real data
CREATE TEMP TABLE _test_const AS SELECT 'test_city_pgtap' AS city;

-- ============================================================================
-- Helper: seed events and call refresh_source_names() in one step
-- ============================================================================
CREATE OR REPLACE FUNCTION _test_seed_and_refresh(
  p_rows text[][],  -- each row: {title, source, source_uid}
  p_city text DEFAULT 'test_city_pgtap'
)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE r text[];
BEGIN
  DELETE FROM events WHERE city = p_city;
  DELETE FROM source_names WHERE city = p_city;
  FOREACH r SLICE 1 IN ARRAY p_rows LOOP
    INSERT INTO events (city, title, start_time, source, source_uid)
    VALUES (p_city, r[1], now(), r[2], r[3]);
  END LOOP;
  PERFORM refresh_source_names(p_city);
END;
$$;

-- ============================================================================
-- Test 1: Comma-only sources are counted
-- ============================================================================
SELECT _test_seed_and_refresh(ARRAY[
  ARRAY['Event 1', 'IU Eskenazi School of Art, Architecture + Design', 'uid-1'],
  ARRAY['Event 2', 'IU Eskenazi School of Art, Architecture + Design', 'uid-2'],
  ARRAY['Event 3', 'Architecture + Design, Eskenazi Museum of Art',    'uid-3']
]);

SELECT is(
  (SELECT event_count FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'Architecture + Design'),
  3,
  'Test 1a: "Architecture + Design" appears in 3 events (comma-only)'
);

SELECT is(
  (SELECT event_count FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'IU Eskenazi School of Art'),
  2,
  'Test 1b: "IU Eskenazi School of Art" appears in 2 events'
);

-- ============================================================================
-- Test 2: Standalone sources (no commas)
-- ============================================================================
SELECT _test_seed_and_refresh(ARRAY[
  ARRAY['Event 1', 'Bloomington Brewing Company', 'uid-s1'],
  ARRAY['Event 2', 'Bloomington Brewing Company', 'uid-s2'],
  ARRAY['Event 3', 'Bloomington Brewing Company', 'uid-s3'],
  ARRAY['Event 4', 'IU Cinema', 'uid-s4'],
  ARRAY['Event 5', 'IU Cinema', 'uid-s5']
]);

SELECT is(
  (SELECT event_count FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'Bloomington Brewing Company'),
  3,
  'Test 2a: "Bloomington Brewing Company" count = 3'
);

SELECT is(
  (SELECT event_count FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'IU Cinema'),
  2,
  'Test 2b: "IU Cinema" count = 2'
);

-- ============================================================================
-- Test 3: Mixed sources (standalone + comma lists)
-- ============================================================================
SELECT _test_seed_and_refresh(ARRAY[
  ARRAY['Event 1', 'IU Cinema', 'uid-m1'],
  ARRAY['Event 2', 'IU Cinema', 'uid-m2'],
  ARRAY['Event 3', 'IU Cinema', 'uid-m3'],
  ARRAY['Event 4', 'IU Cinema, IU Arts & Humanities Institute', 'uid-m4'],
  ARRAY['Event 5', 'Eskenazi Museum of Art, IU Cinema', 'uid-m5']
]);

SELECT is(
  (SELECT event_count FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'IU Cinema'),
  5,
  'Test 3: "IU Cinema" total count = 5 (3 standalone + 2 in comma lists)'
);

-- ============================================================================
-- Test 4: Stale sources are cleaned up on re-run
-- ============================================================================
SELECT _test_seed_and_refresh(ARRAY[
  ARRAY['Event 1', 'Temporary Source', 'uid-c1'],
  ARRAY['Event 2', 'Permanent Source', 'uid-c2']
]);

SELECT isnt(
  (SELECT count(*)::int FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'Temporary Source'),
  0,
  'Test 4a: "Temporary Source" exists after first run'
);

-- Delete events for Temporary Source and re-run
DELETE FROM events
WHERE city = 'test_city_pgtap' AND source = 'Temporary Source';
SELECT refresh_source_names('test_city_pgtap');

SELECT is(
  (SELECT count(*)::int FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'Temporary Source'),
  0,
  'Test 4b: "Temporary Source" removed after its events deleted'
);

SELECT isnt(
  (SELECT count(*)::int FROM source_names
   WHERE city = 'test_city_pgtap' AND name = 'Permanent Source'),
  0,
  'Test 4c: "Permanent Source" still exists'
);

-- ============================================================================
-- Test 5: Idempotency - running twice produces identical results
-- ============================================================================
SELECT _test_seed_and_refresh(ARRAY[
  ARRAY['Event 1', 'Source A', 'uid-i1'],
  ARRAY['Event 2', 'Source A, Source B', 'uid-i2'],
  ARRAY['Event 3', 'Source B', 'uid-i3'],
  ARRAY['Event 4', 'Source C, Source D, Source E', 'uid-i4']
]);

CREATE TEMP TABLE _first_run AS
SELECT name, event_count FROM source_names
WHERE city = 'test_city_pgtap' ORDER BY name;

SELECT refresh_source_names('test_city_pgtap');

SELECT results_eq(
  'SELECT name, event_count FROM source_names WHERE city = ''test_city_pgtap'' ORDER BY name',
  'SELECT name, event_count FROM _first_run ORDER BY name',
  'Test 5: Function is idempotent (identical results on second run)'
);

-- ============================================================================
-- Test 6: Empty / malformed sources don't produce blank rows
-- ============================================================================
SELECT _test_seed_and_refresh(ARRAY[
  ARRAY['Event 1', 'Real Source, ', 'uid-e1'],
  ARRAY['Event 2', '', 'uid-e2'],
  ARRAY['Event 3', 'A,,B', 'uid-e3']
]);

SELECT is(
  (SELECT count(*)::int FROM source_names
   WHERE city = 'test_city_pgtap' AND name = ''),
  0,
  'Test 6a: No empty-string source names from trailing/double commas'
);

SELECT is(
  (SELECT count(*)::int FROM source_names WHERE city = 'test_city_pgtap'),
  3,
  'Test 6b: Only real sources remain (Real Source, A, B)'
);

-- ============================================================================
-- Cleanup & finish
-- ============================================================================
DELETE FROM events WHERE city = 'test_city_pgtap';
DELETE FROM source_names WHERE city = 'test_city_pgtap';

SELECT * FROM finish();
ROLLBACK;
