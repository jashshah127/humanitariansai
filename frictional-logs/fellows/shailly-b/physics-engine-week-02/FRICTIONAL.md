# Week 02 · 2026-10-12 to 2026-10-18 · Onboarding review, Supabase sandbox, AI-tagging research, local setup

*Written 2026-11-10, reconstructed from my dated findings log, plan of action, mid-term report, commit history and my chats with Claude. Not written at the time.*

**Planned:** 32 hours (plan Week 2: sign-in, roles, RLS, RLS tests, auth doc). **Meetings:** 2 (Mon 12 Oct, Thu 15 Oct).

**Plan for this week** (from my mid-term report; hours are plan estimates):

| Planned task | Hours | Status | Done in |
|---|---|---|---|
| Build signup/login using Supabase Auth | 8 | Complete, 21 Oct | week 03 |
| Build role assignment: admin vs regular user | 6 | Complete, 3 Nov | week 05 |
| Build row-level security policies | 8 | Complete, 22 Oct | week 03 |
| Tests confirming RLS blocks another user's data | 6 | Complete, 3 Nov | week 05 |
| Document the auth architecture | 4 | Complete, 3 Nov | week 05 |
Most of what I actually did this week was plan **Week 1** work, plus an early semantic-search prototype (plan Week 6).

## 1. What I worked on
- 13 Oct: read-only onboarding review of `physics-engine/`: structure, data flow, dependencies, fragile spots. Ran `eval/ci_check.py`: all passed.
- 13 Oct: Supabase sandbox project (Free plan). Signed in over HTTP, checked the token (ES256, 60-minute lifetime, refresh token), fetched JWKS.
- 13 Oct: test table `problem_history` + 3 RLS policies: 5 of 5 security tests passed. pgvector enabled; toy similarity test.
- 14 Oct: semantic search prototype: compared `gemini-embedding-001` and `-2` on the 16 golden-set problems (both 6 of 6); added a 768-number embedding column, HNSW index and `match_problems()`; confirmed RLS applies to search (another user got 0 results).
- 14 Oct: browser test with supabase-js: session kept in localStorage, no cookies; sign-out test.
- 14–15 Oct: structured-output test (prompt-only vs schema-enforced) and confidence test (5 runs × 3 problems).
- 15 Oct: local dev: Supabase CLI 2.121.0 via npx, Docker, `supabase init` + `start`.
- 15 Oct: first migration `20261015194448_initial_schema.sql` (app_role, profiles, signup trigger); profile behaviour tests 6 of 6.
- Started a dated findings log for the team (kept outside the repo).

## 2. What I tried, and what I expected
- Tried: prompt-only JSON vs schema-enforced output on 3 problems. Expected the schema version to always give clean, parseable output, and the prompt-only version to be less reliable.
- Tried: asking the same question 5 times (self-consistency), with one deliberately ambiguous problem (charged ball on a string). Expected the model to disagree with itself on the ambiguous problem, so disagreement could flag doubtful tags.
- Question I set out to answer: does a signed-out token still pass `/auth/v1/user`? Expected signing out to stop the token working everywhere.
- Tried: two embedding models and different cutoffs for "similar". Expected one similarity cutoff to work for both models.

## 3. Where it resisted, and what I did next
- Test users couldn't sign in: `email_not_confirmed`. Recreated them with Auto Confirm.
- All three Gemini embedding models returned 3,072 numbers, too many for the index. Asked for 768 instead; both models support it.
- Prompt-only JSON failed 3 of 3: every reply wrapped in ```json fences. Schema-enforced output: 3 of 3 valid.
- Self-reported confidence was flat (0.95–0.99) and self-consistency gave 5 of 5 agreement even on the ambiguous problem. Dead end for spotting doubtful tags; plan switched to cross-checking against the engine's formula card.
- Grade and difficulty came out arbitrary (a quantum problem tagged `high_school / easy`). No definitions exist anywhere in the repo.
- Gemini errors: 503 "high demand" on the flash models; `gemini-2.5-flash` 404 "no longer available"; 429 on `gemini-3.8-flash` after aggressive retries (retries burned the free quota); one request with no answer for 60 s.
- Sign-out: Supabase Auth rejects a signed-out token at once (403 `session_not_found`), but the REST API still accepted it until expiry.
- One cutoff did not fit both models (good matches scored 0.67–0.80 on one, 0.78–0.91 on the other). Cutoffs have to be set per model; chose `gemini-embedding-001` at about 0.75.
- `T` collision (tension vs period): search followed meaning; the mix-up is in the engine's formula matching.
- Homebrew install of the Supabase CLI blocked (tap trust). Used npx with a pinned version.
- 15 Oct: accidentally ran a `create type` in the hosted SQL editor (drift from the migrations). Running the undo together with it aborted the transaction; ran only `drop type`.

## 4. What Claude or another person contributed — accepted, changed, rejected
- Claude wrote the two tagging test scripts (`classify_test.py`, `confidence_test.py`), the first migration SQL and drafts of the findings documents, and guided me step by step. I ran every command and SQL statement myself and checked the outputs.
- No changes or rejections of Claude's code recorded this week.

## 5. What I understand now, and what I still don't
- Schema enforcement guarantees valid **format**, not correct **content**.
- A blocked read/update under RLS returns success with 0 rows, not an error.
- Instant sign-out needs the server to ask Supabase Auth, not just check the token's signature.
- Still open: grade and difficulty definitions; whether "Vibrations and Waves" belongs under Mechanics; problems with two correct topics.

## Evidence
- Tagging test scripts and first migration (committed 20 Oct): [ab66da2](https://github.com/jashshah127/humanitariansai/commit/ab66da2)
- Migration: [supabase/migrations/20261015194448_initial_schema.sql](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/supabase/migrations/20261015194448_initial_schema.sql)
- Findings log: kept outside the repo, not shared as a link.
