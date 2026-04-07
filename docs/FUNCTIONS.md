# Postgres Functions vs Edge Functions

This project uses both Postgres functions (PL/pgSQL or SQL, running inside the database) and Supabase Edge Functions (Deno/TypeScript, running in a V8 isolate outside the database). They serve complementary roles.

## Postgres Functions in This Project

- `get_my_github_username()` — SECURITY DEFINER, resolves current user's GitHub username from auth.users
- `get_my_google_email()` — SECURITY DEFINER, resolves current user's Google email from auth.users
- `get_curator_name(uuid)` — SECURITY DEFINER, resolves a curator's GitHub username by user ID
- `apply_category_override()` — trigger function, stores original category then propagates override to events table
- `get_source_counts(target_city)` — returns source names + event counts by querying events table directly (replaces cached `source_names` table)
- `remove_feed(feed_id)` — SECURITY DEFINER, deletes a feed row (used by Manage Feeds dialog to avoid CORS issues with PATCH)
- `refresh_source_names(target_city)` — legacy, refreshes the `source_names` cache table

## Edge Functions in This Project

- `load-events` — accepts direct POST from CI or fetches from GitHub (fallback); upserts events into Supabase
- `capture-event` — calls Claude API to extract event data from images or audio; supports Whisper transcription for audio
- `my-picks` — generates ICS/JSON feed of a user's bookmarked events (token-based auth)
- `validate-feed` — validates an ICS feed URL, returns preview of future events, detects RRULE recurrence

## When to Use Which

| Use Postgres functions when... | Use Edge Functions when... |
|---|---|
| The work is purely data-to-data inside the DB | You need to call external APIs or services |
| You need transactional atomicity (triggers, multi-table writes) | You need HTTP request/response control (headers, content types, streaming) |
| You need to bridge security boundaries (SECURITY DEFINER) | You need runtime dependencies (npm packages, Deno APIs) |
| Performance matters — no network hop | The logic is complex enough to want TypeScript over PL/pgSQL |

Postgres functions are small, security-focused plumbing — they exist because the database needs to answer a question about its own data atomically and securely. Edge Functions are the app's "backend" — they orchestrate external I/O and return shaped responses.

## SECURITY DEFINER Explained

By default, Postgres functions run with the permissions of the **caller** (SECURITY INVOKER). A function marked `SECURITY DEFINER` runs with the permissions of the **function owner** (typically `postgres`, the superuser).

This is the Postgres equivalent of a Unix setuid binary: it lets unprivileged callers perform a specific privileged operation through a controlled interface.

### Why we use it

RLS prevents the `anon` and `authenticated` roles from reading `auth.users` directly — and it should. But sometimes we need data from `auth.users` (like a GitHub username) in a view or RLS policy. A SECURITY DEFINER function provides a narrow, read-only window into that data:

```sql
CREATE OR REPLACE FUNCTION public.get_curator_name(curator_uuid uuid)
RETURNS text
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = ''
AS $$
  SELECT raw_user_meta_data->>'user_name'
  FROM auth.users
  WHERE id = curator_uuid;
$$;
```

The caller can get a username for a given UUID, but cannot query auth.users arbitrarily.

### Required safety measures

SECURITY DEFINER functions must include `SET search_path = ''` to prevent search-path hijacking (where an attacker creates a function in a schema that shadows a system function). The Supabase linter flags functions that omit this.

### The antipattern: SECURITY DEFINER on views

Before March 2026, this project had two views (`distinct_cities`, `category_overrides_view`) created with SECURITY DEFINER. This meant the views ran as their owner (postgres), bypassing RLS for all querying users. Worse, `category_overrides_view` joined `auth.users` directly, exposing user data to the `anon` role.

The fix: recreate views with `security_invoker = true` (so they respect the caller's permissions) and move the privileged `auth.users` access into a SECURITY DEFINER **function** that returns only the specific field needed.

**Rule of thumb:** SECURITY DEFINER belongs on functions (narrow, parameterized, auditable), not on views (broad, exposes full result sets).
