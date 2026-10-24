-- Scope stale deletion by the sources that ran, not by the sources that have
-- events, and demote the per-source 50% guard to a warning.
--
-- load-events used to derive p_sources from the payload, so a source that ran
-- with zero upcoming events was indistinguishable from a source that failed
-- and its rows were preserved forever (issue #233). The build now writes the
-- set of sources whose ingestion succeeded, and the caller passes that set as
-- p_sources. An empty array means "nothing ran" and sweeps nothing; NULL still
-- selects the legacy whole-city path for a caller that sends no manifest.
--
-- The per-source check can no longer preserve rows: the manifest is the
-- authority on which sources ran, so a source that shrank by more than half is
-- swept and named in a WARNING. A truncated scraper run looks the same as real
-- churn at this layer; the warning is the signal (ADR 0017 amendment, #233).
--
-- The aggregate guard on the legacy NULL path is unchanged.

CREATE OR REPLACE FUNCTION delete_stale_events(
    p_city text, p_source_uids text[], p_sources text[] DEFAULT NULL
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  current_count bigint;
  would_delete bigint;
  incoming_count bigint;
  shrinking_sources text[] := ARRAY[]::text[];
  deleted_count bigint;
BEGIN
  IF p_sources IS NULL THEN
    SELECT count(*) INTO current_count
    FROM events
    WHERE city = p_city;

    SELECT count(*) INTO would_delete
    FROM events e
    WHERE e.city = p_city
      AND e.source_uid IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM unnest(p_source_uids) AS u(uid)
        WHERE u.uid = e.source_uid
      );

    incoming_count := coalesce(array_length(p_source_uids, 1), 0);

    IF current_count > 0
       AND would_delete * 2 > current_count
       AND incoming_count < would_delete THEN
      RAISE EXCEPTION
        'delete_stale_events refused for city %: would delete % of % events '
        'with only % incoming source_uids (>50%% deletion driven by a short '
        'uid list looks like a partial load, not real churn)',
        p_city, would_delete, current_count, incoming_count;
    END IF;
  ELSE
    SELECT coalesce(array_agg(s.source_id), ARRAY[]::text[])
      INTO shrinking_sources
    FROM (
      SELECT e.source_id,
             count(*) AS current_s,
             count(*) FILTER (
               WHERE NOT EXISTS (
                 SELECT 1 FROM unnest(p_source_uids) AS u(uid)
                 WHERE u.uid = e.source_uid
               )
             ) AS stale_s
      FROM events e
      WHERE e.city = p_city
        AND e.source_uid IS NOT NULL
        AND e.source_id = ANY(p_sources)
      GROUP BY e.source_id
    ) s
    WHERE s.stale_s * 2 > s.current_s;

    IF array_length(shrinking_sources, 1) IS NOT NULL THEN
      RAISE WARNING
        'delete_stale_events swept % source(s) for city % after losing more '
        'than half their rows: %',
        array_length(shrinking_sources, 1), p_city,
        array_to_string(shrinking_sources, ', ');
    END IF;
  END IF;

  DELETE FROM events e
  WHERE e.city = p_city
    AND e.source_uid IS NOT NULL
    AND (p_sources IS NULL OR e.source_id = ANY(p_sources))
    AND NOT EXISTS (
      SELECT 1 FROM unnest(p_source_uids) AS u(uid)
      WHERE u.uid = e.source_uid
    );
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;
