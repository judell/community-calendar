-- Events table - stores calendar events from all sources

CREATE TABLE IF NOT EXISTS events (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  title text NOT NULL,
  start_time timestamptz NOT NULL,
  end_time timestamptz,
  location text,
  description text,
  url text,
  city text,                -- e.g., 'santarosa', 'sebastopol', 'cotati'
  source text,              -- e.g., 'bohemian', 'pressdemocrat' (no date suffix)
  source_id text,           -- filename-derived source identifier for curator reference
  source_uid text UNIQUE,   -- unique ID from source for deduplication
  transcript text,          -- Whisper transcript for audio-captured events
  cluster_id text,          -- groups similar events within same timeslot for UI display
  source_urls jsonb,        -- per-source URLs for aggregator attribution links
  category text,            -- auto-classified bucket (e.g., 'Music & Concerts', 'Arts & Culture')
  ics_categories text[],    -- CATEGORIES values from ICS source
  image_url text,           -- event image URL from ICS ATTACH or scraper
  all_day boolean DEFAULT false,  -- true for all-day events (VALUE=DATE in ICS)
  created_at timestamptz DEFAULT now()
);

-- Compound unique index for deduplication by source
CREATE UNIQUE INDEX IF NOT EXISTS events_source_source_uid_key ON events (source, source_uid);

-- Index for city filtering
CREATE INDEX IF NOT EXISTS events_city_idx ON events (city);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS events_category_idx ON events (category);

-- Enable Row Level Security (public read access)
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read events
CREATE POLICY "Anyone can read events"
  ON events FOR SELECT
  USING (true);

-- Allow service functions to insert events
CREATE POLICY "Service function can insert events"
  ON events FOR INSERT
  WITH CHECK (true);

-- Allow admin users to delete events
CREATE POLICY "Admin users can delete events"
  ON events FOR DELETE
  USING (auth.uid() IN (SELECT user_id FROM admin_users));
