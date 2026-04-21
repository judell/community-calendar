create extension if not exists vector with schema extensions;

create or replace function public.chat_event_document_content(
  p_title text,
  p_category text,
  p_location text,
  p_description text,
  p_source text,
  p_city text,
  p_ics_categories text[]
)
returns text
language sql
immutable
as $function$
  select trim(
    both E'\n' from concat_ws(
      E'\n',
      case when coalesce(p_title, '') <> '' then 'title: ' || p_title end,
      case when coalesce(p_category, '') <> '' then 'category: ' || p_category end,
      case when coalesce(p_location, '') <> '' then 'location: ' || p_location end,
      case when coalesce(array_length(p_ics_categories, 1), 0) > 0 then 'ics categories: ' || array_to_string(p_ics_categories, ', ') end,
      case when coalesce(p_source, '') <> '' then 'source: ' || p_source end,
      case when coalesce(p_city, '') <> '' then 'city: ' || p_city end,
      case when coalesce(p_description, '') <> '' then 'description: ' || p_description end
    )
  );
$function$;

create table if not exists public.chat_event_documents (
  event_id bigint primary key,
  city text not null,
  start_time timestamptz not null,
  end_time timestamptz,
  category text,
  title text not null,
  location text,
  description text,
  source text,
  source_urls jsonb,
  ics_categories text[],
  content text not null,
  fts tsvector generated always as (to_tsvector('english', content)) stored,
  embedding extensions.vector(512),
  updated_at timestamptz not null default now()
);

create index if not exists chat_event_documents_city_start_time_idx
  on public.chat_event_documents (city, start_time);

create index if not exists chat_event_documents_fts_gin
  on public.chat_event_documents using gin (fts);

create index if not exists chat_event_documents_embedding_hnsw
  on public.chat_event_documents using hnsw (embedding vector_ip_ops);

alter table public.chat_event_documents enable row level security;

drop policy if exists "Chat event documents are publicly readable" on public.chat_event_documents;
create policy "Chat event documents are publicly readable"
  on public.chat_event_documents for select
  using (true);

grant select on public.chat_event_documents to anon, authenticated, service_role;

create or replace function public.refresh_chat_event_documents()
returns void
language plpgsql
security definer
set statement_timeout to '120s'
as $function$
begin
  insert into public.chat_event_documents (
    event_id,
    city,
    start_time,
    end_time,
    category,
    title,
    location,
    description,
    source,
    source_urls,
    ics_categories,
    content,
    updated_at
  )
  select
    d.id,
    d.city,
    d.start_time,
    d.end_time,
    d.category,
    d.title,
    d.location,
    d.description,
    d.source,
    d.source_urls,
    d.ics_categories,
    public.chat_event_document_content(
      d.title,
      d.category,
      d.location,
      d.description,
      d.source,
      d.city,
      d.ics_categories
    ),
    now()
  from public.deduplicated_chat_events d
  on conflict (event_id) do update
  set
    city = excluded.city,
    start_time = excluded.start_time,
    end_time = excluded.end_time,
    category = excluded.category,
    title = excluded.title,
    location = excluded.location,
    description = excluded.description,
    source = excluded.source,
    source_urls = excluded.source_urls,
    ics_categories = excluded.ics_categories,
    content = excluded.content,
    updated_at = now();

  delete from public.chat_event_documents ced
  where not exists (
    select 1
    from public.deduplicated_chat_events d
    where d.id = ced.event_id
  );
end;
$function$;

grant execute on function public.refresh_chat_event_documents() to anon, authenticated, service_role;

create or replace function public.hybrid_search_events(
  query_text text,
  query_embedding extensions.vector(512),
  filter_city text,
  window_start timestamptz,
  window_end timestamptz,
  match_count int default 30,
  full_text_weight float default 1,
  semantic_weight float default 1,
  rrf_k int default 50
)
returns table (
  id bigint,
  title text,
  start_time timestamptz,
  end_time timestamptz,
  url text,
  location text,
  description text,
  source text,
  source_urls jsonb,
  category text,
  image_url text,
  all_day boolean,
  city text,
  merged_ids bigint[],
  rrf_score double precision,
  full_text_rank bigint,
  semantic_rank bigint
)
language sql
stable
as $function$
with full_text as (
  select
    ced.event_id,
    row_number() over (
      order by ts_rank_cd(ced.fts, websearch_to_tsquery('english', query_text)) desc, ced.start_time asc
    ) as rank_ix
  from public.chat_event_documents ced
  where
    nullif(trim(query_text), '') is not null
    and ced.city = filter_city
    and ced.start_time >= window_start
    and ced.start_time < window_end
    and ced.fts @@ websearch_to_tsquery('english', query_text)
  order by rank_ix
  limit greatest(least(match_count, 50) * 2, 10)
),
semantic as (
  select
    ced.event_id,
    row_number() over (
      order by ced.embedding <#> query_embedding, ced.start_time asc
    ) as rank_ix
  from public.chat_event_documents ced
  where
    query_embedding is not null
    and ced.embedding is not null
    and ced.city = filter_city
    and ced.start_time >= window_start
    and ced.start_time < window_end
  order by rank_ix
  limit greatest(least(match_count, 50) * 2, 10)
)
select
  d.id,
  d.title,
  d.start_time,
  d.end_time,
  d.url,
  d.location,
  d.description,
  d.source,
  d.source_urls,
  d.category,
  d.image_url,
  d.all_day,
  d.city,
  d.merged_ids,
  (
    coalesce(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
    coalesce(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight
  )::double precision as rrf_score,
  full_text.rank_ix as full_text_rank,
  semantic.rank_ix as semantic_rank
from full_text
full outer join semantic
  on full_text.event_id = semantic.event_id
join public.deduplicated_chat_events d
  on d.id = coalesce(full_text.event_id, semantic.event_id)
order by rrf_score desc, d.start_time asc
limit least(match_count, 50);
$function$;

grant execute on function public.hybrid_search_events(
  text,
  extensions.vector(512),
  text,
  timestamptz,
  timestamptz,
  int,
  float,
  float,
  int
) to anon, authenticated, service_role;

create or replace function public.refresh_deduplicated_events()
returns void
language plpgsql
security definer
set statement_timeout to '120s'
as $function$
begin
  refresh materialized view public.deduplicated_events;
  refresh materialized view public.deduplicated_chat_events;
  perform public.refresh_chat_event_documents();
end;
$function$;

grant execute on function public.refresh_deduplicated_events() to anon, authenticated, service_role;

select public.refresh_chat_event_documents();
