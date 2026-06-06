-- Add index on events.source to improve performance of refresh_source_names()
-- The function performs multiple LIKE operations on this column, which were causing
-- full table scans and 3+ second execution times.
--
-- Issue: #12
-- Using CONCURRENTLY to avoid locking the table during index creation.

CREATE INDEX CONCURRENTLY IF NOT EXISTS events_source_idx ON events (source);
