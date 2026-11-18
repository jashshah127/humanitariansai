# Week 03 · 2026-10-19 to 2026-10-25 · Server sign-in, de-identified problem log, hosted project

*Written 2026-11-10, reconstructed from my dated findings log, commit history, plan of action, mid-term report and my chats with Claude. Not written at the time.*

**Planned:** 32 hours (plan Week 3: build the classifier, validate it, wire it in, tests). **Meetings:** 1 (Mon 19 Oct; no meeting Thu 22 Oct).

**Plan for this week** (from my mid-term report; hours are plan estimates):

| Planned task | Hours | Status | Done in |
|---|---|---|---|
| Build the AI problem classifier (grade, difficulty, topic) | 10 | Complete, 3 Nov | week 05 |
| Validate topic-tagging against `formula_kb.py`'s labels | 6 | Complete, 4 Nov (29 of 29) | week 05 |
| Wire the classifier in so every solved problem is tagged and logged | 8 | Complete, 3 Nov | week 05 |
| Tests for the classification pipeline | 8 | Complete, 3–4 Nov | week 05 |
What I actually did this week was mostly plan **Week 1–2** work (sign-in, schema, RLS, pipeline plan).

## 1. What I worked on
- 20 Oct: consolidated backend infrastructure document for the team (components, flows, data model, security, environments, CI/deploy).
- 20 Oct: committed the local Supabase project and the profiles/roles migration.
- 21 Oct: `engine/supabase_auth.py` + `server.py` accept Supabase sign-in tokens on `/solve`, `/parse`, `/grade`. Refused token → 401; Supabase unreachable → 503. 2 offline CI checks; end-to-end against local Supabase 6 of 6 (sign-out → 401).
- 22 Oct: `problems_log` migration: no user or session id, time rounded to the UTC hour (enforced by a check constraint), `topics` lookup table (17 pairs), `is_admin()`, admin-only read, no browser writes.
- 22 Oct: one-page classification pipeline plan, with proposed grade/difficulty definitions for the manager to confirm.
- 22 Oct: hosted Supabase project: migrations pushed (dry run first), existing accounts backfilled with profiles, Site URL + redirect URLs for local and Render, frontend teammate invited and given app-admin role.
- 22–23 Oct: the frontend teammate reviewed my changes and asked for the project URL, publishable key, project membership, sign-up/confirmation settings and what `env()` means. I provided them.
- Renamed my branch to `feature-shailly`.

## 2. What I tried, and what I expected
- Tried: checking tokens by asking Supabase (`GET /auth/v1/user`) instead of verifying them locally. Chosen because sign-out then works at once (week 02 finding). Expected one extra network call per request to be an acceptable cost for that.
- Tried: a mutation check (planting a bug to see the CI check fail). Expected the check to fail on the planted bug and pass once it was removed.
- Hosted setup: pushed with a dry run first, after the week-02 accidental change. Expected the dry run to list only the migrations I meant to apply.

## 3. Where it resisted, and what I did next
- Re-testing on 20 Oct: `/solve` still labelled a failed-verification answer "Verified". Raised with the team.
- Pasted SQL into the Terminal instead of the SQL Editor: zsh parse error. Learned: npx/python in Terminal, SQL in the dashboard.
- Nothing else recorded this week.

## 4. What Claude or another person contributed — accepted, changed, rejected
- Claude wrote `supabase_auth.py`, the server auth changes, the auth CI checks and the `problems_log` migration. I reviewed them, ran the end-to-end tests and did the hosted-project steps in the dashboard myself.
- The frontend teammate reviewed my changes.
- Rejected: on 22 Oct Claude started doing steps itself when I'd only asked what to do. I stopped it and asked for steps only.
- No changes to Claude's code recorded this week.

## 5. What I understand now, and what I still don't
- 401 vs 503: a bad token is the caller's problem; Supabase being down is ours, so the user isn't wrongly told they're signed out.
- RLS with no policy denies by default.
- Still open: grade/difficulty definitions (waiting on the manager); data governance (Q6); who owns the Supabase project long term.

## Evidence
- [ab66da2](https://github.com/jashshah127/humanitariansai/commit/ab66da2): local Supabase project, profiles/roles migration, tagging scripts (20 Oct)
- [35f9e61](https://github.com/jashshah127/humanitariansai/commit/35f9e61): server accepts Supabase sign-in tokens (21 Oct)
- [1548e34](https://github.com/jashshah127/humanitariansai/commit/1548e34): problems_log, topics, is_admin() (22 Oct)
- Files: [engine/supabase_auth.py](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/engine/supabase_auth.py), [supabase/migrations/20261022164924_problems_log.sql](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/supabase/migrations/20261022164924_problems_log.sql)
