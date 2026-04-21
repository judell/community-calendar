# Chat Feature Handoff

## Status

There are currently two concierge backends in `community-calendar`:

- `chat-events`
  - the original facet / SQL path
  - file: `supabase/functions/chat-events/index.ts`
- `chat-events-rag`
  - the retrieval-first prototype
  - file: `supabase/functions/chat-events-rag/index.ts`

The XMLUI panel can switch between them in:

- `xmlui/components/ChatEventsPanel.xmlui`

The RAG path is the one to keep pushing. The facet / SQL path was useful for learning, but it is too heuristic-heavy for open-ended conversational event search.

## What Is Live

### Beta / auth / logging

- Bloomington-only beta access is enforced.
- Allowed users are checked via `chat_beta_users`.
- Both backends write durable logs to `chat_beta_logs`.
- The log table does not yet have an explicit `backend` column.
  - You can currently infer backend from `executed_sql`:
    - SQL path logs a `SELECT ... FROM public.deduplicated_chat_events ...`
    - RAG path logs `rpc hybrid_search_events(...)`

### UI

- The concierge panel is integrated into the main app.
- Main event display is hidden while the concierge is open.
- Results are rendered as event cards.
- Zero-result responses can include adjacent pivot suggestions.
- The `Current` / `RAG` switch is wired in `ChatEventsPanel.xmlui`.
  - A bug in the original button wiring was fixed by replacing `thisComponent.setBackend(...)` with direct inline state updates.
  - The panel now shows visible backend state text and inserts a one-line assistant message when switching.

### RAG substrate

These DB pieces are live:

- `public.chat_event_documents`
- `public.chat_event_document_content(...)`
- `public.refresh_chat_event_documents()`
- `public.hybrid_search_events(...)`

Related files:

- migration: `supabase/migrations/006_add_chat_event_documents.sql`
- DDL snapshot: `supabase/ddl/22_chat_event_documents.sql`
- refresh hook: `supabase/ddl/17_deduplicated_events.sql`

Vector support is enabled:

- `extensions.vector`
- noted in `supabase/ddl/01_extensions.sql`

### Embedding backfill

A backfill function exists:

- `supabase/functions/backfill-chat-event-embeddings/index.ts`

It was run for Bloomington and then paused because it overlapped with app traffic and a build/load path.

Current Bloomington state at end of session:

- total `chat_event_documents` rows: `6821`
- embedded: `4860`
- remaining: `1961`

So Bloomington RAG testing is meaningful now, but not complete.

## Important Performance Fix From Tonight

The app was timing out with `statement timeout`, including on:

- `https://judell.github.io/community-calendar/xmlui/index.html?city=toronto`

Root cause:

- a write-heavy embedding backfill was running
- a build/load path also appeared to be touching the DB
- the app’s main `deduplicated_events` read was already marginal

The main read was:

- `deduplicated_events`
- filtered by `city`
- ordered by `start_time`
- limited to `5000`

The DB was using only the `start_time` index and then filtering `city`, which made the read slow enough to trip REST timeouts under load.

Fix applied live:

- added `(city, start_time)` indexes on both deduplicated materialized views

Migration applied:

- `add_city_start_time_indexes_to_deduplicated_views`

Result:

- the tested Toronto read dropped from about `4.2s` in SQL to about `27ms`
- the public REST call returned `200` again

Backfill was also paused to remove DB pressure.

## Retrieval Findings

The RAG architecture is working, but the main weak link is retrieval query rewriting, not the embedding store itself.

Example failure investigated:

- user query: `cycling for kids/teens`
- target event: `Little Little 499` (`id = 3767296`)

Latest log showed:

- backend was `chat-events-rag`
- retrieval query was `cycling for kids teens`
- `Little Little 499` did not appear in the candidate set

Independent retrieval probing showed:

### Query: `cycling for kids/teens`

- `FTS`: no results
- `semantic`: target not present
- `hybrid`: target not present

### Query: `tricycle race for students`

- `FTS`: target rank 1
- `semantic`: target rank 1
- `hybrid`: target rank 1

Conclusion:

- embeddings are not the primary problem here
- the query rewrite is too literal / narrow
- the event is described as a `tricycle race` for `students`, not as `cycling for kids/teens`

So the next work belongs in `chat-events-rag/index.ts`, specifically in retrieval rewriting.

## Tools Added Tonight

### Retrieval probe

New script:

- `scripts/test_hybrid_retrieval.py`

Purpose:

- test retrieval without the reply model
- compare:
  - `fts`
  - `semantic`
  - `hybrid`
- optionally track a known target id

Example:

```bash
python3 scripts/test_hybrid_retrieval.py 'cycling for kids/teens' --city bloomington --mode all --show 10 --target-id 3767296
python3 scripts/test_hybrid_retrieval.py 'tricycle race for students' --city bloomington --mode all --show 8 --target-id 3767296
```

This is the main diagnostic tool to use before changing reply behavior.

## Current Architectural View

The likely end state is:

- deterministic bounds for:
  - city
  - time
- retrieval-first candidate generation
  - full-text + embeddings
- model does:
  - follow-up-aware retrieval query rewriting
  - answer generation over a small candidate slice

Do not keep deepening the facet / SQL path unless a specific stable concept clearly deserves structure.

RAG may also later inform which structured concepts are worth keeping, but the immediate priority is to see whether RAG is "good enough" with better rewriting.

## Known Gaps

- `chat_beta_logs` needs an explicit backend field.
- Bloomington embedding backfill is incomplete.
- Backfill should be resumed in a less intrusive way:
  - smaller batches
  - throttled
  - or off-hours
- Initial app load still asks for up to `5000` event rows.
  - The new index fixed the urgent timeout, but this is still heavier than ideal.
- RAG retrieval rewriting is too weak for some semantic paraphrases.
- Toronto has not been embedded, so RAG evaluation should stay focused on Bloomington.

## Recommended Next Steps

1. Add a `backend` column to `chat_beta_logs`.
   - values like `sql` and `rag`

2. Resume Bloomington embedding backfill carefully.
   - finish the remaining `1961` rows
   - avoid running it during heavy load or builds

3. Improve `chat-events-rag` retrieval rewriting.
   - especially for:
     - youth / student / family adjacency
     - instrument / genre reformulations
     - participatory vs attend-only language

4. Use `scripts/test_hybrid_retrieval.py` before touching reply logic.
   - first confirm whether a miss is:
     - rewrite failure
     - retrieval failure
     - or reply-model failure

5. Compare `Current` vs `RAG` on the same logged Bloomington beta queries.
   - treat real beta behavior as the evaluation set

6. Prefer multi-query retrieval over hand-authored rewrite heuristics.
   - Do not keep adding domain aliases like `cycling -> tricycle` or `classical guitar -> recital`.
   - The more scalable next step is to have the model emit a small set of retrieval variants by transformation role, not by domain vocabulary.
   - Example shape:

```json
{
  "queries": [
    { "kind": "verbatim", "text": "original user wording" },
    { "kind": "contextualized", "text": "resolved follow-up into standalone query" },
    { "kind": "paraphrase", "text": "same intent, different wording" },
    { "kind": "broadened", "text": "slightly wider version of the same ask" }
  ],
  "start_time": "...",
  "end_time": "..."
}
```

   - The backend should then:
     - run retrieval for each query variant
     - union and fuse the results
     - pass the fused top slice to the reply model
   - This keeps the system domain-independent:
     - the backend defines only transformation roles
     - the model supplies the wording
     - no manual event-domain synonym table is required

## Short Take

At the end of tonight:

- the timeout issue was fixed
- the app is responsive again
- the RAG toggle is wired locally
- Bloomington has enough embeddings for meaningful RAG testing
- retrieval probing shows the main issue is query rewriting, not the vector layer

That is the right place to resume next time.
