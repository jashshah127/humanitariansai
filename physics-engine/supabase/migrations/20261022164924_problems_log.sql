-- =========================================================
-- problems_log: a DE-IDENTIFIED record of every problem asked, with its tags.
--
-- Identity scope "none", the same as most events in engine/event_log.py:
-- no user_id and no session_id, so the log can say WHAT was asked, never WHO asked it.
--
-- Design decisions (2026-10-22):
--   1. created_at is stored ROUNDED TO THE HOUR (data minimisation: exact times can point
--      to a person). Hourly is still fine-grained enough for trends and spike alerts.
--      The database enforces it, so no caller can store exact times by mistake.
--   2. topic/subtopic come from a LOOKUP TABLE (public.topics), not free text or an enum:
--      only valid pairs are accepted, and changing the list is a row edit, not a migration.
--      grade_level and difficulty stay free text until the team defines their values.
--   3. problem_text is CLEANED BEFORE STORING by the server (emails, phone numbers, links,
--      ID-like numbers -> markers such as [email]); `redactions` counts what was removed.
--      Names cannot be removed reliably by rules, so this table is MOSTLY de-identified --
--      to be confirmed under Q6, with a retention period still to be set.
-- =========================================================

-- 1. Allowed (topic, subtopic) pairs: the engine's formula-card labels, plus "Other".
create table public.topics (
  topic    text not null,
  subtopic text not null,
  primary key (topic, subtopic)
);

alter table public.topics enable row level security;

create policy "topics: readable by signed-in users" on public.topics
  for select to authenticated
  using (true);

insert into public.topics (topic, subtopic) values
  ('Mechanics', 'Kinematics'),
  ('Mechanics', 'Dynamics'),
  ('Mechanics', 'Work & Energy'),
  ('Mechanics', 'Momentum'),
  ('Mechanics', 'Rotation'),
  ('Mechanics', 'Gravitation'),
  ('Mechanics', 'Vibrations and Waves'),
  ('E&M', 'Electrostatics'),
  ('E&M', 'Circuits'),
  ('E&M', 'Magnetism'),
  ('E&M', 'Induction'),
  ('Thermodynamics', 'Gas Laws'),
  ('Thermodynamics', 'Calorimetry'),
  ('Thermodynamics', 'Heat Engines'),
  ('Thermodynamics', 'Entropy'),
  ('Thermodynamics', 'Laws'),
  ('Other', 'Other');

-- 2. Is the signed-in caller an admin? Used by admin-only policies.
--    security definer + empty search_path, like handle_new_user(): it reads profiles with
--    the owner's rights, so it keeps working even if profiles' own policies change later.
create function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
  select exists (
    select 1 from public.profiles
    where id = (select auth.uid()) and role = 'admin'
  );
$$;

-- 3. The log itself.
create table public.problems_log (
  id           uuid primary key default gen_random_uuid(),
  problem_text text not null,
  redactions   integer not null default 0 check (redactions >= 0),
  topic        text,
  subtopic     text,
  grade_level  text,
  difficulty   text,
  verification text not null check (verification in ('verified', 'needs_review', 'unverified')),
  tag_model    text,
  -- UTC whole hours only. (Rounding in UTC, not the session time zone, keeps the rule exact
  -- and independent of server settings -- some time zones are offset by half an hour.)
  created_at   timestamptz not null default (date_trunc('hour', now() at time zone 'utc') at time zone 'utc'),

  constraint problems_log_created_at_whole_hour
    check (created_at = date_trunc('hour', created_at at time zone 'utc') at time zone 'utc'),
  -- Tags are added later by the classifier, so both may be empty -- but never just one.
  constraint problems_log_topic_pair_complete
    check ((topic is null) = (subtopic is null)),
  constraint problems_log_topic_pair_valid
    foreign key (topic, subtopic) references public.topics (topic, subtopic)
);

alter table public.problems_log enable row level security;

-- Admins read it (dashboards). There is deliberately NO insert/update/delete policy:
-- browsers can never write here. Only the server writes, using the secret key (which
-- bypasses RLS) -- otherwise anyone signed in could fill the log with junk.
create policy "problems_log: admins read" on public.problems_log
  for select to authenticated
  using ((select public.is_admin()));

-- Indexes for the dashboard queries: trends over time, topic breakdowns, Unverified spikes.
create index problems_log_created_at_idx   on public.problems_log (created_at);
create index problems_log_topic_idx        on public.problems_log (topic, subtopic);
create index problems_log_verification_idx on public.problems_log (verification, created_at);
