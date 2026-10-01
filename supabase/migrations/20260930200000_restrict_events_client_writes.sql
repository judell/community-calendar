-- Close direct client write access to events.
--
-- Found 2026-09-30 while reviewing PR #87: anyone holding the publishable
-- (anon) key — which is public in xmlui/config.json and served to every
-- browser — could insert rows into events. Verified with the public key
-- and a deliberately malformed body, so no row was created:
--
--   POST /rest/v1/events  {}  ->  23502 null value in column "title"
--
-- 23502, not 42501: the request cleared both the grant and RLS and failed
-- only on a column constraint. Two settings combined to allow it. The
-- grant gave anon every privilege, and the policy "Service function can
-- insert events" had no TO clause (so it covered anon) with
-- WITH CHECK (true) — no restriction at all. "Auth users can update event
-- category" is the same shape for UPDATE, and despite its name RLS filters
-- rows and never columns, so it permitted rewriting any column.
--
-- Nothing legitimate used either path:
--
--   * Both event-writing edge functions use the service-role key
--     (capture-event, load-events), and service_role has rolbypassrls,
--     so it ignores policies entirely — dropping them cannot affect the
--     nightly build.
--   * No client code updates events: there is no method="patch" in any app
--     markup, and the only client references to /rest/v1/events are a
--     DELETE (Manage Feeds) and a SELECT (FeedTile).
--   * Category edits write category_overrides; the trigger
--     apply_category_override is SECURITY DEFINER and updates events as
--     the function owner, needing no caller privilege. The update policy
--     was vestigial, predating that system (20260722200000).
--
-- Retained deliberately: select for anon and authenticated (the app reads
-- events), and delete for authenticated, which Manage Feeds uses and which
-- RLS still restricts to rows an admin may remove.
--
-- Supersedes the anon/authenticated write grants that PR #87 introduces
-- for freshly built databases.

drop policy if exists "Service function can insert events" on public.events;
drop policy if exists "Auth users can update event category" on public.events;

revoke insert, update, delete on public.events from anon;
revoke insert, update on public.events from authenticated;
