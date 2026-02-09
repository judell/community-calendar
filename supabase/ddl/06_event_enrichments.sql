-- Event enrichments table - curator overrides/additions per event
-- Self-standing: enrichments store their own title/start_time/city so they
-- survive even if the original event row is deleted.

CREATE TABLE IF NOT EXISTS event_enrichments (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE,  -- nullable
  curator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  rrule text,
  url text,
  description text,
  location text,
  end_time timestamptz,
  categories text[],
  notes text,
  title text,            -- copied from event at creation
  start_time timestamptz, -- copied from event at creation
  city text,             -- copied from event at creation
  curator_name text,     -- display name for source attribution
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(event_id, curator_id)
);

-- Index for event lookups
CREATE INDEX IF NOT EXISTS idx_event_enrichments_event_id ON event_enrichments (event_id);

-- Index for curator lookups
CREATE INDEX IF NOT EXISTS idx_event_enrichments_curator_id ON event_enrichments (curator_id);

-- Enable Row Level Security
ALTER TABLE event_enrichments ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read enrichments
CREATE POLICY "Enrichments are publicly readable"
  ON event_enrichments FOR SELECT
  USING (true);

-- Users can insert their own enrichments
CREATE POLICY "Users can insert own enrichments"
  ON event_enrichments FOR INSERT
  WITH CHECK (auth.uid() = curator_id);

-- Users can update their own enrichments
CREATE POLICY "Users can update own enrichments"
  ON event_enrichments FOR UPDATE
  USING (auth.uid() = curator_id);

-- Users can delete their own enrichments
CREATE POLICY "Users can delete own enrichments"
  ON event_enrichments FOR DELETE
  USING (auth.uid() = curator_id);
