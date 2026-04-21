create or replace function public.run_chat_events_sql(query text)
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
  merged_ids bigint[]
)
language plpgsql
security definer
set search_path = ''
as $function$
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

  if normalized !~* '^select id, title, start_time, end_time, url, location, description, source, source_urls, category, image_url, all_day, city, merged_ids from public\.deduplicated_events where .+ order by start_time asc limit [0-9]+$' then
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

grant execute on function public.run_chat_events_sql(text) to anon, authenticated, service_role;
