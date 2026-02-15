-- Admin GitHub users table - allows preapproval before first sign-in

CREATE TABLE IF NOT EXISTS admin_github_users (
  github_user text PRIMARY KEY,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE admin_github_users ENABLE ROW LEVEL SECURITY;

-- Authenticated users can only read their own GitHub username row
CREATE POLICY "Users can view own github admin status"
  ON admin_github_users FOR SELECT
  USING (github_user = coalesce(auth.jwt()->'user_metadata'->>'user_name', ''));

-- Service role manages admin grants/revokes
CREATE POLICY "Service role can manage github admin users"
  ON admin_github_users FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
