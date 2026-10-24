# 0018. Edge Function Writes Require a Shared Secret, Not JWT Verification

Date: 2026-10-24

## Status

Accepted

## Context

`load-events` upserts events with the service-role key and then calls
`delete_stale_events`. It was deployed with `--no-verify-jwt`, so the gateway
checked nothing, and the function checked nothing either. The publishable key
used by the frontend is committed in `xmlui/config.json`, so any visitor could
POST `{city, events, ran_sources}` and control which rows were written and
which were swept (GHSA-qmc5-6cfg-38p7).

Turning JWT verification back on would not have closed the hole: the anon and
publishable keys are public by design, and both satisfy a JWT check. Supabase's
`verify_jwt` answers "is this a token this project issued?", not "is this an
authorized caller?".

Two paths also bypassed the function entirely: the `events` INSERT policy
applied to PUBLIC with `WITH CHECK (true)`, and `delete_stale_events` was
`SECURITY DEFINER` with the default `PUBLIC` EXECUTE grant.

## Decision

**Gate `load-events` on a shared secret only CI holds.** The function requires
an `x-load-events-secret` header matching the `LOAD_EVENTS_SECRET` project
secret, and fails closed (500, zero writes) when that secret is unset. The
GitHub Actions upload step reads the same value from the `LOAD_EVENTS_SECRET`
Actions secret.

**Close the bypasses in the database.** The `events` INSERT policy is scoped
`TO service_role`, and EXECUTE on `delete_stale_events` is revoked from
`PUBLIC`, `anon`, and `authenticated`.

The legacy fetch-from-GitHub mode was deleted with the same change: it existed
only for the pg_cron job that posted `{}`, and it fetched from the upstream
repository rather than this fork.

## Consequences

- Rotating the secret means updating two values (Supabase project secret,
  GitHub Actions secret). No redeploy is needed.
- A redeploy that loses the project secret fails loudly with 500 rather than
  silently reopening anonymous writes. That is intentional.
- `refresh_source_names` and `refresh_deduplicated_events` keep their anonymous
  EXECUTE grant: the workflow calls them with the anon key.
- A shared secret does not identify *which* caller wrote; both workflows share
  one value. Per-caller identity is unnecessary while CI is the only writer.

## Alternatives Considered

- **Turn `verify_jwt` back on.** Rejected: the anon key is public, so it
  passes, and the request shape does not change.
- **A signed JWT issued to CI.** Rejected as more machinery for one caller; it
  needs a signing key, an expiry policy, and rotation tooling.
- **Keep the secret in the database and check it with an RPC.** Rejected: the
  check then costs a round trip and moves the secret into a table readable by
  anyone with service access, with no security gain.
- **Leave the legacy GitHub-fetch mode and gate it too.** Rejected: nothing in
  this repository used it, and the fork does not build from the upstream repo.
