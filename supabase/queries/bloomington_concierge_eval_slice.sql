-- Stable Bloomington slice for fast concierge-classifier iteration.
-- Targets roughly 140 deduplicated rows across the categories that expose
-- the most retrieval ambiguity for concierge queries.

with base as (
  select
    id,
    title,
    start_time,
    end_time,
    location,
    description,
    source,
    category,
    city,
    merged_ids
  from public.deduplicated_chat_events
  where city = 'bloomington'
    and start_time >= now()
    and start_time < now() + interval '14 days'
),
music as (
  select 'Music / Concerts' as slice_bucket, *
  from base
  where category = 'Music / Concerts'
  order by start_time asc, id asc
  limit 30
),
community as (
  select 'Community / Social' as slice_bucket, *
  from base
  where category = 'Community / Social'
  order by start_time asc, id asc
  limit 25
),
education as (
  select 'Education / Workshops' as slice_bucket, *
  from base
  where category = 'Education / Workshops'
  order by start_time asc, id asc
  limit 25
),
outdoors as (
  select 'Nature / Outdoors / Recreation' as slice_bucket, *
  from base
  where category = 'Nature / Outdoors / Recreation'
  order by start_time asc, id asc
  limit 20
),
family as (
  select 'Family / Kids' as slice_bucket, *
  from base
  where category = 'Family / Kids'
  order by start_time asc, id asc
  limit 10
),
fitness as (
  select 'Sports / Fitness' as slice_bucket, *
  from base
  where category = 'Sports / Fitness'
  order by start_time asc, id asc
  limit 10
),
arts as (
  select 'Arts / Culture' as slice_bucket, *
  from base
  where category = 'Arts / Culture'
  order by start_time asc, id asc
  limit 10
),
books as (
  select 'Books / Literature / Poetry' as slice_bucket, *
  from base
  where category = 'Books / Literature / Poetry'
  order by start_time asc, id asc
  limit 10
)
select *
from music
union all
select *
from community
union all
select *
from education
union all
select *
from outdoors
union all
select *
from family
union all
select *
from fitness
union all
select *
from arts
union all
select *
from books
order by start_time asc, id asc;
