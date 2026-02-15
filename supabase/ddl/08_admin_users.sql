-- Admin users table - server-authorized access for privileged UI/actions

CREATE TABLE IF NOT EXISTS admin_users (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Users can only view their own admin row (presence means admin)
CREATE POLICY "Users can view own admin status"
  ON admin_users FOR SELECT
  USING (auth.uid() = user_id);

-- Service role manages admin grants/revokes
CREATE POLICY "Service role can manage admin users"
  ON admin_users FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
