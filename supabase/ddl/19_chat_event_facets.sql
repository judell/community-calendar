-- Concierge retrieval facets
-- Canonical machine-generated facets per raw event plus a concierge-specific
-- deduplicated materialized view with aggregated facet arrays.

create table if not exists public.event_facets (
  event_id bigint primary key references public.events(id) on delete cascade,
  activity_tags text[] not null default '{}'::text[],
  participation_modes text[] not null default '{}'::text[],
  format_tags text[] not null default '{}'::text[],
  audience_tags text[] not null default '{}'::text[],
  cost_tags text[] not null default '{}'::text[],
  quality_score numeric,
  classified_by text,
  classified_at timestamptz not null default now()
);

create index if not exists event_facets_activity_tags_gin on public.event_facets using gin (activity_tags);
create index if not exists event_facets_participation_modes_gin on public.event_facets using gin (participation_modes);
create index if not exists event_facets_format_tags_gin on public.event_facets using gin (format_tags);
create index if not exists event_facets_audience_tags_gin on public.event_facets using gin (audience_tags);
create index if not exists event_facets_cost_tags_gin on public.event_facets using gin (cost_tags);

alter table public.event_facets enable row level security;

drop policy if exists "Event facets are publicly readable" on public.event_facets;
create policy "Event facets are publicly readable"
  on public.event_facets for select
  using (true);

grant select on public.event_facets to anon, authenticated, service_role;

drop view if exists public.deduplicated_chat_events;
drop materialized view if exists public.deduplicated_chat_events;

create materialized view public.deduplicated_chat_events as
with base_events as (
  select
    e.*,
    lower(trim(both from e.title)) as normalized_title
  from public.events e
  where e.source <> 'poster_capture'
),
grouped_events as (
  select
    min(id) as id,
    (array_agg(title order by id))[1] as title,
    start_time,
    (array_agg(end_time order by id) filter (where end_time is not null))[1] as end_time,
    (array_agg(url order by id) filter (where url is not null and url <> ''))[1] as url,
    (array_agg(location order by id) filter (where location is not null))[1] as location,
    (array_agg(description order by id) filter (where description is not null))[1] as description,
    string_agg(distinct source, ', ') as source,
    (array_agg(source_uid order by id))[1] as source_uid,
    min(created_at) as created_at,
    city,
    (array_agg(transcript order by id) filter (where transcript is not null))[1] as transcript,
    (array_agg(source_id order by id))[1] as source_id,
    (array_agg(cluster_id order by id) filter (where cluster_id is not null))[1] as cluster_id,
    (array_agg(source_urls order by id) filter (where source_urls is not null))[1] as source_urls,
    (array_agg(category order by id) filter (where category is not null))[1] as category,
    (array_agg(image_url order by id) filter (where image_url is not null))[1] as image_url,
    bool_or(all_day) as all_day,
    array_agg(id order by id) as merged_ids,
    normalized_title
  from base_events
  group by city, normalized_title, start_time
),
activity_facets as (
  select
    e.city,
    e.normalized_title,
    e.start_time,
    array_agg(distinct tag order by tag) filter (where tag is not null) as activity_tags
  from base_events e
  left join public.event_facets ef on ef.event_id = e.id
  left join lateral unnest(coalesce(ef.activity_tags, '{}'::text[])) tag on true
  group by e.city, e.normalized_title, e.start_time
),
participation_facets as (
  select
    e.city,
    e.normalized_title,
    e.start_time,
    array_agg(distinct tag order by tag) filter (where tag is not null) as participation_modes
  from base_events e
  left join public.event_facets ef on ef.event_id = e.id
  left join lateral unnest(coalesce(ef.participation_modes, '{}'::text[])) tag on true
  group by e.city, e.normalized_title, e.start_time
),
format_facets as (
  select
    e.city,
    e.normalized_title,
    e.start_time,
    array_agg(distinct tag order by tag) filter (where tag is not null) as format_tags
  from base_events e
  left join public.event_facets ef on ef.event_id = e.id
  left join lateral unnest(coalesce(ef.format_tags, '{}'::text[])) tag on true
  group by e.city, e.normalized_title, e.start_time
),
audience_facets as (
  select
    e.city,
    e.normalized_title,
    e.start_time,
    array_agg(distinct tag order by tag) filter (where tag is not null) as audience_tags
  from base_events e
  left join public.event_facets ef on ef.event_id = e.id
  left join lateral unnest(coalesce(ef.audience_tags, '{}'::text[])) tag on true
  group by e.city, e.normalized_title, e.start_time
),
cost_facets as (
  select
    e.city,
    e.normalized_title,
    e.start_time,
    array_agg(distinct tag order by tag) filter (where tag is not null) as cost_tags
  from base_events e
  left join public.event_facets ef on ef.event_id = e.id
  left join lateral unnest(coalesce(ef.cost_tags, '{}'::text[])) tag on true
  group by e.city, e.normalized_title, e.start_time
)
select
  g.id,
  g.title,
  g.start_time,
  g.end_time,
  g.url,
  g.location,
  g.description,
  g.source,
  g.source_uid,
  g.created_at,
  g.city,
  g.transcript,
  g.source_id,
  g.cluster_id,
  g.source_urls,
  g.category,
  canonical_event.ics_categories,
  g.image_url,
  g.all_day,
  g.merged_ids,
  coalesce(a.activity_tags, '{}'::text[]) as activity_tags,
  coalesce(p.participation_modes, '{}'::text[]) as participation_modes,
  coalesce(f.format_tags, '{}'::text[]) as format_tags,
  coalesce(u.audience_tags, '{}'::text[]) as audience_tags,
  coalesce(c.cost_tags, '{}'::text[]) as cost_tags
from grouped_events g
left join activity_facets a using (city, normalized_title, start_time)
left join participation_facets p using (city, normalized_title, start_time)
left join format_facets f using (city, normalized_title, start_time)
left join audience_facets u using (city, normalized_title, start_time)
left join cost_facets c using (city, normalized_title, start_time)
left join public.events canonical_event on canonical_event.id = g.id
order by g.start_time;

create unique index deduplicated_chat_events_id_idx on public.deduplicated_chat_events (id);
create index deduplicated_chat_events_city_idx on public.deduplicated_chat_events (city);
create index deduplicated_chat_events_start_time_idx on public.deduplicated_chat_events (start_time);
create index deduplicated_chat_events_activity_tags_gin on public.deduplicated_chat_events using gin (activity_tags);
create index deduplicated_chat_events_participation_modes_gin on public.deduplicated_chat_events using gin (participation_modes);
create index deduplicated_chat_events_format_tags_gin on public.deduplicated_chat_events using gin (format_tags);
create index deduplicated_chat_events_audience_tags_gin on public.deduplicated_chat_events using gin (audience_tags);
create index deduplicated_chat_events_cost_tags_gin on public.deduplicated_chat_events using gin (cost_tags);

grant select on public.deduplicated_chat_events to anon, authenticated, service_role;

create or replace function public.refresh_deduplicated_chat_events()
returns void
language plpgsql
security definer
set statement_timeout to '120s'
as $function$
begin
  refresh materialized view public.deduplicated_chat_events;
end;
$function$;

grant execute on function public.refresh_deduplicated_chat_events() to anon, authenticated, service_role;
