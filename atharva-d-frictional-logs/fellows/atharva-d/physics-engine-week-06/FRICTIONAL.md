# Physics Engine — Week 06

## 2026-10-26 to 2026-11-01 — Diagrams for the golden set, integrated demo

Planned hours: 32 (Atwood diagram 10 and login 8 — both built in week 05; Harsh CI/CD coordination 4, regression pass 6, milestone 4) · Meetings: Mon 26 Oct, Thu 29 Oct (integrated demo)

**What I worked on**
- Diagrams for 14 of the 16 golden-set problems (was 2), drawn by code from engine-verified values only, no AI.
- Hint ladder now shows LaTeX instead of raw Python maths (`physics_mode.py` + new `MathText.tsx`), checked across all 28 cards.
- 29 Oct: integrated demo with real login shown at the Thursday meeting.
- Login integration finished: login, signup, reset-password pages, protected routes, old paste-a-token box removed.
- Confirmed with Harsh that pushes now build and deploy the frontend automatically through his CI/CD.
- Full regression pass across Solve, Tutor and Grade after login was added.
- State at end of week: backend endpoints `/solve`, `/parse`, `/grade` (login required), `/health`, `/cards`, `/stats`; 31 formula cards across 16 topics; 14 CI checks; 29 frontend test files.

**What I tried, and what I expected**
- Expected diagrams to be frontend-only work.
- Expected the hint LaTeX fix to work for every card once it worked for one.

**Where it resisted, and what I did next**
- Problems with values hidden in words ('a proton', 'Earth's mass', 'from rest', 'perpendicular') failed: the parser correctly leaves out constants, but nothing filled them in. Added a `NAMED_OBJECTS` table in `variable_glossary.py` that I fill from books, not AI.
- Symbol `I` meant both moment of inertia and current, so a wire-force problem failed. Widened the glossary entry.
- Checking all 28 cards showed the open-pipe and closed-pipe wave cards always clash: same required inputs.
- EM-001 and EM-002 (point charges) blocked on whether to track charge sign.
- Build failed from a file named `MathTest` instead of `MathText`; CI failed on Prettier until `npm run format`.
- I pushed to build all diagrams at once instead of the phased plan with physics review first.

**What Claude or another person contributed — accepted, changed, rejected**
- Claude wrote the diagram components and engine fixes and rendered previews to check label overlaps. I picked building new diagrams (option B) over only shipping the two that existed.
- Claude raised whether code-drawn diagrams break the no-AI rule. I clarified: code can draw them; AI can't supply the reasoning or answers.

**What I understand now, and what I still don't**
- Understand: the LLM only parses; every answer and diagram value comes from sympy/scipy.
- Open: Earth constants not filled in yet; charge-sign decision; pipe-card clash; hint LaTeX contract change not yet told to the manager.
- Open: none of the diagrams has been reviewed by a physicist.
- Open: milestone sign-off not yet recorded.

**Evidence**
- https://github.com/jashshah127/humanitariansai branch `feature-atharva` (diagrams committed 28 Oct, not yet in `main`)