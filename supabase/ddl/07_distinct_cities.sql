-- View for distinct city names (used by city picker UI)
CREATE OR REPLACE VIEW distinct_cities WITH (security_invoker = true) AS
SELECT DISTINCT city FROM events WHERE city IS NOT NULL ORDER BY city;

REVOKE ALL ON distinct_cities FROM anon, authenticated;
GRANT SELECT ON distinct_cities TO anon, authenticated;
