-- Materialized view: deduplicated_events
-- Authoritative deduplicated read model. The confidence route (#150) stores one
-- Merge/Group/Separate decision per listing as events.duplicate_group; this view
-- groups by that stored decision and never recomputes similarity, location, or
-- grouping.
--
-- NULL isolation: a NULL duplicate_group means the route left the row alone and
-- it is its own group. PostgreSQL groups all NULLs together, so each NULL row is
-- keyed by a per-row value ('row:<id>') instead of by the NULL itself.
--
-- Representative: the route persists duplicate_group_representative, so the
-- view presents that member's fields and id. There is no database-assigned
-- min(id) competing rule.
--
-- Refreshed after load-events runs so the app can query pre-deduplicated rows.

DROP VIEW IF EXISTS deduplicated_events;
DROP MATERIALIZED VIEW IF EXISTS deduplicated_events;

CREATE MATERIALIZED VIEW IF NOT EXISTS deduplicated_events AS
WITH base AS (
    SELECT
        e.*,
        COALESCE(e.duplicate_group, 'row:' || e.id::text) AS group_key,
        CASE
            WHEN e.duplicate_group IS NOT NULL
                AND e.source_uid IS NOT DISTINCT FROM e.duplicate_group_representative
            THEN 0
            ELSE 1
        END AS rep_rank,
        CASE
            WHEN e.source_names IS NOT NULL AND array_length(e.source_names, 1) >= 1
                THEN e.source_names
            WHEN COALESCE(e.source, '') <> '' THEN ARRAY[e.source]
            ELSE ARRAY[]::text[]
        END AS structured_names
    FROM events e
    WHERE e.source IS DISTINCT FROM 'poster_capture'
),
name_occurrences AS (
    SELECT
        b.city,
        b.start_time,
        b.group_key,
        n.name,
        b.rep_rank,
        n.pos,
        ROW_NUMBER() OVER (
            PARTITION BY b.city, b.start_time, b.group_key, n.name
            ORDER BY b.rep_rank, n.pos, b.id
        ) AS occurrence_rank
    FROM base b
    CROSS JOIN LATERAL unnest(b.structured_names) WITH ORDINALITY AS n(name, pos)
),
name_union AS (
    SELECT city, start_time, group_key, name, rep_rank, pos
    FROM name_occurrences
    WHERE occurrence_rank = 1
),
name_agg AS (
    SELECT
        city,
        start_time,
        group_key,
        string_agg(name, ', ' ORDER BY rep_rank, pos, name) AS source,
        array_agg(name ORDER BY rep_rank, pos, name) AS source_names
    FROM name_union
    GROUP BY city, start_time, group_key
),
url_union AS (
    SELECT
        b.city,
        b.start_time,
        b.group_key,
        kv.key AS name,
        kv.value,
        ROW_NUMBER() OVER (
            PARTITION BY b.city, b.start_time, b.group_key, kv.key ORDER BY b.id
        ) AS rn
    FROM base b
    CROSS JOIN LATERAL jsonb_each(b.source_urls) AS kv(key, value)
    WHERE b.source_urls IS NOT NULL AND jsonb_typeof(b.source_urls) = 'object'
),
url_agg AS (
    SELECT
        city,
        start_time,
        group_key,
        jsonb_object_agg(name, value) AS source_urls
    FROM url_union
    WHERE rn = 1
    GROUP BY city, start_time, group_key
),
ics_categories_pick AS (
    -- Pick one member's categories. A `text[]` column cannot go through
    -- `array_agg` (2202E when members differ), so select the first non-NULL
    -- value in the same deterministic order the rolled columns use.
    SELECT DISTINCT ON (b.city, b.start_time, b.group_key)
        b.city,
        b.start_time,
        b.group_key,
        b.ics_categories
    FROM base b
    WHERE b.ics_categories IS NOT NULL
    ORDER BY b.city, b.start_time, b.group_key, b.rep_rank, b.id
),
rolled AS (
    SELECT
        (array_agg(b.id ORDER BY b.rep_rank, b.id))[1] AS id,
        (array_agg(b.title ORDER BY b.rep_rank, b.id))[1] AS title,
        b.start_time,
        (array_agg(b.end_time ORDER BY b.rep_rank, b.id) FILTER (WHERE b.end_time IS NOT NULL))[1] AS end_time,
        (array_agg(b.url ORDER BY b.rep_rank, b.id) FILTER (WHERE b.url IS NOT NULL AND b.url <> ''))[1] AS url,
        (array_agg(b.location ORDER BY b.rep_rank, b.id) FILTER (WHERE b.location IS NOT NULL))[1] AS location,
        (array_agg(b.description ORDER BY b.rep_rank, b.id) FILTER (WHERE b.description IS NOT NULL))[1] AS description,
        (array_agg(b.source_uid ORDER BY b.rep_rank, b.id))[1] AS source_uid,
        min(b.created_at) AS created_at,
        b.city,
        (array_agg(b.transcript ORDER BY b.rep_rank, b.id) FILTER (WHERE b.transcript IS NOT NULL))[1] AS transcript,
        (array_agg(b.source_id ORDER BY b.rep_rank, b.id))[1] AS source_id,
        (array_agg(b.cluster_id ORDER BY b.rep_rank, b.id) FILTER (WHERE b.cluster_id IS NOT NULL))[1] AS cluster_id,
        (array_agg(b.category ORDER BY b.rep_rank, b.id) FILTER (WHERE b.category IS NOT NULL))[1] AS category,
        (array_agg(b.image_url ORDER BY b.rep_rank, b.id) FILTER (WHERE b.image_url IS NOT NULL))[1] AS image_url,
        bool_or(b.all_day) AS all_day,
        max(b.duplicate_group) AS duplicate_group,
        max(b.duplicate_group_representative) AS duplicate_group_representative,
        array_agg(b.id ORDER BY b.id) AS merged_ids,
        b.group_key
    FROM base b
    GROUP BY b.city, b.start_time, b.group_key
)
SELECT
    r.id,
    r.title,
    r.start_time,
    r.end_time,
    r.url,
    r.location,
    r.description,
    COALESCE(n.source, '') AS source,
    r.source_uid,
    r.created_at,
    r.city,
    r.transcript,
    r.source_id,
    r.cluster_id,
    u.source_urls,
    r.category,
    ic.ics_categories,
    r.image_url,
    r.all_day,
    r.duplicate_group,
    r.duplicate_group_representative,
    COALESCE(n.source_names, ARRAY[]::text[]) AS source_names,
    r.merged_ids
FROM rolled r
LEFT JOIN name_agg n USING (city, start_time, group_key)
LEFT JOIN url_agg u USING (city, start_time, group_key)
LEFT JOIN ics_categories_pick ic USING (city, start_time, group_key)
ORDER BY r.start_time;

CREATE UNIQUE INDEX IF NOT EXISTS deduplicated_events_id_idx ON deduplicated_events (id);
CREATE INDEX IF NOT EXISTS deduplicated_events_city_start_time_idx ON deduplicated_events (city, start_time);

GRANT SELECT ON deduplicated_events TO anon, authenticated, service_role;

-- RPC used by the nightly build after load-events completes.
-- CI-only since 20261024130000_secure_definer_functions.sql
-- (GHSA-69r3-3gxw-fm4g): a loop of calls pinned database CPU from anon, so
-- EXECUTE is revoked from PUBLIC, anon and authenticated.
CREATE OR REPLACE FUNCTION public.refresh_deduplicated_events()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET statement_timeout TO '0'
SET search_path = ''
AS $function$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY public.deduplicated_events;
END;
$function$;

REVOKE EXECUTE ON FUNCTION public.refresh_deduplicated_events() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.refresh_deduplicated_events() TO service_role;
