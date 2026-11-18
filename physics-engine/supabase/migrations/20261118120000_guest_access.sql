-- Guest (anonymous) sign-in: a per-guest problem limit and a daily total for all guest.
-- The server enforces both, through use_guest_problem(); browsers can't read or change
-- any of this. With no CAPTCHA, the DAILY TOTAL is the real protection: new guest are
-- free to create, so a per-guest limit alone never caps the total.

-- 1. Problems used per guest. No policies: only the server (secret key) can touch it.
create table public.guest_usage (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  used       int not null default 0 check (used >= 0),
  updated_at timestamptz not null default now()
);
alter table public.guest_usage enable row level security;

-- 2. Problems used by all guest together, per UTC day.
create table public.guest_daily_usage (
  day  date primary key,
  used int not null default 0 check (used >= 0)
);
alter table public.guest_daily_usage enable row level security;

-- 3. Check AND count in one step, with row locks, so two tabs can't both get the last
--    problem. Returns {"status": "ok" | "guest_limit" | "daily_limit" | "not_guest",
--    "remaining": n}.
create function public.use_guest_problem(p_user uuid, p_per_guest int, p_daily int)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_used  int;
  v_total int;
  v_today date := (now() at time zone 'utc')::date;
begin
  -- Only guest are counted: a server bug must never charge a real account.
  if not exists (select 1 from auth.users where id = p_user and is_anonymous) then
    return jsonb_build_object('status', 'not_guest', 'remaining', null);
  end if;

  -- Always lock the guest row first, then the daily row: one fixed order, no deadlocks.
  insert into public.guest_usage (user_id) values (p_user) on conflict (user_id) do nothing;
  select used into v_used from public.guest_usage where user_id = p_user for update;
  if v_used >= p_per_guest then
    return jsonb_build_object('status', 'guest_limit', 'remaining', 0);
  end if;

  insert into public.guest_daily_usage (day) values (v_today) on conflict (day) do nothing;
  select used into v_total from public.guest_daily_usage where day = v_today for update;
  if v_total >= p_daily then
    return jsonb_build_object('status', 'daily_limit', 'remaining', p_per_guest - v_used);
  end if;

  update public.guest_usage set used = used + 1, updated_at = now() where user_id = p_user;
  update public.guest_daily_usage set used = used + 1 where day = v_today;
  return jsonb_build_object('status', 'ok', 'remaining', p_per_guest - v_used - 1);
end;
$$;

-- Supabase lets browsers run new public functions by default. Without these lines a
-- guest could call this directly and reset nothing, but read or burn others' budget.
revoke execute on function public.use_guest_problem(uuid, int, int) from public, anon, authenticated;
grant execute on function public.use_guest_problem(uuid, int, int) to service_role;