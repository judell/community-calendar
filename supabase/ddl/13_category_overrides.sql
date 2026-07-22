-- Category overrides: curator corrections to LLM-assigned event categories
-- These feed back as few-shot examples to improve future classifications
--
-- Durable since 20260722200000_durable_category_overrides.sql:
-- source_uid is the durable key (survives event delete/re-create), and a
-- trigger on events re-asserts the override on every category write, so
-- the nightly load-events upsert cannot clobber a curator correction.

CREATE TABLE IF NOT EXISTS category_overrides (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id bigint REFERENCES events(id) ON DELETE SET NULL,
  category text NOT NULL,
  original_category text,
  curator_id uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  source_uid text,      -- durable key; auto-backfilled from events on insert
  event_title text,     -- snapshot for few-shot examples (survives event deletion)
  event_location text,  -- snapshot for few-shot examples
  event_city text,      -- snapshot; lets the classifier prefer same-city examples
  UNIQUE(event_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS category_overrides_source_uid_key
  ON category_overrides (source_uid);

ALTER TABLE category_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read overrides" ON category_overrides FOR SELECT USING (true);
CREATE POLICY "Auth users can insert overrides" ON category_overrides FOR INSERT WITH CHECK (auth.uid() = curator_id);
CREATE POLICY "Auth users can update own overrides" ON category_overrides FOR UPDATE USING (auth.uid() = curator_id);

-- Trigger (on category_overrides): backfill source_uid, original_category,
-- and the event_title/location/city snapshot from events, and propagate the
-- override to events.category — but only when the category actually changed
-- (an event_id re-attach from the events-side trigger must not recurse back
-- into events).
CREATE OR REPLACE FUNCTION apply_category_override()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.event_id IS NOT NULL THEN
    IF NEW.source_uid IS NULL THEN
      SELECT source_uid INTO NEW.source_uid FROM events WHERE id = NEW.event_id;
    END IF;
    IF NEW.original_category IS NULL THEN
      SELECT category INTO NEW.original_category FROM events WHERE id = NEW.event_id;
    END IF;
    IF NEW.event_title IS NULL THEN
      SELECT title, location, city
      INTO NEW.event_title, NEW.event_location, NEW.event_city
      FROM events WHERE id = NEW.event_id;
    END IF;
  END IF;
  IF TG_OP = 'INSERT' OR NEW.category IS DISTINCT FROM OLD.category THEN
    UPDATE events SET category = NEW.category WHERE id = NEW.event_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_category_override
  BEFORE INSERT OR UPDATE ON category_overrides
  FOR EACH ROW EXECUTE FUNCTION apply_category_override();

-- Triggers (on events): the enforcement point. BEFORE forces the curator's
-- category on any insert/update touching category (nightly upsert included).
-- AFTER re-attaches the override's event_id for re-created events — it must
-- run AFTER because during BEFORE INSERT the events row doesn't exist yet
-- and the FK on event_id would reject it. Depth guards skip both when the
-- write originated from apply_category_override itself.
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

CREATE TRIGGER on_event_category_write
  BEFORE INSERT OR UPDATE OF category ON events
  FOR EACH ROW EXECUTE FUNCTION enforce_category_override();

CREATE TRIGGER on_event_override_reattach
  AFTER INSERT OR UPDATE OF category ON events
  FOR EACH ROW EXECUTE FUNCTION reattach_category_override();

-- SECURITY DEFINER function to resolve curator name without exposing auth.users
CREATE OR REPLACE FUNCTION public.get_curator_name(curator_uuid uuid)
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT raw_user_meta_data->>'user_name'
  FROM auth.users
  WHERE id = curator_uuid;
$$;

-- View for report: uses function instead of direct auth.users join
CREATE OR REPLACE VIEW category_overrides_view WITH (security_invoker = true) AS
SELECT
  co.id,
  co.category,
  co.original_category,
  co.created_at,
  co.event_id,
  public.get_curator_name(co.curator_id) AS curator_name
FROM category_overrides co;

REVOKE ALL ON category_overrides_view FROM anon, authenticated;
GRANT SELECT ON category_overrides_view TO anon, authenticated;
