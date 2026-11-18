# Physics Engine — Week 02

## 2026-09-28 to 2026-10-04 — First React frontend, Supabase proposal, milestone

Planned hours: 32 (milestone 4, React frontend 24, Supabase/redesign proposal 4) · Meetings: Mon 28 Sept, Thu 1 Oct (first milestone)

**What I worked on**
- Built a first React frontend (Vite + React 18, plain JSX) under `physics-engine/frontend/`, with `engine/static_files.py` (path-safe static file server). `server.py` serves `frontend/dist/` when built, else the old inline page.
- Added a one-at-a-time hint ladder per `physics_mode_api.json`, and filtered empty source phrases.
- Proposed a Supabase login system and a UI redesign to the manager by email.
- Milestone (1 Oct meeting): public demo live, authenticated, rate-limited.

**What I tried, and what I expected**
- Expected the frontend to drop into `server.py` with no backend changes.
- Expected the login idea to be a simple yes/no from the manager.

**Where it resisted, and what I did next**
- `server.py` crashed on start: `import static_files` ran before `sys.path.insert(..., "engine")` → ImportError. Moved the import.
- Login proposal raised real blockers before any code: Q6 (data/IRB governance), unclear admin scope, Supabase free-tier projects pausing. Sent an email asking permission instead of building.
- DEPLOY.md still said "31 formula cards"; the KB has 25.

**What Claude or another person contributed — accepted, changed, rejected**
- Claude wrote the nine frontend files, `static_files.py` and the `server.py` patch; I recreated them in PyCharm and tested.

**What I understand now, and what I still don't**
- Understand: `dist/` must be built and committed last, because Render does not build the frontend.
- Open: this JSX frontend was later replaced by the TypeScript one (week 03). Part of this week's work did not survive.

**Evidence**
- https://github.com/jashshah127/humanitariansai: `frontend/`, `engine/static_files.py`, `server.py`
