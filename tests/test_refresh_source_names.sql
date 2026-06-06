-- Test suite for refresh_source_names() function
-- Tests the set-based rewrite (Option A) that fixes performance + comma-only source bug
-- 
-- Run: supabase db query --linked -f tests/test_refresh_source_names.sql

-- Cleanup from any previous test runs
DELETE FROM events WHERE city = 'test_city_refresh_sources';
DELETE FROM source_names WHERE city = 'test_city_refresh_sources';

-- ============================================================================
-- Test 1: TRACER BULLET - Comma-only sources are counted
-- ============================================================================

-- Setup: Insert events where "Architecture + Design" only appears in comma lists
INSERT INTO events (city, title, start_time, source, source_uid) VALUES
  ('test_city_refresh_sources', 'Event 1', NOW(), 'IU Eskenazi School of Art, Architecture + Design', 'test-uid-1'),
  ('test_city_refresh_sources', 'Event 2', NOW(), 'IU Eskenazi School of Art, Architecture + Design', 'test-uid-2'),
  ('test_city_refresh_sources', 'Event 3', NOW(), 'Architecture + Design, Eskenazi Museum of Art', 'test-uid-3');

-- Run the function
SELECT refresh_source_names('test_city_refresh_sources');

-- Test 1a: "Architecture + Design" should exist with count = 3
DO $$
DECLARE
  v_count integer;
  v_event_count integer;
BEGIN
  SELECT COUNT(*), COALESCE(MAX(event_count), 0)
  INTO v_count, v_event_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'Architecture + Design';
  
  IF v_count = 0 THEN
    RAISE EXCEPTION '[Test 1a] FAIL: "Architecture + Design" not found in source_names';
  END IF;
  
  IF v_event_count != 3 THEN
    RAISE EXCEPTION '[Test 1a] FAIL: "Architecture + Design" event_count = %, expected 3', v_event_count;
  END IF;
  
  RAISE NOTICE '[Test 1a] PASS: "Architecture + Design" found with correct count (3)';
END $$;

-- Test 1b: "IU Eskenazi School of Art" should also exist with count = 2
DO $$
DECLARE
  v_count integer;
  v_event_count integer;
BEGIN
  SELECT COUNT(*), COALESCE(MAX(event_count), 0)
  INTO v_count, v_event_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'IU Eskenazi School of Art';
  
  IF v_count = 0 THEN
    RAISE EXCEPTION '[Test 1b] FAIL: "IU Eskenazi School of Art" not found in source_names';
  END IF;
  
  IF v_event_count != 2 THEN
    RAISE EXCEPTION '[Test 1b] FAIL: "IU Eskenazi School of Art" event_count = %, expected 2', v_event_count;
  END IF;
  
  RAISE NOTICE '[Test 1b] PASS: "IU Eskenazi School of Art" found with correct count (2)';
END $$;

-- Cleanup Test 1
DELETE FROM events WHERE city = 'test_city_refresh_sources';
DELETE FROM source_names WHERE city = 'test_city_refresh_sources';

-- ============================================================================
-- Test 2: Standalone sources (no commas) are counted correctly
-- ============================================================================

-- Setup: Insert events with standalone sources
INSERT INTO events (city, title, start_time, source, source_uid) VALUES
  ('test_city_refresh_sources', 'Event 1', NOW(), 'Bloomington Brewing Company', 'test-uid-standalone-1'),
  ('test_city_refresh_sources', 'Event 2', NOW(), 'Bloomington Brewing Company', 'test-uid-standalone-2'),
  ('test_city_refresh_sources', 'Event 3', NOW(), 'Bloomington Brewing Company', 'test-uid-standalone-3'),
  ('test_city_refresh_sources', 'Event 4', NOW(), 'IU Cinema', 'test-uid-standalone-4'),
  ('test_city_refresh_sources', 'Event 5', NOW(), 'IU Cinema', 'test-uid-standalone-5');

-- Run the function
SELECT refresh_source_names('test_city_refresh_sources');

-- Test 2a: "Bloomington Brewing Company" should have count = 3
DO $$
DECLARE
  v_event_count integer;
BEGIN
  SELECT COALESCE(event_count, 0)
  INTO v_event_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'Bloomington Brewing Company';
  
  IF v_event_count != 3 THEN
    RAISE EXCEPTION '[Test 2a] FAIL: "Bloomington Brewing Company" event_count = %, expected 3', v_event_count;
  END IF;
  
  RAISE NOTICE '[Test 2a] PASS: "Bloomington Brewing Company" count = 3';
END $$;

-- Test 2b: "IU Cinema" should have count = 2
DO $$
DECLARE
  v_event_count integer;
BEGIN
  SELECT COALESCE(event_count, 0)
  INTO v_event_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'IU Cinema';
  
  IF v_event_count != 2 THEN
    RAISE EXCEPTION '[Test 2b] FAIL: "IU Cinema" event_count = %, expected 2', v_event_count;
  END IF;
  
  RAISE NOTICE '[Test 2b] PASS: "IU Cinema" count = 2';
END $$;

-- Cleanup Test 2
DELETE FROM events WHERE city = 'test_city_refresh_sources';
DELETE FROM source_names WHERE city = 'test_city_refresh_sources';

-- ============================================================================
-- Test 3: Mixed sources (standalone + comma lists) have correct total
-- ============================================================================

-- Setup: "IU Cinema" appears 3 times standalone + 2 times in comma lists = 5 total
INSERT INTO events (city, title, start_time, source, source_uid) VALUES
  -- Standalone appearances (3)
  ('test_city_refresh_sources', 'Event 1', NOW(), 'IU Cinema', 'test-uid-mixed-1'),
  ('test_city_refresh_sources', 'Event 2', NOW(), 'IU Cinema', 'test-uid-mixed-2'),
  ('test_city_refresh_sources', 'Event 3', NOW(), 'IU Cinema', 'test-uid-mixed-3'),
  -- Comma-list appearances (2)
  ('test_city_refresh_sources', 'Event 4', NOW(), 'IU Cinema, IU Arts & Humanities Institute', 'test-uid-mixed-4'),
  ('test_city_refresh_sources', 'Event 5', NOW(), 'Eskenazi Museum of Art, IU Cinema', 'test-uid-mixed-5');

-- Run the function
SELECT refresh_source_names('test_city_refresh_sources');

-- Test 3: "IU Cinema" should have count = 5 (3 standalone + 2 in comma lists)
DO $$
DECLARE
  v_event_count integer;
BEGIN
  SELECT COALESCE(event_count, 0)
  INTO v_event_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'IU Cinema';
  
  IF v_event_count != 5 THEN
    RAISE EXCEPTION '[Test 3] FAIL: "IU Cinema" event_count = %, expected 5 (3 standalone + 2 comma)', v_event_count;
  END IF;
  
  RAISE NOTICE '[Test 3] PASS: "IU Cinema" total count = 5';
END $$;

-- Cleanup Test 3
DELETE FROM events WHERE city = 'test_city_refresh_sources';
DELETE FROM source_names WHERE city = 'test_city_refresh_sources';

-- ============================================================================
-- Test 4: Sources with zero events are removed (cleanup)
-- ============================================================================

-- Setup: Insert events, run function, then delete events for one source
INSERT INTO events (city, title, start_time, source, source_uid) VALUES
  ('test_city_refresh_sources', 'Event 1', NOW(), 'Temporary Source', 'test-uid-cleanup-1'),
  ('test_city_refresh_sources', 'Event 2', NOW(), 'Permanent Source', 'test-uid-cleanup-2');

-- First run: both sources should exist
SELECT refresh_source_names('test_city_refresh_sources');

DO $$
DECLARE
  v_count integer;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'Temporary Source';
  
  IF v_count = 0 THEN
    RAISE EXCEPTION '[Test 4a] FAIL: "Temporary Source" not found after first run';
  END IF;
  
  RAISE NOTICE '[Test 4a] PASS: "Temporary Source" exists after first run';
END $$;

-- Delete events for "Temporary Source"
DELETE FROM events
WHERE city = 'test_city_refresh_sources'
  AND source = 'Temporary Source';

-- Second run: "Temporary Source" should be removed
SELECT refresh_source_names('test_city_refresh_sources');

DO $$
DECLARE
  v_count integer;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'Temporary Source';
  
  IF v_count != 0 THEN
    RAISE EXCEPTION '[Test 4b] FAIL: "Temporary Source" still exists after deletion';
  END IF;
  
  RAISE NOTICE '[Test 4b] PASS: "Temporary Source" removed after events deleted';
END $$;

-- Verify "Permanent Source" still exists
DO $$
DECLARE
  v_count integer;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM source_names
  WHERE city = 'test_city_refresh_sources'
    AND name = 'Permanent Source';
  
  IF v_count = 0 THEN
    RAISE EXCEPTION '[Test 4c] FAIL: "Permanent Source" was removed';
  END IF;
  
  RAISE NOTICE '[Test 4c] PASS: "Permanent Source" still exists';
END $$;

-- Cleanup Test 4
DELETE FROM events WHERE city = 'test_city_refresh_sources';
DELETE FROM source_names WHERE city = 'test_city_refresh_sources';

-- ============================================================================
-- Test 5: Idempotency - Running function twice produces same result
-- ============================================================================

-- Setup: Insert diverse events
INSERT INTO events (city, title, start_time, source, source_uid) VALUES
  ('test_city_refresh_sources', 'Event 1', NOW(), 'Source A', 'test-uid-idem-1'),
  ('test_city_refresh_sources', 'Event 2', NOW(), 'Source A, Source B', 'test-uid-idem-2'),
  ('test_city_refresh_sources', 'Event 3', NOW(), 'Source B', 'test-uid-idem-3'),
  ('test_city_refresh_sources', 'Event 4', NOW(), 'Source C, Source D, Source E', 'test-uid-idem-4');

-- First run
SELECT refresh_source_names('test_city_refresh_sources');

-- Capture state after first run
CREATE TEMP TABLE first_run_state AS
SELECT name, event_count
FROM source_names
WHERE city = 'test_city_refresh_sources'
ORDER BY name;

-- Second run (should produce identical results)
SELECT refresh_source_names('test_city_refresh_sources');

-- Capture state after second run
CREATE TEMP TABLE second_run_state AS
SELECT name, event_count
FROM source_names
WHERE city = 'test_city_refresh_sources'
ORDER BY name;

-- Test 5: States should be identical
DO $$
DECLARE
  v_diff_count integer;
BEGIN
  -- Check if there are any differences
  SELECT COUNT(*) INTO v_diff_count
  FROM (
    SELECT name, event_count FROM first_run_state
    EXCEPT
    SELECT name, event_count FROM second_run_state
    UNION ALL
    SELECT name, event_count FROM second_run_state
    EXCEPT
    SELECT name, event_count FROM first_run_state
  ) AS differences;
  
  IF v_diff_count != 0 THEN
    RAISE EXCEPTION '[Test 5] FAIL: Function is not idempotent (% differences found)', v_diff_count;
  END IF;
  
  RAISE NOTICE '[Test 5] PASS: Function is idempotent (identical results on second run)';
END $$;

-- Cleanup Test 5
DROP TABLE first_run_state;
DROP TABLE second_run_state;
DELETE FROM events WHERE city = 'test_city_refresh_sources';
DELETE FROM source_names WHERE city = 'test_city_refresh_sources';

SELECT '[refresh_source_names] All tests passed!' as result;
