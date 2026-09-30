-- Explicit Data API grants for tables created by earlier migrations.
--
-- Supabase stops granting new public tables to anon, authenticated and service_role
-- automatically on 2026-10-30. Existing tables on the hosted project keep the grants they
-- have, so this migration changes nothing there. It makes a database built from these
-- migrations without automatic grants (a preview branch, a new project, a local reset with
-- auto_expose_new_tables = false) match: each table gets what its RLS policies and server
-- code need, and every serial sequence behind a client insert gets usage.

grant select, insert, update, delete on public.admin_users to service_role;
grant select on public.admin_users to anon, authenticated;
grant select, insert, update, delete on public.events to service_role;
grant select, insert, delete on public.events to anon, authenticated;
grant select, insert, update, delete on public.picks to service_role;
grant select, insert, delete on public.picks to anon, authenticated;
grant select, insert, update, delete on public.feed_tokens to service_role;
grant select, insert on public.feed_tokens to anon, authenticated;
grant select, insert, update, delete on public.event_enrichments to service_role;
grant select, insert, update, delete on public.event_enrichments to anon, authenticated;
grant select on public.distinct_cities to service_role;
grant select, insert, update, delete on public.admin_github_users to service_role;
grant select on public.admin_github_users to authenticated;
grant select, insert, update, delete on public.user_settings to service_role;
grant select, insert, update on public.user_settings to anon, authenticated;
grant select, insert, update, delete on public.admin_google_users to service_role;
grant select on public.admin_google_users to authenticated;
grant select, insert, update, delete on public.source_suggestions to service_role;
grant select, insert on public.source_suggestions to anon, authenticated;
grant select, insert, update, delete on public.category_overrides to service_role;
grant select, insert, update on public.category_overrides to anon, authenticated;
grant select on public.category_overrides_view to service_role;
grant select, insert, update, delete on public.source_names to service_role;
grant select on public.source_names to anon, authenticated;
grant select, insert, update, delete on public.feeds to service_role;
grant select, insert, update, delete on public.feeds to anon, authenticated;
