-- =========================================================
-- 1. Roles: the only values a role can ever have
-- =========================================================
create type public.app_role as enum ('user', 'admin');

-- =========================================================
-- 2. Profiles: one row per login account (auth.users), plus app fields
-- =========================================================
create table public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  role       public.app_role not null default 'user',
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- Signed-in users can read their own profile. No insert/update policy on purpose:
-- users must never be able to change their own role.
create policy "profiles: read own" on public.profiles
  for select to authenticated
  using ((select auth.uid()) = id);

-- =========================================================
-- 3. Create a profile automatically whenever someone signs up
-- =========================================================
create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id) values (new.id);
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
