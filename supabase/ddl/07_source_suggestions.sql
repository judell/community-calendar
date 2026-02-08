-- Source suggestions table - anonymous community submissions for new calendar sources

CREATE TABLE IF NOT EXISTS source_suggestions (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  city text NOT NULL,
  name text NOT NULL,
  url text,
  feed_type text,
  notes text,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE source_suggestions ENABLE ROW LEVEL SECURITY;

-- Anyone can insert suggestions (anonymous, no auth required)
CREATE POLICY "Anyone can insert suggestions"
  ON source_suggestions FOR INSERT
  WITH CHECK (true);

-- Anyone can read suggestions
CREATE POLICY "Anyone can read suggestions"
  ON source_suggestions FOR SELECT
  USING (true);
