# Concierge Facets

## Problem

`chat-events` is currently asking the model to infer retrieval intent directly from raw event text plus one broad `category`.

That works for obvious topical queries like `hiking this weekend`, but it does not scale for queries like:

- `where can i find people to play music with?`
- `something outdoors tomorrow`
- `free talks downtown`
- `volunteer opportunities this week`

The failure mode is structural:

- `events.category` is too broad for concierge retrieval
- prompt tuning does not create stable searchable structure
- `event_enrichments` is curator-authored and sparse, so it is the wrong home for machine-generated search metadata

## Recommendation

Add a dedicated machine-generated facet table keyed to `events.id`, then surface those facets on the deduplicated query surface used by concierge.

Do not put these facets in `event_enrichments`.

Reasons:

- `event_enrichments` is per-curator, not canonical
- many events will never be manually enriched
- concierge needs one stable facet set per event
- machine-generated search metadata should be separable from curator edits

## Minimal Schema

This is the smallest schema that materially improves concierge retrieval.

```sql
create table event_facets (
  event_id bigint primary key references events(id) on delete cascade,
  activity_tags text[] not null default '{}',
  participation_modes text[] not null default '{}',
  format_tags text[] not null default '{}',
  audience_tags text[] not null default '{}',
  cost_tags text[] not null default '{}',
  quality_score numeric,
  classified_by text,
  classified_at timestamptz not null default now()
);
```

### Facet meanings

- `activity_tags`
  - What the event is about.
  - Examples: `music`, `jazz`, `hiking`, `nature`, `talks`, `poetry`, `volunteering`, `fitness`

- `participation_modes`
  - What the user does there.
  - Controlled values:
    - `attend`
    - `participate`
    - `learn`
    - `volunteer`
    - `socialize`
    - `compete`

- `format_tags`
  - Event shape.
  - Examples:
    - `concert`
    - `class`
    - `workshop`
    - `meetup`
    - `jam`
    - `rehearsal`
    - `ensemble`
    - `talk`
    - `screening`
    - `market`
    - `hike`

- `audience_tags`
  - Who it is for.
  - Examples:
    - `kids`
    - `families`
    - `students`
    - `adults`
    - `seniors`
    - `beginners`

- `cost_tags`
  - Pricing signal.
  - Controlled values:
    - `free`
    - `paid`
    - `donation`
    - `unknown`

## Why These Facets

This set is intentionally small.

It is enough to answer the kinds of concierge questions we are already seeing:

- `where can i find people to play music with?`
  - `activity_tags && {'music'}`
  - `participation_modes && {'participate','socialize'}`
  - `format_tags && {'jam','rehearsal','ensemble','meetup'}`

- `something outdoors tomorrow`
  - `activity_tags && {'outdoors','nature','hiking'}`

- `free talks this week`
  - `format_tags && {'talk'}`
  - `cost_tags && {'free'}`

- `family events after school`
  - `audience_tags && {'families','kids'}`

We do not need embeddings or a large ontology to get a major retrieval improvement.

## What Not To Add Yet

Do not start with:

- a normalized many-table ontology
- hundreds of tags
- per-city vocabularies
- a fully generic `jsonb` blob with unconstrained keys

Those options can come later if needed. For first-pass concierge retrieval, they will slow down iteration more than they help.

## Where This Fits In The Current Pipeline

Current data flow:

1. sources -> `events`
2. dedup -> `deduplicated_events`
3. concierge queries `deduplicated_events`

Recommended data flow:

1. sources -> `events`
2. facet classifier writes -> `event_facets`
3. dedup -> `deduplicated_events`
4. concierge queries a deduplicated surface that includes aggregated facets

## Query Surface

There are two reasonable ways to expose facets to concierge.

### Option A: extend `deduplicated_events`

Add aggregated facet columns to the materialized view:

```sql
activity_tags text[],
participation_modes text[],
format_tags text[],
audience_tags text[],
cost_tags text[]
```

Aggregate across merged rows with `array_agg(distinct ...)`.

This keeps concierge querying a single object.

### Option B: create `deduplicated_chat_events`

Leave `deduplicated_events` alone and create a second materialized view specifically for concierge retrieval.

This is cleaner if we want to keep the app's general event listing schema stable.

My recommendation: start with `deduplicated_chat_events`.

Reason:

- less risk to existing XMLUI list/card queries
- concierge can evolve independently
- the SQL executor can be tightened to one concierge-specific surface

## Classifier Contract

The model should stop generating SQL directly from raw user text.

Instead:

1. classify events offline into facets
2. at query time, have the model emit structured user intent
3. let backend code map intent -> SQL

### Query-time intent shape

```json
{
  "activity_tags": ["music"],
  "participation_modes": ["participate", "socialize"],
  "format_tags": ["jam", "rehearsal", "ensemble", "meetup"],
  "audience_tags": [],
  "cost_tags": [],
  "time_range": {
    "start": "2026-04-20T00:00:00Z",
    "end": "2026-05-04T00:00:00Z"
  }
}
```

That is much easier to validate and much more stable than arbitrary SQL generation.

## Example Query

For `where can i find people to play music with?`

```sql
select
  id, title, start_time, end_time, url, location, description, source,
  source_urls, category, image_url, all_day, city, merged_ids
from public.deduplicated_chat_events
where city = 'bloomington'
  and start_time >= '2026-04-20T00:00:00Z'::timestamptz
  and start_time < '2026-05-04T00:00:00Z'::timestamptz
  and activity_tags && array['music']
  and participation_modes && array['participate','socialize']
  and format_tags && array['jam','rehearsal','ensemble','meetup']
order by start_time asc
limit 20;
```

## Rollout Plan

### Phase 1

- add `event_facets`
- classify a small upcoming slice for one city
- build `deduplicated_chat_events`
- switch concierge SQL executor to that surface

### Phase 2

- replace free-form SQL planning with structured intent output
- keep deterministic backend SQL generation

### Phase 3

- add reranking or semantic fallback only when structured retrieval returns weak candidates

## First Migration Set

The first DB change should be:

1. create `event_facets`
2. add indexes for array overlap queries
3. create `deduplicated_chat_events`

Example indexes:

```sql
create index event_facets_activity_tags_gin on event_facets using gin (activity_tags);
create index event_facets_participation_modes_gin on event_facets using gin (participation_modes);
create index event_facets_format_tags_gin on event_facets using gin (format_tags);
create index event_facets_audience_tags_gin on event_facets using gin (audience_tags);
create index event_facets_cost_tags_gin on event_facets using gin (cost_tags);
```

## Recommendation Summary

Minimal scalable move:

- new canonical `event_facets` table
- machine-generated, not curator-authored
- five small facet families
- concierge queries a dedicated deduplicated facet surface
- model emits intent, backend writes SQL

That gets us out of the current dead end where every new concierge phrase becomes a prompt patch.
