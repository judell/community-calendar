-- feeds: all calendar sources (ICS URLs, scrapers, curators) per city
-- Source of truth for what feeds are in the system.
-- Replaces feeds.txt and pending_feeds.

CREATE TABLE feeds (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  city text NOT NULL,
  url text NOT NULL,
  name text NOT NULL,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'pending', 'removed')),
  feed_type text NOT NULL CHECK (feed_type IN ('ics_url', 'scraper', 'curator')),
  scraper_cmd text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(city, url)
);

ALTER TABLE feeds ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read feeds" ON feeds FOR SELECT USING (true);

CREATE POLICY "Admin users can manage feeds" ON feeds FOR ALL
  USING (auth.uid() IN (SELECT user_id FROM admin_users));
