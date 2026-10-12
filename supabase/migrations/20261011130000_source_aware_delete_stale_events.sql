-- Make stale deletion source-aware so a source that did not produce output
-- (a scraper that crashed, a feed that 404'd) keeps its existing rows.
--
-- Previously delete_stale_events removed every city row whose source_uid was
-- absent from the incoming list, so a source whose ingestion failed lost its
-- events exactly as if it had written a valid-empty calendar (issue #227).
-- Now the caller passes p_sources, the set of source_ids present in the
-- payload; only those sources are swept. A source absent from the payload is
-- left untouched.
--
-- p_sources IS NULL keeps the old whole-city behavior for any caller that has
-- not been updated yet (load-events passes the real set; the 2-arg pgTAP
-- calls exercise the legacy path).
--
-- Trade-off: a source that legitimately runs with zero upcoming events looks
-- identical to a failed one, so its rows are preserved until its next
-- non-empty run. Retiring a source goes through remove_feed, which deletes its
-- rows explicitly. A source whose every event merges into another source is
-- likewise absent, so those rows can persist; see ADR 0017.
--
-- The 50% partial-load guard is evaluated per present source, so a healthy
-- source's uid count cannot mask a truncated one: a source that would lose
-- more than half its rows is preserved (skipped) and the rest are swept, with
-- a WARNING naming it. Skipping instead of raising keeps one source that winds
-- down (a festival, a semester) from blocking cleanup for the whole city. The
-- caller upserts the payload first (load-events does), so each source's row
-- count already includes its incoming uids.
--
-- CREATE OR REPLACE cannot change the argument list (it would overload rather
-- than replace, leaving the old whole-city function callable by name), so the
-- two-argument form is dropped first.

DROP FUNCTION IF EXISTS delete_stale_events(text, text[]);

CREATE FUNCTION delete_stale_events(
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
  guard_sources text[] := ARRAY[]::text[];
  deleted_count bigint;
BEGIN
  IF p_sources IS NULL THEN
    -- Legacy whole-city sweep: the original aggregate guard.
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
    -- Source-scoped sweep: evaluate the guard per present source so a healthy
    -- source's uid count cannot mask a truncated one, but preserve the
    -- offending sources and sweep the rest. Raising here would let one source
    -- winding down (a festival, a semester) refuse every run and so block
    -- cleanup for the whole city.
    SELECT coalesce(array_agg(s.source_id), ARRAY[]::text[])
      INTO guard_sources
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

    IF array_length(guard_sources, 1) IS NOT NULL THEN
      RAISE WARNING
        'delete_stale_events preserved % source(s) for city % (would delete '
        'more than half their rows): %',
        array_length(guard_sources, 1), p_city, array_to_string(guard_sources, ', ');
    END IF;
  END IF;

  DELETE FROM events e
  WHERE e.city = p_city
    AND e.source_uid IS NOT NULL
    AND (p_sources IS NULL OR e.source_id = ANY(p_sources))
    AND NOT (e.source_id = ANY(guard_sources))
    AND NOT EXISTS (
      SELECT 1 FROM unnest(p_source_uids) AS u(uid)
      WHERE u.uid = e.source_uid
    );
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RETURN deleted_count;
END;
$$;
