# Physics Engine — Week 03

## 2026-10-05 to 2026-10-11 — New frontend plan, TypeScript setup, benchmark 0% investigation, research review

Planned hours: 32 (ci_check re-run 1, review inline frontend + API contract 3, IA 6, React/TS setup 4, design system 8, base components 10) · Meetings: Mon 5 Oct, Thu 8 Oct

**What I worked on**
- New frontend plan of action started 5 Oct.
- Wrote the information architecture (`frontend-ia.md`): pages, routes, components, and a keep/replace call for existing code.
- Set up Vite + TypeScript; design tokens (brand colour `#871919`, Inter font from the Humanitarians AI site); Button, Input, Card, VerificationBadge with tests; a `/design` preview page (committed 13 Oct).
- Investigated a 0% benchmark result; built `diag_results.py` and `ollama_probe.py` to test single problems fast.
- Prepared a script for a meeting with the professors about API costs and local models.
- Reviewed 9 research papers from the manager against the code.
- Re-ran `ci_check.py` on the new frontend setup: 12/12 passed.
- Reviewed the old inline page in `server.py` and the full `/solve` and `/grade` contract in `physics_mode_api.json`; listed what to keep, what to replace, and 7 backend blockers for the new frontend.
- Tooling: TypeScript, ESLint, Prettier, Vitest.

**What I tried, and what I expected**
- Expected a 200-problem benchmark run to give a real accuracy number.
- Expected local models (Ollama) to be a quick free swap for Gemini.
- Expected a 'past student mistakes' feature to be new work.

**Where it resisted, and what I did next**
- 6 Oct: 200-problem run gave 0% on both Gemini and Ollama. Not an engine result: Gemini quota was used up, and Ollama returned HTTP 500 (model not pulled; later, a model-manifest access error).
- `run_benchmark.py` counted parse failures as wrong answers, which corrupted the accuracy number. Rewrote the scoring.
- Golden set through local models: llama3.2 9/16, qwen2.5:7b 7/16. Causes: the prompt never said 'perpendicular' = 90°, and `q` vs `Q` confusion.
- I reported Gemini at 81.6%. That is impossible on 16 problems (only multiples of 6.25%). It came from a different metric. My 16/16 'perfect' score came from `demo.py`/`ci_check.py`, which use hand-typed inputs and no AI parsing at all.
- Found the glossary matched names without case: radius `b` could become magnetic field `B`, giving a wrong answer marked Verified. Fixed (case-sensitive for short names). Also: JSON repair for LaTeX backslashes, `parse.py` accepting symbolic values, fixed seed for Ollama.
- After fixes, qwen2.5 parsing rose from 18 to 23 of 26 attempted problems, with 0 wrong answers. Blocker is missing formula cards, not parsing.
- Measured the real parse prompt (~1,700 tokens) for a cost estimate: paid Flash was enough; Pro was not justified by any bottleneck.
- The mistakes feature already partly exists in `grade_mode.py`, and using real student data would need IRB review. Stopped calling informal chats with high schoolers a 'survey'.
- Explorer cluster can run batch benchmarks but cannot serve live traffic.
- TypeScript setup: `Card.tsx` type clash on `title`, two empty test files, stale Python processes on port 8000, `localhost` vs `127.0.0.1` on Windows. Accidentally staged IDE files with `git add -A`; unstaged them.

**What Claude or another person contributed — accepted, changed, rejected**
- Claude diagnosed the 0% runs, wrote both diagnostic scripts, the glossary/parse/benchmark fixes, the token file and base components. I recreated the frontend files by hand and ran everything locally.
- Claude built a 12-slide PowerPoint I had not asked for. I rejected it and asked for a reusable prompt file instead.
- Claude flagged that my draft email to the manager was wrong (it said parsing, not coverage, was the problem). I accepted the correction and asked for a plain-language rewrite, since the physics version went over my head.
- Claude corrected its own baseline (18, not 17 of 26). I accepted.

**What I understand now, and what I still don't**
- Understand: the AI only parses text into values; SymPy does all solving. But a wrong parse can still pass every check and get Verified.
- Understand: I kept switching models or rerunning before finding why the last run failed. That cost hours.
- Open: formula cards are picked only by variable names, never by when they apply (e.g. 'solid sphere, not shell'). This threatens the 'Verified' claim as cards grow.
- Open: asked the manager for someone with physics knowledge to own card content. I can't own that part.

**Evidence**
- https://github.com/jashshah127/humanitariansai: `eval/run_benchmark.py`, `eval/diag_results.py`, `eval/ollama_probe.py`, `engine/variable_glossary.py`, `frontend-ia.md`, `frontend/src/design-system/`