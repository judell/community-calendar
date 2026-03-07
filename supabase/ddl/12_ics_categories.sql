-- Add ics_categories column to events table
-- Stores raw category tags from the ICS source file, used as classification hints

ALTER TABLE events ADD COLUMN IF NOT EXISTS ics_categories jsonb;
