-- Category overrides: curator corrections to LLM-assigned event categories
-- These feed back as few-shot examples to improve future classifications

CREATE TABLE IF NOT EXISTS category_overrides (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,
  category text NOT NULL,
  original_category text,
  curator_id uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  UNIQUE(event_id)
);

ALTER TABLE category_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read overrides" ON category_overrides FOR SELECT USING (true);
CREATE POLICY "Auth users can insert overrides" ON category_overrides FOR INSERT WITH CHECK (auth.uid() = curator_id);
CREATE POLICY "Auth users can update own overrides" ON category_overrides FOR UPDATE USING (auth.uid() = curator_id);

-- Trigger: store original category then propagate override to events.category
CREATE OR REPLACE FUNCTION apply_category_override()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.original_category IS NULL THEN
    SELECT category INTO NEW.original_category FROM events WHERE id = NEW.event_id;
  END IF;
  UPDATE events SET category = NEW.category WHERE id = NEW.event_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_category_override
  BEFORE INSERT OR UPDATE ON category_overrides
  FOR EACH ROW EXECUTE FUNCTION apply_category_override();

-- View for report: joins curator name from auth.users
CREATE OR REPLACE VIEW category_overrides_view AS
SELECT
  co.id,
  co.category,
  co.original_category,
  co.created_at,
  co.event_id,
  u.raw_user_meta_data->>'user_name' AS curator_name
FROM category_overrides co
LEFT JOIN auth.users u ON u.id = co.curator_id;
