# Security Audit Notes

Date: 2026-02-15
Scope: Supabase RLS policies, edge function auth model, frontend data-access patterns.

## Confirmed Controls

- `picks` has per-user RLS for select/insert/delete via `auth.uid() = user_id`.
- `feed_tokens` has per-user RLS for select/insert via `auth.uid() = user_id`.
- `event_enrichments` is public-read with per-user write/delete via `curator_id`.
- Frontend calls to `picks` and `feed_tokens` include user bearer token; reads of `events` and `event_enrichments` are public by design.

## Findings / Risks

1. `events` insert policy is overly broad.
- Current policy: `WITH CHECK (true)`.
- Effect: any authenticated user can insert into `events` via REST unless otherwise blocked.
- File: `supabase/ddl/02_events.sql`.

2. Edge functions are configured without gateway JWT verification.
- Docs currently deploy with `--no-verify-jwt`.
- Security therefore depends on each function’s internal checks.
- Files: `supabase/README.md`, `supabase/functions/my-picks/README.md`.

3. `capture-event` extract mode appears unauthenticated.
- Extract path runs before auth validation.
- Commit path validates bearer token with `auth.getUser(token)`.
- Risk: abuse/cost exposure for AI calls in extract mode.
- File: `supabase/functions/capture-event/index.ts`.

4. `load-events` accepts external invocation and writes with service role.
- Function uses `SUPABASE_SERVICE_ROLE_KEY`.
- Workflow calls it with anon bearer, but function code does not strongly authenticate caller intent.
- Files: `supabase/functions/load-events/index.ts`, `.github/workflows/generate-calendar.yml`.

## Model Notes

- GitHub OAuth is the identity source; Supabase Auth session is the auth context used by RLS (`auth.uid()`).
- `LOCAL_ADMIN_USERS` in the app is UI-only feature gating, not a backend security control.

## Hardening Backlog

1. Restrict `events` insert policy to service role only.
2. Require auth (or server-side allowlist) for `capture-event` extract mode.
3. Add trusted-caller check for `load-events` (for example shared secret header) while preserving scheduled/workflow invocation.
4. Keep `my-picks` tokenized public feed behavior as-is.
