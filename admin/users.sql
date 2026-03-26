SELECT
  to_char(u.last_sign_in_at, 'YYYY-MM-DD:HH') AS last_sign_in,
  u.email, to_char(u.created_at, 'YYYY-MM-DD') AS created,
  string_agg(i.provider, ', ') AS providers FROM auth.users u
  LEFT JOIN auth.identities i ON u.id = i.user_id
  GROUP BY u.email, u.last_sign_in_at, u.created_at
  ORDER BY u.last_sign_in_at
