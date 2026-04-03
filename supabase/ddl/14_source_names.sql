-- Source names: clean flat list of individual source names per city
-- Populated/refreshed by refresh_source_names() RPC during nightly build
-- The events.source column may contain comma-separated merged sources from dedup;
-- this table provides the canonical individual source names with counts.

CREATE TABLE source_names (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  city text NOT NULL,
  name text NOT NULL,
  event_count integer DEFAULT 0,
  UNIQUE(city, name)
);

ALTER TABLE source_names ENABLE ROW LEVEL SECURITY;
CREATE POLICY "source_names_read" ON source_names FOR SELECT USING (true);

-- RPC to refresh source names and counts for a city (called after load-events)
CREATE OR REPLACE FUNCTION refresh_source_names(target_city text)
RETURNS void AS $$
BEGIN
  -- Upsert distinct non-comma sources for this city
  INSERT INTO source_names (city, name, event_count)
  SELECT city, source, COUNT(*)
  FROM events
  WHERE city = target_city
    AND source IS NOT NULL
    AND source NOT LIKE '%,%'
  GROUP BY city, source
  ON CONFLICT (city, name) DO UPDATE SET event_count = EXCLUDED.event_count;

  -- Update counts for sources that also appear in comma-separated merged sources
  UPDATE source_names sn
  SET event_count = (
    SELECT COUNT(DISTINCT e.id)
    FROM events e
    WHERE e.city = sn.city
      AND (e.source = sn.name
        OR e.source LIKE sn.name || ', %'
        OR e.source LIKE '%, ' || sn.name
        OR e.source LIKE '%, ' || sn.name || ', %')
  )
  WHERE sn.city = target_city;

  -- Remove sources that no longer have events
  DELETE FROM source_names
  WHERE city = target_city AND event_count = 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
