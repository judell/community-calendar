-- Migration: curator feeds stop carrying their token in feeds.url
-- (GHSA-3pg8-w4j4-6wv8)
--
-- A picks feed is authenticated only by its ?token= query param. `feeds` is
-- world-readable (ddl/16_feeds.sql) and re-exported to cities/<city>/feeds.txt
-- on every build, so storing that URL there published a read-only capability
-- URL for the curator's saved-event feed (and report.py then quoted it into
-- the Pages-served report.json).
--
-- Curator rows now name the curator instead: curator_user_id, with url set to
-- the non-secret curator://<user_id>. download_feeds.py mints the real URL from
-- feed_tokens at download time. That table is RLS-scoped to its owner, so
-- rotation needs no feeds edit and no token can reach the repo again.
--
-- A row whose token belongs to another deployment cannot be resolved here
-- (feed_tokens is per-project) and is retired with its events. Idempotent: a
-- second run converts nothing, rotates nothing, deletes nothing.

-- The curator names the feed. ON DELETE RESTRICT, not CASCADE: deleting the
-- account must not drop the feed row behind remove_feed()'s back and strand
-- the events it imported (ADR 0007 is the only ownership-aware cleanup).
-- Retire the feed first, then the account can go.
ALTER TABLE feeds ADD COLUMN IF NOT EXISTS curator_user_id uuid;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS feeds_curator_user_id_fkey;
ALTER TABLE feeds
  ADD CONSTRAINT feeds_curator_user_id_fkey
  FOREIGN KEY (curator_user_id)
  REFERENCES auth.users(id) ON DELETE RESTRICT;

DO $$
DECLARE
  r record;
  new_stem text;
  old_stem text;
BEGIN
  -- MATERIALIZED: the body rewrites feeds.url, and mutating the table a cursor
  -- scans is the classic plpgsql footgun.
  --
  -- Select by the function path, not by "?token=": my-picks accepts the token
  -- after another parameter (?format=ics&token=...), and a narrower selector
  -- would leave that row for the CHECK below to abort the whole migration.
  FOR r IN
    WITH targets AS MATERIALIZED (
      SELECT f.id, f.url AS old_url, f.city, t.id AS token_id, t.user_id
      FROM feeds f
      JOIN feed_tokens t
        ON t.token = substring(
             f.url
             from 'token=([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})'
           )::uuid
      WHERE f.url LIKE '%/functions/v1/my-picks%'
    )
    SELECT * FROM targets
  LOOP
    -- A download is slugify(url).ics and events.source_id is that stem, so the
    -- new url renames the source. Re-label the rows the feed already imported,
    -- or the next sweep (scoped to sources that ran) never sees them and picks
    -- the curator has dropped stay in the calendar. Mirrors slugify's general
    -- case for a Supabase my-picks URL (host label + /functions/v1). The city
    -- predicate matters: that stem names the project, not the curator, so two
    -- curators on one project share it and an unscoped update would move the
    -- first city's events to whichever feed was processed first.
    old_stem := left(
      regexp_replace(
        lower(split_part(split_part(r.old_url, '://', 2), '.', 1) || '_functions_v1'),
        '[^a-z0-9]+',
        '_',
        'g'
      ),
      50
    );
    new_stem := replace(r.user_id::text, '-', '_');

    UPDATE events SET source_id = new_stem WHERE source_id = old_stem AND city = r.city;

    UPDATE feeds
    SET feed_type = 'curator',
        curator_user_id = r.user_id,
        url = 'curator://' || r.user_id,
        source_ids = array_replace(source_ids, old_stem, new_stem)
    WHERE id = r.id;

    -- The token is in public git history forever; rotate it so the published
    -- copy stops working. The curator re-copies the new URL from the app.
    UPDATE feed_tokens SET token = gen_random_uuid() WHERE id = r.token_id;
  END LOOP;
END $$;

-- Retire curator rows this deployment cannot mint a token for (e.g. a feed
-- served by another Supabase project). The selector is the CHECK's predicate
-- exactly: anything still named that way is unpublishable, so leaving it would
-- abort the ALTER TABLE below instead of removing the exposed credential.
-- Retiring goes through remove_feed(), the DB authority for source retirement
-- (ADR 0007), so its merge-survivor rules apply. remove_feed() is admin-gated,
-- and a raw SQL session has no JWT: present an admin claim the way
-- ddl/16_feeds.sql documents.
DO $$
DECLARE
  stale_ids bigint[];
  admin_id uuid;
BEGIN
  SELECT array_agg(id) INTO stale_ids
  FROM feeds
  WHERE url LIKE '%/functions/v1/my-picks%';

  IF stale_ids IS NULL THEN
    RETURN;
  END IF;

  SELECT user_id INTO admin_id FROM admin_users LIMIT 1;
  IF admin_id IS NULL THEN
    RAISE EXCEPTION
      'cannot retire curator feed(s) %: no admin_users row to authorize remove_feed()',
      stale_ids;
  END IF;

  PERFORM set_config(
    'request.jwt.claims', json_build_object('sub', admin_id)::text, true
  );
  PERFORM remove_feed(id) FROM unnest(stale_ids) AS id;
END $$;

-- A row that predates the constraint must not make the ADD below fail. The
-- token is already in git history; rotate local tokens first (the scrub below
-- discards the reference) and then scrub the whole capability URL so the
-- metadata cannot be re-exported. A name keeps a placeholder (NOT NULL) and a
-- scraper_cmd keeps its "python ..." prefix, so the row stays valid.
UPDATE feed_tokens t
SET token = gen_random_uuid()
WHERE t.token IN (
  SELECT substring(ref.value from 'token=([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})')::uuid
  FROM (
    SELECT name AS value FROM feeds WHERE name LIKE '%/functions/v1/my-picks%'
    UNION ALL
    SELECT fallback_url FROM feeds WHERE fallback_url LIKE '%/functions/v1/my-picks%'
    UNION ALL
    SELECT scraper_cmd FROM feeds WHERE scraper_cmd LIKE '%/functions/v1/my-picks%'
  ) ref
);
UPDATE feeds
SET fallback_url = NULL
WHERE fallback_url LIKE '%/functions/v1/my-picks%';
UPDATE feeds
SET name = regexp_replace(name, '\S*/functions/v1/my-picks\S*', '[redacted]', 'g')
WHERE name LIKE '%/functions/v1/my-picks%';
UPDATE feeds
SET scraper_cmd = regexp_replace(scraper_cmd, '\S*/functions/v1/my-picks\S*', '[redacted]', 'g')
WHERE scraper_cmd LIKE '%/functions/v1/my-picks%';

-- Only these two constraints keep the token out. A CHECK covers every writer
-- (app dialog, pending_feeds, seed scripts, ad-hoc SQL), with no trigger to
-- maintain. Every field that reaches the repo or the public events payload is
-- covered, not just url: name is exported as the source attribution,
-- scraper_cmd is exported as a comment, and fallback_url is copied into
-- X-SOURCE-URL. The older name is dropped too so a database that ran an
-- earlier copy of this migration ends up with one constraint.
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS feeds_url_has_no_capability_token;
ALTER TABLE feeds DROP CONSTRAINT IF EXISTS feeds_metadata_has_no_capability_token;
ALTER TABLE feeds
  ADD CONSTRAINT feeds_metadata_has_no_capability_token
  CHECK (
    url NOT LIKE '%/functions/v1/my-picks%'
    AND name NOT LIKE '%/functions/v1/my-picks%'
    AND coalesce(scraper_cmd, '') NOT LIKE '%/functions/v1/my-picks%'
    AND coalesce(fallback_url, '') NOT LIKE '%/functions/v1/my-picks%'
  );

ALTER TABLE feeds DROP CONSTRAINT IF EXISTS feeds_curator_user_matches_type;
ALTER TABLE feeds
  ADD CONSTRAINT feeds_curator_user_matches_type
  CHECK (
    (
      feed_type = 'curator'
      AND curator_user_id IS NOT NULL
      AND url = 'curator://' || curator_user_id
    )
    OR (feed_type <> 'curator' AND curator_user_id IS NULL)
  );
