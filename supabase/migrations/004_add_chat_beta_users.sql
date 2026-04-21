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

insert into public.chat_beta_users (user_id, city, note)
values
  ('fff28b3c-159a-449b-9084-2760f3adbcf9', 'bloomington', 'Joyce Searls beta access'),
  ('e13d6163-0b86-4875-bf3c-9d1c277a4997', 'bloomington', 'Dave Askins beta access (GitHub)'),
  ('db6a0bb1-a342-4aad-b645-7837c299c2cc', 'bloomington', 'Dave Askins beta access (Google)'),
  ('5232ef0b-3f20-453d-bd81-3470884aec93', 'bloomington', 'Jon Udell beta access (GitHub judell)')
on conflict (user_id, city) do update
set note = excluded.note;
