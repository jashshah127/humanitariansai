# Week 05 · 2026-11-02 to 2026-11-08 (logged up to 4 Nov) · Milestone 1: roles, tests, classifier, problem logging, integration

*Written 2026-11-10, reconstructed from my commit history, dated findings log, evaluation result files, plan of action, mid-term report and my chats with Claude. Not written at the time.*

**Planned:** 32 hours (plan Week 5: admin dashboard design, "most-asked problems" view, charts, tests; not started). **Meetings:** 1 so far (Mon 2 Nov).

**Plan for this week** (from my mid-term report; hours are plan estimates):

| Planned task | Hours | Status | Done in |
|---|---|---|---|
| Design the admin dashboard's information architecture | 4 | Not started | — |
| Build the "most-asked problems" ranked view | 10 | Not started | — |
| Build grade-level and difficulty breakdown charts | 10 | Not started | — |
| Tests for the dashboard queries | 8 | Not started | — |

**Week 5 so far** (from my report): went to finishing Milestone 1 (the plan Week 2–4 tasks above). Dashboard work starts after the joint demo.
This week finished the plan Week 2–4 tasks for Milestone 1. This log covers 2–4 Nov.

## 1. What I worked on
- 3 Nov: role management: `set_user_role()` (admins only, last admin can't be removed), `admin_list_users()`, `GET /me`. Applied to hosted (dry run first).
- 3 Nov: `eval/rls_tests.py`: security suite through the real API (35 checks, 43 by 4 Nov). Auth architecture doc.
- 3 Nov: `engine/classifier.py` (card-first topics, schema-enforced Gemini, review flags); accuracy tool `eval/classifier_eval.py` (answer key from the formula cards: 29 problems); circuit breaker.
- 3 Nov: `engine/redact.py` (emails, phones, links, IDs); `engine/problem_log.py` (store each solve cleaned, then tag it in one background worker); tagging migration; frontend API contract; regression pass.
- 4 Nov: accuracy: `gemini-3.6-flash` 10 of 10, fallback `gemini-3.5-flash-lite` 19 of 19 (29 of 29 cards).
- 4 Nov: model overrides (`GEMINI_PARSE_MODEL`, `GEMINI_TAG_MODELS`); logging health on `/stats`; live demo; tagging migration applied to hosted; draft PR #9; merged my branch with `feature-atharva` locally and tested it in the browser.
- 4 Nov: mid-term report.

## 2. What I tried, and what I expected
- Evaluation: one model over two days because of the 20-a-day limit (my choice on 3 Nov). Expected 20 problems on day 1 and 9 on day 2 to fit inside the free limit.
- 4 Nov: chose to spend about 11 remaining calls as 6 evaluation problems + 2 live solves. Expected about 11 calls to be enough for both.
- Redaction: expected narrow rules to catch emails, phones and IDs without changing any physics numbers. Logging worker: expected `/solve` replies to be no slower.

## 3. Where it resisted, and what I did next
- Migration used `current_role`, a reserved word. Renamed it `v_current_role` (still only local, so editing was safe).
- "Unknown user" error P0002 came back as HTTP 500. Switched to 22023 (HTTP 400).
- A test line compared a value with itself. Removed and re-ran the suite.
- `.env` broken: a note and example lines were pasted in and `JWT_SECRET` was deleted. Cleaned it to 5 variables and re-added the secret.
- First evaluation run stalled for 40+ minutes and was killed: `gemini-3.8-flash` timed out on every call (~1.5 min per problem). Added the circuit breaker.
- `python3` (python.org) failed with `CERTIFICATE_VERIFY_FAILED`. Used `.venv/bin/python` instead.
- 429 `GenerateRequestsPerDayPerProjectPerModel-FreeTier = 20`. `gemini-3.7-flash` and `3.5-flash` were refused too.
- `npx` pulled Supabase CLI 3.0.0 (new major). Pinned 2.121.0.
- Live test: Postgres error replies quote the whole row ("Failing row contains …"), which would put problem text in server logs. Kept only the code and message; added a test.
- My new tag rule made an old test fail for the wrong reason (23514 instead of 23503). Gave those test rows a `tag_source` so each test checks one rule.
- 4 Nov: the circuit breaker skipped 9 evaluation problems untried. Set `cooldown=0` for the evaluation only.
- 4 Nov: ran the first evaluation command a second time by mistake. Hit the per-minute limit, and failed retries counted toward the daily 20, so only 10 problems were measured on the main model. Added `--skip`.
- Live demo: the lite parser missed `g` in a free-fall problem, so the engine marked it Unverified. One row stayed untagged because the test server was stopped after 15 s, mid-tag. Added an "untagged because …" log line and `/stats` counts.
- Opening `/login` directly on a built app gives 404 (no fallback page). Reported to the frontend teammate.

## 4. What Claude or another person contributed — accepted, changed, rejected
- Claude wrote the code, tests and docs in all the commits below, the API contract, the PR #9 text and the report draft. I reviewed each step, ran the evaluation commands, did the browser sign-in test, and approved each outward step (hosted migration, PR, fallback run).
- My decisions: single model split over days; the 6 + 2 quota split; adding the Medhavy section at the end of the report after my manager asked.
- The CI/CD teammate's pipeline ran on PR #9 (both jobs passed). The frontend teammate's branch was used in the local integration test.
- No changes or rejections of Claude's code recorded.

## 5. What I understand now, and what I still don't
- On the free tier, retries during an outage use up the day's quota. A circuit breaker helps a live server but is wrong for an evaluation.
- A bounded queue drops entries under load rather than slowing students down.
- Rule-based redaction has to stay narrow so physics numbers survive. Names aren't removed.
- 29 of 29 is on clean textbook problems: an upper bound.
- Still open: paid Gemini tier or Claude credit; grade/difficulty definitions; Q6 (student data); the joint demo and merging PR #9; `SUPABASE_SECRET_KEY` on Render; the `/login` 404; the main model's run on the last 19 problems (planned next).

## Evidence
- Draft PR: https://github.com/jashshah127/humanitariansai/pull/9
- Commits: [3a5f1ca](https://github.com/jashshah127/humanitariansai/commit/3a5f1ca) roles + /me · [5e43e94](https://github.com/jashshah127/humanitariansai/commit/5e43e94) RLS suite · [c7112d7](https://github.com/jashshah127/humanitariansai/commit/c7112d7) auth doc · [905df90](https://github.com/jashshah127/humanitariansai/commit/905df90) classifier · [275086d](https://github.com/jashshah127/humanitariansai/commit/275086d) eval + circuit breaker · [f8eed0d](https://github.com/jashshah127/humanitariansai/commit/f8eed0d) redaction · [ec1dea2](https://github.com/jashshah127/humanitariansai/commit/ec1dea2) problem logging · [9ecbf87](https://github.com/jashshah127/humanitariansai/commit/9ecbf87) API contract · [4efef07](https://github.com/jashshah127/humanitariansai/commit/4efef07) eval fix · [e0e93c8](https://github.com/jashshah127/humanitariansai/commit/e0e93c8) model overrides
- Files: [engine/classifier.py](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/engine/classifier.py), [engine/redact.py](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/engine/redact.py), [engine/problem_log.py](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/engine/problem_log.py), [eval/rls_tests.py](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/eval/rls_tests.py), [docs/api-contract.md](https://github.com/jashshah127/humanitariansai/blob/feature-shailly/physics-engine/docs/api-contract.md)
