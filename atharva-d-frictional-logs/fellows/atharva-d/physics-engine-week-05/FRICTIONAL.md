# Physics Engine — Week 05

## 2026-10-19 to 2026-10-25 — Visualizations, component tests, deploy fixes, quantum task scoping, Supabase sign-in

Planned hours: 32 (hint ladder 8 and grade UI 8 — both built in week 04; trajectory 10, component tests 6) · Meetings: Mon 19 Oct; no Thursday meeting (22 Oct)

**What I worked on**
- PR #5 (19 Oct): `card_id` and `knowns` in the response; trajectory plot for projectile answers; Atwood force diagram that checks Newton's 2nd law against the engine's numbers; nine component test files.
- Fixed deployed page routes returning 404 (`server.py` single-page-app fallback).
- Generated a proper JWT secret; checked the Render Blueprint path.
- New task: quantum physics textbook. Turned meeting notes into questions, emailed the manager and both professors, researched Python libraries (sympy best fit).
- 23 Oct: merged a teammate's Supabase auth branch; built frontend sign-in (email + password only, reset-password page, always on, `/` redirects to `/app`).
- No Thursday meeting this week (22 Oct).
- Trajectory plot draws only when the answer is Verified.
- Atwood diagram and Supabase login were planned for week 06; built early this week.
- Redeployed on Render after the 404 fix.

**What I tried, and what I expected**
- Expected the deployed site to behave like local dev.
- Expected the teammate's branch to contain only the auth work.
- Expected the quantum task to be a step-by-step solver for the book's worked examples.

**Where it resisted, and what I did next**
- Gemini returned malformed JSON → turned on JSON response mode; added logging of which provider answered.
- A zip extracted into a nested folder, and a full-file replacement of `types.ts` and `physics_mode_api.json` overwrote my newer uncommitted grade code. Recovered it with `git diff`. Set a rule: no zips, one file at a time, line-level edits only.
- CI failed on the draft PR: untracked visualization folder, Prettier formatting, an unused variable in a test mock. Now run typecheck, lint, format:check, test, build locally before pushing.
- `/app?mode=grade` worked locally but 404'd on Render: Vite serves `index.html` for every path, `server.py` didn't. Also `mode.ts` only knew solve/tutor, so `?mode=grade` silently showed solve mode even locally — I may have been testing the wrong mode.
- Render: a new Blueprint named `physics-engine` could duplicate the existing `physics-engine-2inp` service.
- Teammate's branch brought unreviewed extras (a problems log table, roles migration, topics lookup). Its commit message said 'de-identified'; its own SQL said 'mostly de-identified'. Merged after review because nothing writes to that table yet.
- Sign-in testing: confused my own sandbox Supabase project with the team's; env vars set in PyCharm didn't reach the terminal. Confirmed end-to-end: sign in, `/solve` works, sign-out kills the token.
- Rotated secrets that had been pasted into chats.
- Quantum task scope shifted mid-week: from a solver to making existing Medhavy textbook simulations interactive, in a new repo. Most of the first plan no longer applies.

**What Claude or another person contributed — accepted, changed, rejected**
- Claude wrote the visualization, test, auth-page and `server.py` fix code, and drafted the quantum emails. I applied, tested and committed.
- I corrected Claude twice for jumping into code or plans before I asked.
- I chose `@supabase/supabase-js` over hand-written fetch calls and refused extra questions on sign-in trade-offs.

**What I understand now, and what I still don't**
- Understand: dev mode hides routing bugs; test with `npm run build` + `server.py` before deploying.
- Open: no migrations go to the hosted Supabase until Q6 (data governance) is answered.
- Open: quantum task blocked until the book and repo access arrive; role split with the textbook team unclear; who reviews the physics is unknown.

**Evidence**
- https://github.com/jashshah127/humanitariansai/pull/5 (visualizations + tests). Sign-in work (23 Oct) is on `feature-atharva`, not yet merged to `main`.