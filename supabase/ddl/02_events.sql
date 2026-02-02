-- Events table - stores calendar events from all sources

CREATE TABLE IF NOT EXISTS events (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  title text NOT NULL,
  start_time timestamptz NOT NULL,
  end_time timestamptz,
  location text,
  description text,
  url text,
  source text,
  source_uid text UNIQUE,
  created_at timestamptz DEFAULT now()
);

-- Index for date range queries
CREATE INDEX IF NOT EXISTS events_start_time_idx ON events (start_time);

-- Index for source filtering
CREATE INDEX IF NOT EXISTS events_source_idx ON events (source);

-- Enable Row Level Security (public read access)
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read events
CREATE POLICY "Events are publicly readable"
  ON events FOR SELECT
  USING (true);
