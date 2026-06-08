-- Add index on events.source to improve performance of refresh_source_names()
-- and general source-column lookups.
--
-- refresh_source_names() splits events.source with string_to_array (no LIKE),
-- but an index on source still helps the grouped scan and other source filters.
--
-- Issue: #12
-- Note: CONCURRENTLY was intentionally dropped. It cannot run inside a
-- transaction block, which breaks transactional migration runners (supabase
-- db push / SQL editor). On a fresh/local DB the table is small and a brief
-- lock is harmless. For a zero-downtime build on a large live table, create
-- the index CONCURRENTLY as a separate manual ops step instead.

CREATE INDEX IF NOT EXISTS events_source_idx ON events (source);
