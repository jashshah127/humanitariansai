# Physics Engine — Week 07

## 2026-11-02 to 2026-11-08 — UGPhysics CSV plan, frontend polish, mid-point report, spend guard, admin roles

Planned hours: 32 planned (responsive pass 10 of these) · Meetings: Mon 2 Nov, Thu 5 Nov

**What I worked on**
- Meeting added on Monday 2 Nov.
- Planned how to run the engine on the UGPhysics Classical Mechanics (836) and Electromagnetism (390) CSVs.
- Frontend polish steps 1–4: cleanup, error/empty states, accessibility, responsive.
- Mid-point report for supervisors (3 Nov).
- Built `spend_guard.py` to enforce the $40 all-time API budget; `MetaLLM` provider in `parse.py`; `--budget` flags in `run_benchmark.py`.
- Checked what admin-roles frontend work is missing; merged teammate commit `3a5f1ca`.
- Responsive pass: phone layouts for the workspace, result cards, diagrams, auth and 404 pages; bigger tap targets; tested at 320, 375, 768 and 1280 px.
- UGPhysics plan: measure answer rate and accuracy; split into development and held-out sets; start with Vibrations and Waves; sort every failure by cause (misread, no matching card, missing values, unclear problem, wrong answer) and fix the biggest cause first.
- Rule kept: nothing is Verified unless the formula card matches. A wrong Verified answer counts as the worst failure.

**What I tried, and what I expected**
- Expected 'solve the CSV' to mean writing solutions. It means running the engine and measuring where it fails.
- Expected the platform's spend limit to stop spending at the limit.

**Where it resisted, and what I did next**
- Earlier benchmark runs never answered a single problem; Ollama crashes were again being counted as wrong answers.
- Only ~148 of 836 mechanics problems can be scored numerically today; 387 need symbolic comparison that isn't built.
- A legacy global stylesheet (`legacy/styles.css`) was silently overriding fonts → removed.
- Solved answers in grade mode showed raw SymPy strings, not LaTeX. Cause was the backend (`grade_mode.py`), not the frontend. Added a `relationship_latex` field end to end.
- Accessibility: screen-reader announcements too broad, focus not moving to new hints, duplicate heading IDs, missing `<h1>`s. `vitest-axe` didn't work → used `axe-core`. A test broke because visible text and hidden announcement matched the same query.
- The platform 'spend limit' only sends warning emails. Built my own hard stop with a $35 internal limit. It only covers benchmark calls, not the coding agent.
- Admin roles: no role in the frontend, no RPC calls, no admin route. Hiding buttons is not security; the database check is.
- Merge was messy: half-built `dist/`, unexplained backend edits, stray files. Got stuck in Vim on the merge commit.

**What Claude or another person contributed — accepted, changed, rejected**
- Claude audited the frontend, wrote the polish changes, `spend_guard.py` and `MetaLLM`, and tested the guard against a fake server. I ran tests and builds locally.
- I deferred a SymPy subscript mismatch (m₁ vs 'm1') to later.
- Report: I asked Claude to merge the two plans into one timeline, remove commit IDs (squash merges make them misleading) and remove the open-issues section.

**What I understand now, and what I still don't**
- Understand: a clean merge does not mean the code still works.
- Open: phone check of diagram labels and example-button layout; animation (step 5) not started.
- Open: whether to collapse the 15 example buttons on mobile.
- Open: confirm with the manager the CSV work doesn't overlap a teammate's benchmark task.
- Open: 387 'Math Derivation' mechanics problems can't be scored until symbolic answer checking is finished.
- Open: new formula cards need physics review (Prof. Sri) before merge.
- Next scope after the benchmark: quantum problems from the Medhavy textbook, waiting on the book and repo access.

**Evidence**
- https://github.com/jashshah127/humanitariansai branch `feature-atharva`: `eval/spend_guard.py`, `engine/parse.py`, `frontend/src/`