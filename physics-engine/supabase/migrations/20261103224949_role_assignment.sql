-- =========================================================
-- Role assignment: an in-app way for admins to grant or remove the admin role.
--
-- Until now, making someone an admin needed a raw SQL update run by an operator.
-- public.set_user_role() lets an ADMIN do it through the API (POST /rest/v1/rpc/set_user_role),
-- with the rules enforced inside the database:
--   * only an admin can call it (anyone else gets "permission denied");
--   * the target must have a profile;
--   * the LAST admin cannot be demoted, so the app can never be left without an admin.
-- The very first admin is still created by an operator (one SQL update), because nobody
-- is an admin yet to grant it -- the usual "bootstrap" step.
--
-- Users still cannot change their own role through the profiles table: profiles has no
-- update policy. This function is the only path, and it checks is_admin() first.
-- =========================================================

create function public.set_user_role(target_user uuid, new_role public.app_role)
returns void
language plpgsql
security definer          -- needs to update profiles, which has no update policy
set search_path = ''      -- fully qualified names only (see handle_new_user)
as $$
declare
  v_current_role public.app_role;
  other_admins integer;
begin
  if not public.is_admin() then
    raise exception 'only admins can change roles' using errcode = '42501';
  end if;

  -- Lock every admin row first. Two admins demoting each other at the same moment would
  -- otherwise both see "one other admin left" and both succeed, leaving no admin at all.
  perform 1 from public.profiles where role = 'admin' for update;

  select role into v_current_role from public.profiles where id = target_user;
  if not found then
    raise exception 'no profile for user %', target_user using errcode = '22023';  -- invalid parameter -> HTTP 400
  end if;

  if v_current_role = 'admin' and new_role <> 'admin' then
    select count(*) into other_admins
    from public.profiles where role = 'admin' and id <> target_user;
    if other_admins = 0 then
      raise exception 'cannot remove the last admin' using errcode = 'P0001';
    end if;
  end if;

  update public.profiles set role = new_role where id = target_user;
end;
$$;

-- Functions in the public schema are callable by everyone by default. Restrict this one to
-- signed-in users (the admin check inside does the rest); anonymous callers get nothing.
revoke execute on function public.set_user_role(uuid, public.app_role) from public, anon;
grant execute on function public.set_user_role(uuid, public.app_role) to authenticated;

-- =========================================================
-- Admins list every user with their role, so they can see who to promote.
-- Emails live in auth.users, which the API can't read; this security-definer function
-- exposes only id, email, role and sign-up time, and only to admins.
-- =========================================================

create function public.admin_list_users()
returns table (id uuid, email text, role public.app_role, created_at timestamptz)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if not public.is_admin() then
    raise exception 'only admins can list users' using errcode = '42501';
  end if;
  return query
    select u.id, u.email::text, p.role, u.created_at
    from auth.users u
    join public.profiles p on p.id = u.id
    order by u.created_at;
end;
$$;

revoke execute on function public.admin_list_users() from public, anon;
grant execute on function public.admin_list_users() to authenticated;
