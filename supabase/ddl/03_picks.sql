-- Picks table - stores user's picked events

CREATE TABLE IF NOT EXISTS picks (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  event_id bigint REFERENCES events(id) ON DELETE CASCADE NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, event_id)
);

-- Enable Row Level Security
ALTER TABLE picks ENABLE ROW LEVEL SECURITY;

-- Users can only view their own picks
CREATE POLICY "Users can view own picks"
  ON picks FOR SELECT
  USING (auth.uid() = user_id);

-- Users can only insert their own picks
CREATE POLICY "Users can insert own picks"
  ON picks FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own picks
CREATE POLICY "Users can delete own picks"
  ON picks FOR DELETE
  USING (auth.uid() = user_id);
