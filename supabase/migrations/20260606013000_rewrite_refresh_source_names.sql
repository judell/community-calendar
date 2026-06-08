-- Migration: Replace refresh_source_names() with set-based implementation
-- Fixes performance issue (#12) and comma-only source bug
-- Old: O(n×m) correlated subquery, 3.79s, misses comma-only sources
-- New: O(n) set-based, 0.78s, counts all sources correctly

CREATE OR REPLACE FUNCTION refresh_source_names(target_city text)
RETURNS void
SET statement_timeout TO '0'
AS $$
BEGIN
  -- Delete old entries for this city first
  DELETE FROM source_names WHERE city = target_city;
  
  -- Split comma-separated sources and count in one pass.
  -- CONVENTION: commas in events.source are always treated as separators
  -- between distinct source names (produced by deduplicated_events via
  -- string_agg). Individual source names must not contain commas.
  -- This processes each event exactly once (O(n)) instead of
  -- running a correlated subquery for each source_name (O(n×m)).
  -- Empty names (from blank sources, trailing/double commas) are filtered out.
  INSERT INTO source_names (city, name, event_count)
  SELECT city, name, event_count FROM (
    SELECT
      target_city AS city,
      trim(unnest(string_to_array(source, ','))) AS name,
      COUNT(DISTINCT id) AS event_count
    FROM events
    WHERE city = target_city
      AND source IS NOT NULL
    GROUP BY name
  ) s
  WHERE name <> '';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
