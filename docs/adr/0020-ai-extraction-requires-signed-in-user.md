# 0020. AI-Backed Extraction Requires a Signed-In User

Date: 2026-10-27

## Status

Accepted

## Context

`capture-event` mode=extract forwarded poster images and audio recordings to
Anthropic and OpenAI Whisper with the project's keys, and only mode=commit
checked a bearer token. The frontend ships the publishable key in
`xmlui/config.json`, and the function runs with `--no-verify-jwt`, so any caller
could spend both API accounts (GHSA-qq24-wmxg-hrgv).

Turning on the gateway's JWT check would not have closed the hole: the
publishable key is public and satisfies it (ADR 0019).

## Decision

**Require a valid Supabase user JWT on every `capture-event` request.** The
function reads `Authorization: Bearer <access_token>`, verifies it with
`auth.getUser()`, and returns 401 before reading the body or calling a paid API.
Any signed-in user is allowed, matching the UI gate and the commit path. The
gateway check stays off; the check lives in the function.

**Cap uploads at 10 MiB**, rejecting requests well over the cap with 413
before the multipart body is parsed and enforcing the exact cap on
`file.size`.

**Delete the legacy JSON base64 extract path**, which had no caller and was
equally unauthenticated.

## Consequences

- An expired session now fails the capture flow; the dialogs send the user
  token and surface the error instead of leaving the spinner running.
- Any signed-in user can still spend API credits. Per-user quotas are a
  separate decision.
- `supabase/functions/capture-event/auth_test.ts` asserts that a request
  without a token gets 401 with zero outbound fetches.

## Alternatives Considered

- **Turn `verify_jwt` back on.** Rejected: the publishable key passes it, so it
  adds no authorization.
- **A shared secret.** Rejected: the caller is the browser, which cannot hold
  one.
- **Admin-only extraction.** Rejected: poster and audio capture are available to
  every signed-in user.
