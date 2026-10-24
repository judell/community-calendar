-- Drop the unused source_names cache and its refresh RPC.
--
-- Nothing reads public.source_names. The app and my-picks read
-- events.source_names (the structured column the confidence route writes), and
-- no view or function joins the table. Its only consumer was its own pgTAP
-- suite. Keeping a SECURITY DEFINER writer with statement_timeout = 0 for a
-- table nobody reads is a needless anon-era surface (GHSA-69r3-3gxw-fm4g), so
-- the nightly step, the RPC, and the table all go.

DROP FUNCTION IF EXISTS public.refresh_source_names(text);
DROP TABLE IF EXISTS public.source_names;
