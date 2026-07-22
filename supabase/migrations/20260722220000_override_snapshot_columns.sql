-- Few-shot durability: snapshot event context onto category_overrides
-- (worklist: few-shot-selection)
--
-- The classifier's few-shot examples were fetched via the events(...)
-- embed on event_id, so an override orphaned by event churn (event_id
-- NULL since durable_category_overrides) silently dropped out of the
-- prompt. Snapshot title/location/city onto the override row at write
-- time so orphaned corrections keep teaching, and city preference can
-- order examples without a join.

ALTER TABLE category_overrides
  ADD COLUMN IF NOT EXISTS event_title text,
  ADD COLUMN IF NOT EXISTS event_location text,
  ADD COLUMN IF NOT EXISTS event_city text;

UPDATE category_overrides co
SET event_title = e.title,
    event_location = e.location,
    event_city = e.city
FROM events e
WHERE co.event_id = e.id AND co.event_title IS NULL;

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
