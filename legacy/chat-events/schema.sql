-- Chat events experiment: schema as captured from production on 2026-10-25,
-- immediately before supabase/migrations/20261025120000_retire_chat_events.sql
-- dropped it. Archive only; not applied by anything. Grants and RLS policies
-- are not included.

-- ---------------------------------------------------------------- tables

CREATE TABLE public.event_facets (
  event_id bigint NOT NULL,
  activity_tags text[] NOT NULL DEFAULT '{}'::text[],
  participation_modes text[] NOT NULL DEFAULT '{}'::text[],
  format_tags text[] NOT NULL DEFAULT '{}'::text[],
  audience_tags text[] NOT NULL DEFAULT '{}'::text[],
  cost_tags text[] NOT NULL DEFAULT '{}'::text[],
  quality_score numeric,
  classified_by text,
  classified_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT event_facets_pkey PRIMARY KEY (event_id),
  CONSTRAINT event_facets_event_id_fkey FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);
CREATE INDEX event_facets_activity_tags_gin ON public.event_facets USING gin (activity_tags);
CREATE INDEX event_facets_participation_modes_gin ON public.event_facets USING gin (participation_modes);
CREATE INDEX event_facets_format_tags_gin ON public.event_facets USING gin (format_tags);
CREATE INDEX event_facets_audience_tags_gin ON public.event_facets USING gin (audience_tags);
CREATE INDEX event_facets_cost_tags_gin ON public.event_facets USING gin (cost_tags);

CREATE TABLE public.chat_event_documents (
  event_id bigint NOT NULL,
  city text NOT NULL,
  start_time timestamp with time zone NOT NULL,
  end_time timestamp with time zone,
  category text,
  title text NOT NULL,
  location text,
  description text,
  source text,
  source_urls jsonb,
  ics_categories text[],
  content text NOT NULL,
  fts tsvector DEFAULT to_tsvector('english'::regconfig, content),
  embedding vector(512),
  updated_at timestamp with time zone NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX chat_event_documents_pkey ON public.chat_event_documents USING btree (event_id);
CREATE INDEX chat_event_documents_city_start_time_idx ON public.chat_event_documents USING btree (city, start_time);
CREATE INDEX chat_event_documents_embedding_hnsw ON public.chat_event_documents USING hnsw (embedding vector_ip_ops);
CREATE INDEX chat_event_documents_fts_gin ON public.chat_event_documents USING gin (fts);

-- user_id references auth.users
CREATE TABLE public.chat_beta_users (
  user_id uuid NOT NULL,
  city text NOT NULL,
  note text,
  created_at timestamp with time zone NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX chat_beta_users_pkey ON public.chat_beta_users USING btree (user_id, city);

-- user_id references auth.users
CREATE TABLE public.chat_beta_logs (
  id bigint NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  user_id uuid NOT NULL,
  city text NOT NULL,
  latest_user_text text NOT NULL,
  request_messages jsonb NOT NULL DEFAULT '[]'::jsonb,
  intent_plan jsonb,
  planner_model text NOT NULL,
  reply_model text NOT NULL,
  planner_raw text,
  planner_error text,
  executed_sql text NOT NULL,
  query_error text,
  used_fallback boolean NOT NULL DEFAULT false,
  planner_fallback_used boolean NOT NULL DEFAULT false,
  query_fallback_used boolean NOT NULL DEFAULT false,
  candidate_ids bigint[] NOT NULL DEFAULT '{}'::bigint[],
  recommended_ids bigint[] NOT NULL DEFAULT '{}'::bigint[],
  reply_text text NOT NULL,
  reply_raw text,
  reply_error text
);
CREATE UNIQUE INDEX chat_beta_logs_pkey ON public.chat_beta_logs USING btree (id);
CREATE INDEX chat_beta_logs_city_created_at_idx ON public.chat_beta_logs USING btree (city, created_at DESC);
CREATE INDEX chat_beta_logs_user_created_at_idx ON public.chat_beta_logs USING btree (user_id, created_at DESC);

-- ---------------------------------------------------------------- matview

CREATE MATERIALIZED VIEW public.deduplicated_chat_events AS
 WITH base_events AS (
         SELECT e.id,
            e.title,
            e.start_time,
            e.end_time,
            e.location,
            e.description,
            e.url,
            e.source,
            e.source_uid,
            e.created_at,
            e.city,
            e.transcript,
            e.source_id,
            e.cluster_id,
            e.source_urls,
            e.category,
            e.ics_categories,
            e.image_url,
            e.all_day,
            lower(TRIM(BOTH FROM e.title)) AS normalized_title
           FROM events e
          WHERE e.source <> 'poster_capture'::text
        ), grouped_events AS (
         SELECT min(base_events.id) AS id,
            (array_agg(base_events.title ORDER BY base_events.id))[1] AS title,
            base_events.start_time,
            (array_agg(base_events.end_time ORDER BY base_events.id) FILTER (WHERE base_events.end_time IS NOT NULL))[1] AS end_time,
            (array_agg(base_events.url ORDER BY base_events.id) FILTER (WHERE base_events.url IS NOT NULL AND base_events.url <> ''::text))[1] AS url,
            (array_agg(base_events.location ORDER BY base_events.id) FILTER (WHERE base_events.location IS NOT NULL))[1] AS location,
            (array_agg(base_events.description ORDER BY base_events.id) FILTER (WHERE base_events.description IS NOT NULL))[1] AS description,
            string_agg(DISTINCT base_events.source, ', '::text) AS source,
            (array_agg(base_events.source_uid ORDER BY base_events.id))[1] AS source_uid,
            min(base_events.created_at) AS created_at,
            base_events.city,
            (array_agg(base_events.transcript ORDER BY base_events.id) FILTER (WHERE base_events.transcript IS NOT NULL))[1] AS transcript,
            (array_agg(base_events.source_id ORDER BY base_events.id))[1] AS source_id,
            (array_agg(base_events.cluster_id ORDER BY base_events.id) FILTER (WHERE base_events.cluster_id IS NOT NULL))[1] AS cluster_id,
            (array_agg(base_events.source_urls ORDER BY base_events.id) FILTER (WHERE base_events.source_urls IS NOT NULL))[1] AS source_urls,
            (array_agg(base_events.category ORDER BY base_events.id) FILTER (WHERE base_events.category IS NOT NULL))[1] AS category,
            (array_agg(base_events.image_url ORDER BY base_events.id) FILTER (WHERE base_events.image_url IS NOT NULL))[1] AS image_url,
            bool_or(base_events.all_day) AS all_day,
            array_agg(base_events.id ORDER BY base_events.id) AS merged_ids,
            base_events.normalized_title
           FROM base_events
          GROUP BY base_events.city, base_events.normalized_title, base_events.start_time
        ), activity_facets AS (
         SELECT e.city,
            e.normalized_title,
            e.start_time,
            array_agg(DISTINCT tag.tag ORDER BY tag.tag) FILTER (WHERE tag.tag IS NOT NULL) AS activity_tags
           FROM base_events e
             LEFT JOIN event_facets ef ON ef.event_id = e.id
             LEFT JOIN LATERAL unnest(COALESCE(ef.activity_tags, '{}'::text[])) tag(tag) ON true
          GROUP BY e.city, e.normalized_title, e.start_time
        ), participation_facets AS (
         SELECT e.city,
            e.normalized_title,
            e.start_time,
            array_agg(DISTINCT tag.tag ORDER BY tag.tag) FILTER (WHERE tag.tag IS NOT NULL) AS participation_modes
           FROM base_events e
             LEFT JOIN event_facets ef ON ef.event_id = e.id
             LEFT JOIN LATERAL unnest(COALESCE(ef.participation_modes, '{}'::text[])) tag(tag) ON true
          GROUP BY e.city, e.normalized_title, e.start_time
        ), format_facets AS (
         SELECT e.city,
            e.normalized_title,
            e.start_time,
            array_agg(DISTINCT tag.tag ORDER BY tag.tag) FILTER (WHERE tag.tag IS NOT NULL) AS format_tags
           FROM base_events e
             LEFT JOIN event_facets ef ON ef.event_id = e.id
             LEFT JOIN LATERAL unnest(COALESCE(ef.format_tags, '{}'::text[])) tag(tag) ON true
          GROUP BY e.city, e.normalized_title, e.start_time
        ), audience_facets AS (
         SELECT e.city,
            e.normalized_title,
            e.start_time,
            array_agg(DISTINCT tag.tag ORDER BY tag.tag) FILTER (WHERE tag.tag IS NOT NULL) AS audience_tags
           FROM base_events e
             LEFT JOIN event_facets ef ON ef.event_id = e.id
             LEFT JOIN LATERAL unnest(COALESCE(ef.audience_tags, '{}'::text[])) tag(tag) ON true
          GROUP BY e.city, e.normalized_title, e.start_time
        ), cost_facets AS (
         SELECT e.city,
            e.normalized_title,
            e.start_time,
            array_agg(DISTINCT tag.tag ORDER BY tag.tag) FILTER (WHERE tag.tag IS NOT NULL) AS cost_tags
           FROM base_events e
             LEFT JOIN event_facets ef ON ef.event_id = e.id
             LEFT JOIN LATERAL unnest(COALESCE(ef.cost_tags, '{}'::text[])) tag(tag) ON true
          GROUP BY e.city, e.normalized_title, e.start_time
        )
 SELECT g.id,
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
    COALESCE(a.activity_tags, '{}'::text[]) AS activity_tags,
    COALESCE(p.participation_modes, '{}'::text[]) AS participation_modes,
    COALESCE(f.format_tags, '{}'::text[]) AS format_tags,
    COALESCE(u.audience_tags, '{}'::text[]) AS audience_tags,
    COALESCE(c.cost_tags, '{}'::text[]) AS cost_tags
   FROM grouped_events g
     LEFT JOIN activity_facets a USING (city, normalized_title, start_time)
     LEFT JOIN participation_facets p USING (city, normalized_title, start_time)
     LEFT JOIN format_facets f USING (city, normalized_title, start_time)
     LEFT JOIN audience_facets u USING (city, normalized_title, start_time)
     LEFT JOIN cost_facets c USING (city, normalized_title, start_time)
     LEFT JOIN events canonical_event ON canonical_event.id = g.id
  ORDER BY g.start_time;
CREATE UNIQUE INDEX deduplicated_chat_events_id_idx ON public.deduplicated_chat_events USING btree (id);
CREATE INDEX deduplicated_chat_events_city_idx ON public.deduplicated_chat_events USING btree (city);
CREATE INDEX deduplicated_chat_events_city_start_time_idx ON public.deduplicated_chat_events USING btree (city, start_time);
CREATE INDEX deduplicated_chat_events_start_time_idx ON public.deduplicated_chat_events USING btree (start_time);
CREATE INDEX deduplicated_chat_events_activity_tags_gin ON public.deduplicated_chat_events USING gin (activity_tags);
CREATE INDEX deduplicated_chat_events_audience_tags_gin ON public.deduplicated_chat_events USING gin (audience_tags);
CREATE INDEX deduplicated_chat_events_cost_tags_gin ON public.deduplicated_chat_events USING gin (cost_tags);
CREATE INDEX deduplicated_chat_events_format_tags_gin ON public.deduplicated_chat_events USING gin (format_tags);
CREATE INDEX deduplicated_chat_events_participation_modes_gin ON public.deduplicated_chat_events USING gin (participation_modes);

-- ---------------------------------------------------------------- functions

CREATE OR REPLACE FUNCTION public.chat_event_document_content(p_title text, p_category text, p_location text, p_description text, p_source text, p_city text, p_ics_categories text[])
 RETURNS text
 LANGUAGE sql
 IMMUTABLE
AS $function$
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

CREATE OR REPLACE FUNCTION public.hybrid_search_events(query_text text, query_embedding vector, filter_city text, window_start timestamp with time zone, window_end timestamp with time zone, match_count integer DEFAULT 30, full_text_weight double precision DEFAULT 1, semantic_weight double precision DEFAULT 1, rrf_k integer DEFAULT 50)
 RETURNS TABLE(id bigint, title text, start_time timestamp with time zone, end_time timestamp with time zone, url text, location text, description text, source text, source_urls jsonb, category text, image_url text, all_day boolean, city text, merged_ids bigint[], rrf_score double precision, full_text_rank bigint, semantic_rank bigint)
 LANGUAGE sql
 STABLE
AS $function$
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

CREATE OR REPLACE FUNCTION public.refresh_chat_event_documents()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET statement_timeout TO '120s'
AS $function$
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

CREATE OR REPLACE FUNCTION public.refresh_deduplicated_chat_events()
 RETURNS void
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET statement_timeout TO '120s'
AS $function$
begin
  refresh materialized view public.deduplicated_chat_events;
end;
$function$;

CREATE OR REPLACE FUNCTION public.run_chat_events_sql(query text)
 RETURNS TABLE(id bigint, title text, start_time timestamp with time zone, end_time timestamp with time zone, url text, location text, description text, source text, source_urls jsonb, category text, image_url text, all_day boolean, city text, merged_ids bigint[])
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  normalized text;
  limit_match text[];
  limit_value integer;
begin
  normalized := regexp_replace(trim(query), '\s+', ' ', 'g');

  if normalized is null or normalized = '' then
    raise exception 'Query is required';
  end if;

  if normalized ~ ';|--|/\*|\*/' then
    raise exception 'Comments and statement separators are not allowed';
  end if;

  if normalized !~* '^select id, title, start_time, end_time, url, location, description, source, source_urls, category, image_url, all_day, city, merged_ids from public\.(deduplicated_events|deduplicated_chat_events) where .+ order by start_time asc limit [0-9]+$' then
    raise exception 'Query must match the allowed chat-events shape';
  end if;

  if normalized !~* 'city\s*=\s*''' then
    raise exception 'Query must include a city filter';
  end if;

  if normalized !~* 'start_time\s*>=\s*''' or normalized !~* 'start_time\s*<\s*''' then
    raise exception 'Query must include both lower and upper start_time bounds';
  end if;

  if normalized ~* '\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|refresh|execute|perform|do|join|union|intersect|except|with)\b' then
    raise exception 'Query contains forbidden SQL keywords';
  end if;

  limit_match := regexp_match(normalized, '(?i) limit ([0-9]+)$');
  if limit_match is null then
    raise exception 'Query must end with LIMIT';
  end if;

  limit_value := limit_match[1]::integer;
  if limit_value < 1 or limit_value > 50 then
    raise exception 'LIMIT must be between 1 and 50';
  end if;

  return query execute normalized;
end;
$function$;
