-- View for distinct city names (used by city picker UI)
CREATE OR REPLACE VIEW distinct_cities AS
SELECT DISTINCT city FROM events WHERE city IS NOT NULL ORDER BY city;

GRANT SELECT ON distinct_cities TO anon, authenticated;
