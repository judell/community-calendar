-- Feed tokens table - unique token per user for ICS feed access

CREATE TABLE IF NOT EXISTS feed_tokens (
  id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
  token uuid DEFAULT gen_random_uuid() NOT NULL UNIQUE,
  created_at timestamptz DEFAULT now()
);

-- Index for token lookups (used by my-picks edge function)
CREATE INDEX IF NOT EXISTS feed_tokens_token_idx ON feed_tokens (token);

-- Enable Row Level Security
ALTER TABLE feed_tokens ENABLE ROW LEVEL SECURITY;

-- Users can only view their own feed token
CREATE POLICY "Users can view own feed token"
  ON feed_tokens FOR SELECT
  USING (auth.uid() = user_id);

-- Users can insert their own feed token (created on first sign-in)
CREATE POLICY "Users can insert own feed token"
  ON feed_tokens FOR INSERT
  WITH CHECK (auth.uid() = user_id);
