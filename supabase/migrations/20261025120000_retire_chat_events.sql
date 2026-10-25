-- Retire the experimental chat-events concierge (spring 2026 beta).
--
-- Never wired into the app or the build, unused since 2026-04-21, and still
-- publicly reachable: five functions were executable with the publishable
-- key, three of them SECURITY DEFINER (run_chat_events_sql,
-- refresh_chat_event_documents, refresh_deduplicated_chat_events).
-- The three chat edge functions were deleted separately (Supabase CLI).
--
-- Archived before dropping: legacy/chat-events/ holds the edge function
-- source and schema.sql with every definition below. Row data was not
-- archived: chat_beta_users / chat_beta_logs hold testers' personal data,
-- the derived tables regenerate from events, and event_facets was empty.
--
-- Nothing outside these objects depends on them (checked pg_depend,
-- pg_trigger, pg_constraint); their only foreign keys point outward to
-- auth.users and events. No CASCADE, so an unexpected dependent fails the
-- migration instead of silently disappearing.

DROP FUNCTION public.run_chat_events_sql(text);
DROP FUNCTION public.hybrid_search_events(text, vector, text, timestamptz, timestamptz, integer, double precision, double precision, integer);
DROP FUNCTION public.refresh_chat_event_documents();
DROP FUNCTION public.refresh_deduplicated_chat_events();
DROP FUNCTION public.chat_event_document_content(text, text, text, text, text, text, text[]);

DROP TABLE public.chat_event_documents;
DROP MATERIALIZED VIEW public.deduplicated_chat_events;
DROP TABLE public.event_facets;
DROP TABLE public.chat_beta_logs;
DROP TABLE public.chat_beta_users;
