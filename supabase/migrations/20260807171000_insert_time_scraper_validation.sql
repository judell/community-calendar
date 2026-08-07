-- Insert-time validation for scraper rows (cleanup-plan item 4, DB-first
-- prerequisite). Malformed rows found in the 2026-08 clean pass — legacy
-- "cmd:" prefixes, a row with no command at all, rows keyed by page URLs
-- instead of output paths, URL-keyed legacy duplicates — all entered the
-- feeds table silently and were only caught months later by audits. Once
-- DB rows drive scraper execution, a bad row becomes a bad run, so reject
-- them at write time, on every write path at once.
--
-- Removed-status tombstones are exempt so history is not invalidated.
-- All 350 active scraper rows passed these rules at migration time.

CREATE OR REPLACE FUNCTION validate_scraper_row()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.feed_type = 'scraper' AND coalesce(NEW.status, 'active') <> 'removed' THEN
    IF NEW.url IS NULL OR NEW.url !~ '^cities/[a-z0-9-]+/[A-Za-z0-9._-]+\.ics$' THEN
      RAISE EXCEPTION
        'scraper row rejected: url must be an output path like cities/<city>/<file>.ics, got %',
        coalesce(NEW.url, '<null>');
    END IF;
    IF NEW.scraper_cmd IS NULL OR btrim(NEW.scraper_cmd) = '' THEN
      RAISE EXCEPTION
        'scraper row rejected: scraper_cmd is required for non-removed scraper rows (url %)',
        NEW.url;
    END IF;
    IF NEW.scraper_cmd !~ '^python (scrapers|scripts)/' THEN
      RAISE EXCEPTION
        'scraper row rejected: scraper_cmd must start with "python scrapers/" or "python scripts/", got %',
        left(NEW.scraper_cmd, 80);
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS feeds_validate_scraper_row ON feeds;
CREATE TRIGGER feeds_validate_scraper_row
BEFORE INSERT OR UPDATE ON feeds
FOR EACH ROW EXECUTE FUNCTION validate_scraper_row();
