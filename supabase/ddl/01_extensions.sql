-- Enable required extensions

-- HTTP requests from database (for scheduled jobs)
CREATE EXTENSION IF NOT EXISTS pg_net;

-- Scheduled jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;
