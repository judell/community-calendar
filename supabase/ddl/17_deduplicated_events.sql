-- View: deduplicated_events
-- Server-side deduplication of events by normalized title + start_time
-- Groups events with the same (lowercased, trimmed) title and start_time,
-- merging sources and picking the first non-null value for other columns.

CREATE OR REPLACE VIEW deduplicated_events AS
SELECT
    min(id) AS id,
    (array_agg(title ORDER BY e.id))[1] AS title,
    start_time,
    (array_agg(end_time ORDER BY e.id) FILTER (WHERE end_time IS NOT NULL))[1] AS end_time,
    (array_agg(url ORDER BY e.id) FILTER (WHERE url IS NOT NULL AND url <> ''))[1] AS url,
    (array_agg(location ORDER BY e.id) FILTER (WHERE location IS NOT NULL))[1] AS location,
    (array_agg(description ORDER BY e.id) FILTER (WHERE description IS NOT NULL))[1] AS description,
    string_agg(DISTINCT source, ', ') AS source,
    (array_agg(source_uid ORDER BY e.id))[1] AS source_uid,
    min(created_at) AS created_at,
    (array_agg(city ORDER BY e.id))[1] AS city,
    (array_agg(transcript ORDER BY e.id) FILTER (WHERE transcript IS NOT NULL))[1] AS transcript,
    (array_agg(source_id ORDER BY e.id))[1] AS source_id,
    (array_agg(cluster_id ORDER BY e.id) FILTER (WHERE cluster_id IS NOT NULL))[1] AS cluster_id,
    (array_agg(source_urls ORDER BY e.id) FILTER (WHERE source_urls IS NOT NULL))[1] AS source_urls,
    (array_agg(category ORDER BY e.id) FILTER (WHERE category IS NOT NULL))[1] AS category,
    (SELECT ic.ics_categories
       FROM events ic
      WHERE ic.ics_categories IS NOT NULL AND ic.id = min(e.id)) AS ics_categories,
    (array_agg(image_url ORDER BY e.id) FILTER (WHERE image_url IS NOT NULL))[1] AS image_url,
    bool_or(all_day) AS all_day,
    array_agg(id ORDER BY e.id) AS merged_ids
FROM events e
WHERE source <> 'poster_capture'
GROUP BY lower(TRIM(BOTH FROM title)), start_time
ORDER BY start_time;
