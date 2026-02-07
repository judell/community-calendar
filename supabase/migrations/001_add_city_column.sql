-- Migration: Add city column to events table
-- Run this against the live Supabase database before deploying new code

-- Add city column
ALTER TABLE events ADD COLUMN IF NOT EXISTS city text;

-- Create index for city filtering
CREATE INDEX IF NOT EXISTS events_city_idx ON events (city);
