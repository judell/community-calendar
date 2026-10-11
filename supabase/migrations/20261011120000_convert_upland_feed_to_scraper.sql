-- Migration: Convert the Upland Brewing feed to a Tribe REST scraper
-- (issue #188)
--
-- The registered Bloomington row for "Upland Brewing" is the Tribe/WordPress
-- iCal export (https://uplandbeer.com/events/?ical=1). Upland's Tribe calendar
-- has no upcoming events (last event 2025-02-07; the site renders "There are no
-- upcoming events"), so the export answers with an empty body. download_feeds.py
-- writes that zero-byte file to uplandbeer.ics, which lacks BEGIN:VCALENDAR and
-- is classified not_ics — a broken_feed in the Bloomington feed-health report.
--
-- The Tribe REST API is live and reachable from the project's default
-- User-Agent (verified 2026-10-11: HTTP 200, valid-empty for the current
-- window; the bare "Mozilla/5.0" UA is Cloudflare-403'd, the project UA is
-- not). Convert the row from ics_url to the parameterized scrapers/tribe_rest.py
-- (the #185 Hard Truth move): a dormant calendar then writes a valid-empty
-- calendar classified "quiet", not broken_feed, and repopulates when Upland
-- posts again. The conversion goes through feeds_validate_scraper_row, so the
-- scraper row is validated at insert/update time. Idempotent and a no-op on
-- forks without the row.

DO $$
DECLARE
  old_url text := 'https://uplandbeer.com/events/?ical=1';
  out_path text := 'cities/bloomington/uplandbeer.ics';
  cmd text := 'python scrapers/tribe_rest.py --api-base "https://uplandbeer.com" --name "Upland Brewing" --timezone America/Indiana/Indianapolis --output cities/bloomington/uplandbeer.ics';
BEGIN
  UPDATE feeds
  SET feed_type = 'scraper',
      url = out_path,
      scraper_cmd = cmd
  WHERE city = 'bloomington'
    AND url = old_url;
END $$;
