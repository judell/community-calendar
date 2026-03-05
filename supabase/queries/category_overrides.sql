-- View category overrides with event details
SELECT
  co.id,
  co.category AS override_category,
  e.title,
  e.location,
  e.city,
  e.category AS current_category,
  co.created_at,
  u.email AS curator_email
FROM category_overrides co
JOIN events e ON e.id = co.event_id
LEFT JOIN auth.users u ON u.id = co.curator_id
ORDER BY co.created_at DESC;
