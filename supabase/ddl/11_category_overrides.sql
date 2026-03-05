-- Category overrides: curator corrections to LLM-assigned event categories
-- These feed back as few-shot examples to improve future classifications

CREATE TABLE IF NOT EXISTS category_overrides (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,
  category text NOT NULL,
  curator_id uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now(),
  UNIQUE(event_id)
);

ALTER TABLE category_overrides ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read overrides" ON category_overrides FOR SELECT USING (true);
CREATE POLICY "Auth users can insert overrides" ON category_overrides FOR INSERT WITH CHECK (auth.uid() = curator_id);
CREATE POLICY "Auth users can update own overrides" ON category_overrides FOR UPDATE USING (auth.uid() = curator_id);

-- Trigger: automatically propagate override to events.category
CREATE OR REPLACE FUNCTION apply_category_override()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE events SET category = NEW.category WHERE id = NEW.event_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_category_override
  AFTER INSERT OR UPDATE ON category_overrides
  FOR EACH ROW EXECUTE FUNCTION apply_category_override();
