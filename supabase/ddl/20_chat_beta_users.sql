create table if not exists public.chat_beta_users (
  user_id uuid not null references auth.users(id) on delete cascade,
  city text not null,
  note text,
  created_at timestamptz not null default now(),
  primary key (user_id, city)
);

alter table public.chat_beta_users enable row level security;

drop policy if exists "Users can view own chat beta access" on public.chat_beta_users;
create policy "Users can view own chat beta access"
  on public.chat_beta_users for select
  to authenticated
  using (auth.uid() = user_id);

drop policy if exists "Service role can manage chat beta access" on public.chat_beta_users;
create policy "Service role can manage chat beta access"
  on public.chat_beta_users for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

grant select on public.chat_beta_users to authenticated, service_role;
