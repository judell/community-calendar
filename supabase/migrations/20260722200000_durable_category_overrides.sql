-- Durable category overrides (worklist: durable-category-overrides)
--
-- Curator corrections were write-once cosmetic: the nightly build's
-- load-events upsert overwrote events.category with the archive-carried
-- value, and ON DELETE CASCADE destroyed override rows whenever
-- delete_stale_events removed a churned event (~29 rows lost to date).
--
-- This migration makes overrides durable:
--   1. category_overrides.source_uid becomes the durable key (backfilled,
--      unique, auto-populated by the overrides trigger).
--   2. event_id FK becomes ON DELETE SET NULL so corrections outlive
--      event churn.
--   3. A trigger on events re-asserts the override category on every
--      insert/update touching category — no writer can clobber a
--      curator correction — and re-attaches event_id when a churned
--      event reappears under the same source_uid.

-- 1. Durable key ------------------------------------------------------

ALTER TABLE category_overrides ADD COLUMN IF NOT EXISTS source_uid text;

UPDATE category_overrides co
SET source_uid = e.source_uid
FROM events e
WHERE co.event_id = e.id AND co.source_uid IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS category_overrides_source_uid_key
  ON category_overrides (source_uid);

-- 2. Survive event deletion -------------------------------------------

ALTER TABLE category_overrides
  DROP CONSTRAINT category_overrides_event_id_fkey;

ALTER TABLE category_overrides
  ADD CONSTRAINT category_overrides_event_id_fkey
  FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL;

-- 3. Overrides trigger: backfill source_uid, snapshot original_category,
--    and propagate to events only when the category actually changed
--    (an event_id re-attach must not recurse into events).

CREATE OR REPLACE FUNCTION apply_category_override()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.source_uid IS NULL AND NEW.event_id IS NOT NULL THEN
    SELECT source_uid INTO NEW.source_uid FROM events WHERE id = NEW.event_id;
  END IF;
  IF NEW.original_category IS NULL AND NEW.event_id IS NOT NULL THEN
    SELECT category INTO NEW.original_category FROM events WHERE id = NEW.event_id;
  END IF;
  IF TG_OP = 'INSERT' OR NEW.category IS DISTINCT FROM OLD.category THEN
    UPDATE events SET category = NEW.category WHERE id = NEW.event_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Events triggers: the enforcement point. BEFORE forces the curator's
--    category on any insert/update touching category (nightly upsert
--    included). AFTER re-attaches the override's event_id for re-created
--    events — it must run AFTER because during BEFORE INSERT the events
--    row doesn't exist yet and the FK on event_id would reject it.
--    Depth guards skip both when the write originated from
--    apply_category_override itself.

CREATE OR REPLACE FUNCTION enforce_category_override()
RETURNS TRIGGER AS $$
DECLARE
  o_category text;
BEGIN
  IF pg_trigger_depth() > 1 OR NEW.source_uid IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT category INTO o_category
  FROM category_overrides
  WHERE source_uid = NEW.source_uid;
  IF FOUND THEN
    NEW.category := o_category;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION reattach_category_override()
RETURNS TRIGGER AS $$
BEGIN
  IF pg_trigger_depth() > 1 OR NEW.source_uid IS NULL THEN
    RETURN NULL;
  END IF;
  UPDATE category_overrides
  SET event_id = NEW.id
  WHERE source_uid = NEW.source_uid
    AND event_id IS DISTINCT FROM NEW.id;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_event_category_write ON events;
CREATE TRIGGER on_event_category_write
  BEFORE INSERT OR UPDATE OF category ON events
  FOR EACH ROW EXECUTE FUNCTION enforce_category_override();

DROP TRIGGER IF EXISTS on_event_override_reattach ON events;
CREATE TRIGGER on_event_override_reattach
  AFTER INSERT OR UPDATE OF category ON events
  FOR EACH ROW EXECUTE FUNCTION reattach_category_override();
