-- Enable the extension if not already
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule to run daily at 6am UTC
SELECT cron.schedule(
  'load-events-daily',
  '0 6 * * *',
  $$
  SELECT net.http_post(
    url := 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events',
    headers := jsonb_build_object(
      'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6cGR1YWx2d3NwZ3FnaHJ5c3l6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5MTQwOTEsImV4cCI6MjA4NTQ5MDA5MX0.WZtNKDSRLmeQLU2fpWF_R8KN4Gd8hzMg9VzC7DZn89A',
      'Content-Type', 'application/json'
    ),
    body := '{}'::jsonb
  );
  $$
);

-- List all scheduled jobs
-- SELECT * FROM cron.job;

-- Delete a job
-- SELECT cron.unschedule('load-events-daily');
