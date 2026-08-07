-- Add RPC function for stale event cleanup (replaces URL-based NOT IN filter
-- that exceeded PostgREST URL length limits with large source_uid lists)
CREATE OR REPLACE FUNCTION delete_stale_events(p_city text, p_source_uids text[])
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  deleted_count bigint;
BEGIN
  DELETE FROM events
  WHERE city = p_city
    AND source_uid IS NOT NULL
    AND source_uid != ALL(p_source_uids)
  ;
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;

-- Drop redundant constraint (source_uid is already unique on its own)
ALTER TABLE events DROP CONSTRAINT IF EXISTS events_source_source_uid_key;
