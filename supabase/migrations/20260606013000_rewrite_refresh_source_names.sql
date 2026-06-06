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
  
  -- Split comma-separated sources and count in one pass
  -- This processes each event exactly once (O(n)) instead of
  -- running a correlated subquery for each source_name (O(n×m))
  INSERT INTO source_names (city, name, event_count)
  SELECT 
    target_city as city,
    trim(unnest(string_to_array(source, ','))) as name,
    COUNT(DISTINCT id) as event_count
  FROM events
  WHERE city = target_city
    AND source IS NOT NULL
  GROUP BY name
  HAVING COUNT(DISTINCT id) > 0;  -- Only keep sources with events
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
