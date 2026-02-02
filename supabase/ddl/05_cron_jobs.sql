-- Scheduled jobs for automatic event loading

-- Schedule load-events to run daily at 6am UTC
-- Note: Replace the Authorization token with your project's anon key (legacy format)
SELECT cron.schedule(
  'load-events-daily',
  '0 6 * * *',
  $$
  SELECT net.http_post(
    url := 'https://dzpdualvwspgqghrysyz.supabase.co/functions/v1/load-events',
    headers := jsonb_build_object(
      'Authorization', 'Bearer <YOUR_LEGACY_ANON_KEY>',
      'Content-Type', 'application/json'
    ),
    body := '{}'::jsonb
  );
  $$
);

-- Useful commands:
-- List all scheduled jobs:
--   SELECT * FROM cron.job;
--
-- Delete a job:
--   SELECT cron.unschedule('load-events-daily');
--
-- Run job manually (for testing):
--   SELECT cron.schedule('manual-load', 'now', $$ ... $$);
