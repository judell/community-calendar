-- Admin Google users table - allows preapproval before first sign-in

CREATE TABLE IF NOT EXISTS admin_google_users (
  google_email text PRIMARY KEY,
  created_at timestamptz DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE admin_google_users ENABLE ROW LEVEL SECURITY;

-- Helper function: reads email from server-side auth.users record
-- (not from the client-writable JWT claims)
CREATE OR REPLACE FUNCTION public.get_my_google_email()
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT email
  FROM auth.users
  WHERE id = auth.uid();
$$;

-- Authenticated users can only read their own Google email row
CREATE POLICY "Users can view own google admin status"
  ON admin_google_users FOR SELECT
  TO authenticated
  USING (google_email = coalesce(public.get_my_google_email(), ''));

-- Service role manages admin grants/revokes
CREATE POLICY "Service role can manage google admin users"
  ON admin_google_users FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
