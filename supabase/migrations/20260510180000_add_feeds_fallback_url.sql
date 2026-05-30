-- Add fallback_url to feeds: human-facing source page URL.
-- Distinct from feeds.url (machine ICS URL) and event.url (per-event page).
-- Injected as X-SOURCE-URL header in download_feeds.py for events that lack URL.
-- See issue #60.

ALTER TABLE feeds ADD COLUMN fallback_url text;
