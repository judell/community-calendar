-- Admin GitHub users table - allows preapproval before first sign-in

CREATE TABLE IF NOT EXISTS admin_github_users (
  github_user text PRIMARY KEY,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE admin_github_users ENABLE ROW LEVEL SECURITY;

-- Helper function: reads GitHub username from server-side auth.users record
-- (not from the client-writable JWT user_metadata claim)
CREATE OR REPLACE FUNCTION public.get_my_github_username()
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT raw_user_meta_data->>'user_name'
  FROM auth.users
  WHERE id = auth.uid();
$$;

-- Authenticated users can only read their own GitHub username row
CREATE POLICY "Users can view own github admin status"
  ON admin_github_users FOR SELECT
  TO authenticated
  USING (github_user = coalesce(public.get_my_github_username(), ''));

-- Service role manages admin grants/revokes
CREATE POLICY "Service role can manage github admin users"
  ON admin_github_users FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
