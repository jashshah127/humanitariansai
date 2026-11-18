# Physics Engine — Week 04

## 2026-10-12 to 2026-10-18 — TypeScript frontend build-out, KaTeX, Claude fallback, GitHub Actions, grade mode

Planned hours: 32 (problem input 6, badges 4, answer display 8, KaTeX 6, /solve wiring 6, GitHub Actions 2) · Meetings: Mon 12 Oct, Thu 15 Oct

**What I worked on**
- Built the TypeScript API client, result panel, workspace page and KaTeX formula rendering; wired the real `/solve` call.
- Hint ladder (PR #2, 14 Oct) and grade mode (PR #3, 15 Oct).
- Backend: new `/parse` endpoint so a problem is parsed once; grade contract added to `physics_mode_api.json`; 2 new CI checks (12 total).
- Added Claude as a fallback parser when Gemini is down.
- GitHub Actions to run `ci_check.py` on every pull request.
- Problem-input UI: text box, submit button, example problems, Solve/Tutor/Grade switch, loading state.
- Answer display: answer with badge, formula card used, assumptions, where each value came from in the problem, other candidate formulas, and a 'why' panel for the badge.
- KaTeX with a safe fallback when a formula can't be drawn.
- API client: request timeout, a message when the free Render server is slow to wake, clear error messages, a retry countdown when the rate limit is hit.
- Hint ladder and grade UI were planned for week 05; built early this week.

**What I tried, and what I expected**
- Expected most of the TypeScript frontend to already exist.
- Expected grade mode to be frontend-only work.

**Where it resisted, and what I did next**
- An audit showed most real work sat in the old `legacy/` JavaScript folder; the TypeScript structure was nearly empty. Rebuilt the missing pieces.
- Bugs found: badge label mismatch, a colour-contrast failure, hint ladder crashing on symbolic problems, and a risky text-to-symbol parse change that could give misread values a Verified badge.
- Grade backend bugs: feedback leaked the correct answer, partial answers marked correct, ungraded results not handled, quantities not asked for were required. Fixed in `grade_mode.py`.
- Claude fallback broke three times in a row: unsupported `temperature` parameter, an unhandled 'thinking' content block, a crash formatting symbolic values.
- Applying patches: wrong extraction folder; Vite proxy missing `/parse` (needed a dev-server restart); a test regex `/tension/` didn't match 'Tension'.
- Mixed engine/frontend/benchmark changes in one working tree → split them with `git add -p`.
- No repo-settings access, so Actions needed the manager to enable it.

**What Claude or another person contributed — accepted, changed, rejected**
- Claude wrote the TypeScript files, the grade backend fixes and patches, and diagnosed the three fallback bugs. I applied, tested and committed.
- Claude drafted two emails asking the manager to enable Actions; I sent one.
- I chose light mode only and had dark mode commented out.
- Claude assumed manager sign-off was needed; I corrected it: the manager gave me full control and wants the finished product.

**What I understand now, and what I still don't**
- Understand: correct answers stay hidden until the second wrong attempt, and this is enforced in a test.
- Open: misread text-to-symbol values could still earn a Verified badge.

**Evidence**
- https://github.com/jashshah127/humanitariansai/pull/2 (hint ladder), https://github.com/jashshah127/humanitariansai/pull/3 (grade mode)