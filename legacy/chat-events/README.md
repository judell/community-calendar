# Chat events experiment (retired 2026-10-25)

An invite-only "events concierge" beta for Bloomington, spring 2026. A
signed-in beta user asked a question in natural language; Claude Haiku
planned a structured query, the backend ran it against a faceted copy of
the deduplicated events, and Haiku wrote a one-sentence reply plus up to
four recommended events. Two retrieval strategies were tried:

- `chat-events/`: LLM-planned SQL, executed through the
  `run_chat_events_sql` RPC (allowlist-shaped SELECT over
  `deduplicated_chat_events`).
- `chat-events-rag/`: hybrid full-text + embedding search via the
  `hybrid_search_events` RPC over `chat_event_documents` (OpenAI
  `text-embedding-3-small`, 512 dims).
- `backfill-chat-event-embeddings/`: filled `chat_event_documents.embedding`.

None of this was ever wired into the app or the build; the source lived only
as deployed edge functions. The last beta log entry is from 2026-04-21.

## Why retired

Unused, and still publicly reachable:

- `backfill-chat-event-embeddings` had no auth, so anyone could make it
  call OpenAI with the project key.
- Five SQL functions were executable with the publishable key. Three of
  them were SECURITY DEFINER: `run_chat_events_sql`,
  `refresh_chat_event_documents` and `refresh_deduplicated_chat_events`.

The two chat functions themselves required a signed-in user listed in
`chat_beta_users` (city `bloomington`) before calling Anthropic.

## What's here

- `<function>/index.ts`: edge function source exactly as deployed
  (`chat-events` v25, `chat-events-rag` v2, `backfill-chat-event-embeddings` v2).
- `schema.sql`: definitions of every database object the experiment used,
  captured from production before the drop. That's tables, the matview,
  functions and indexes; grants and RLS policies aren't included.

Not archived: row data. `chat_beta_users` (4 rows) and `chat_beta_logs`
(12 rows, which hold testers' prompts) contain personal data. The derived
tables `chat_event_documents` / `deduplicated_chat_events` (~42k rows) can
be regenerated from `events`. `event_facets` was empty.

Dropped by `supabase/migrations/20261025120000_retire_chat_events.sql`.
