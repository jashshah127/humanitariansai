-- Admin edits on problems_log, for the admin-only problem-history page.
--
-- Agreed with the frontend (2026-11-15): the page is admins only, and admins may FIX TAGS,
-- nothing else.
--   admins may change : topic, subtopic, grade_level, difficulty, needs_review, review_reason
--   locked            : problem_text, redactions, verification, created_at, matched_card,
--                       tag_model, tag_source (set automatically, see the trigger)
--   no browser insert or delete, not even for admins -- rows only come from real solves
-- Reading stays admin-only (policy from the problems_log migration).
--
-- Two layers, so neither can be bypassed alone:
--   1. COLUMN PRIVILEGES decide which columns a browser may change at all.
--   2. RLS decides which rows: only an admin's update matches the policy.
-- The server writes with the secret key (service_role), which is unaffected by both.

-- Who last edited the tags, and when. The editor is an admin (staff), not a student, so the
-- table stays free of student identity. Exact time is fine here: it describes staff work.
alter table public.problems_log
  add column tags_edited_by uuid references auth.users (id) on delete set null,
  add column tags_edited_at timestamptz;

-- 'admin' marks a tag a human corrected, so dashboards can tell it from engine/AI tags.
alter table public.problems_log drop constraint problems_log_tag_source_check;
alter table public.problems_log
  add constraint problems_log_tag_source_check
    check (tag_source in ('engine_card', 'llm', 'admin'));

-- Grade and difficulty were free text; an edit box could store anything. Same values as
-- engine/classifier.py (GRADES, DIFFICULTIES).
alter table public.problems_log
  add constraint problems_log_grade_level_valid
    check (grade_level in ('high_school', 'intro_undergrad', 'upper_undergrad', 'graduate')),
  add constraint problems_log_difficulty_valid
    check (difficulty in ('easy', 'medium', 'hard'));

-- 1. Column privileges. Supabase grants browsers every table privilege by default and relies
--    on RLS alone. Take them all back, then grant only reading and the editable columns.
revoke all on public.problems_log from anon, authenticated;
grant select on public.problems_log to authenticated;
grant update (topic, subtopic, grade_level, difficulty, needs_review, review_reason)
  on public.problems_log to authenticated;

-- 2. Rows: only admins' updates match. A non-admin's update changes 0 rows.
create policy "admins edit tags"
  on public.problems_log for update
  to authenticated
  using ((select public.is_admin()))
  with check ((select public.is_admin()));

-- Stamp every admin edit: who and when, and mark changed tags as admin tags. Runs only for a
-- signed-in admin (the server's own updates have no auth.uid(), so they are left alone).
create function public.problems_log_stamp_admin_edit()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if auth.uid() is not null and public.is_admin() then
    if (new.topic, new.subtopic, new.grade_level, new.difficulty)
       is distinct from (old.topic, old.subtopic, old.grade_level, old.difficulty) then
      new.tag_source := 'admin';
      new.tag_model := null;
    end if;
    new.tags_edited_by := auth.uid();
    new.tags_edited_at := now();
  end if;
  return new;
end;
$$;

create trigger problems_log_stamp_admin_edit
  before update on public.problems_log
  for each row execute function public.problems_log_stamp_admin_edit();
