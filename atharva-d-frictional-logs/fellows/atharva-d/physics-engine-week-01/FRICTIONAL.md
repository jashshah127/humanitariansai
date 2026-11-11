# Physics Engine — Week 01

## 2026-09-21 to 2026-09-27 — Onboarding, Render deploy, JWT auth, rate limiting

Planned hours: 32 (split across tasks: ci_check 2, docs + demos 5, Gemini key + local run 3, Render 8, JWT 8, rate limit 4, DEPLOY.md 2) · Meetings: Mon 21 Sept, Thu 24 Sept

**What I worked on**
- Onboarding (done 16–18 Sept, before the counted start date): Python 3.12 venv, ran `eval/ci_check.py`, `eval/demo.py`, `eval/demo_phase1.py`; Gemini key as an env var; ran `server.py` on the 3 built-in examples.
- Deployed `server.py` to Render: https://physics-engine-2inp.onrender.com
- Added stdlib-only HS256 JWT auth on `/solve` and `/grade` (`engine/jwt_auth.py`, `mint_token.py`).
- Added a global rate limiter (`engine/rate_limit.py`, 8 requests/min, checked before auth) to protect the shared Gemini free-tier quota.
- Updated DEPLOY.md with the live URL, auth and rate-limit steps (committed 23 Sept, a week ahead of plan).
- All checks in `ci_check.py` passed; demo.py 16/16, demo_phase1.py 5/5 with P6 sent to `no_deterministic_path`. All 3 built-in server examples ran correctly.
- Raised the check-count gap and the `G`/`g` glossary bug with the team (later; not in the same week I found them). The suite now has 14 checks.

**What I tried, and what I expected**
- Expected the plan's onboarding steps to match the repo. They didn't.
- Expected Render to find `render.yaml` and use the free tier by default.
- Expected the Gemini client's own pacing to protect the quota.

**Where it resisted, and what I did next**
- Plan said "confirm all 12 checks pass". `ci_check.py` had fewer (10 by my onboarding count; 8 by a later count). Never settled which number was right at the time.
- `GRADUATE_LEVEL_TEST.md` and `qualifier_exam_test.py`, named in the plan, did not exist.
- `demo_phase1.py` on P1 (pure 1D kinematics): constant `G` was injected next to `g`. Cause: `variable_glossary.py` injects constants by an output variable shared across cards, not by the matched card. The code comments already flagged this risk.
- PyCharm showed 22 false "unresolved reference" errors → marked `engine/` as Sources Root.
- Windows: several Python installs (Store stub, 3.12, 3.14) on PATH started duplicate servers. Fixed with the venv path; `netstat -ano | findstr :8000` to see who owns the port; `curl.exe` because PowerShell aliases `curl`.
- Render: `render.yaml` lives in `physics-engine/`, so Blueprint Path had to be set by hand. Render picked the paid Starter plan until `plan: free` was added.
- `auth.py` clashed with an installed PyPI package → renamed `jwt_auth.py`. Fixed a token-persistence bug in the demo page.
- Found `_llm()` creates a new `GeminiLLM()` per request, so its pacing (`self._last`) resets every time. The new rate limiter is the only real quota protection.
- Considered a custom domain; dropped it (yearly cost, DNS delay, unclear account ownership).

**What Claude or another person contributed — accepted, changed, rejected**
- Claude walked me through venv setup, Render config, the JWT code and the rate limiter. I applied and tested each locally and on Render.
- Gemini key request: Claude recommended the cheaper Flash-Lite tier and said there was no evidence I needed Pro. I rejected that and sent a Pro request, and removed the caveat Claude had added about the missing justification.

**What I understand now, and what I still don't**
- Understand: adding auth means anyone using the public demo page now needs a token.
- Understand: the existing pacing code only works in long-running scripts like `baseline_eval.py`.
- Open: `/solve` and `/grade` report the same Gemini 429 with different badge/route values.
- Open: the `G`/`g` glossary bug and the check-count gap were not raised with the manager this week.

**Evidence**
- https://github.com/jashshah127/humanitariansai (branch `feature-atharva`): `engine/jwt_auth.py`, `engine/rate_limit.py`, `render.yaml`, `DEPLOY.md`