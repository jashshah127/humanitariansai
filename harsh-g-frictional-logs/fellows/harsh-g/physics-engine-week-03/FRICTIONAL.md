# Week 03 (2026-10-19 to 2026-10-25): first checks, baseline and CI

*Written 2026-11-10, reconstructed from my plan of action, my dated work log, the CI run list, the commit history I remember, and my Claude chat history. Not written at the time.*

Planned: 32 hours. Meetings attended: 2 (Mon 19 Oct, Thu 22 Oct). Hours actually worked: 32 (my stated weekly hours, as in my mid-term report; not a logged figure).

## 1. What I worked on
- Ran the engine's own checks (`ci_check.py`, all passing) and read the parser, scorer and benchmark code.
- Checked that CI runs on pull requests (merged [PR #4](https://github.com/jashshah127/humanitariansai/pull/4), a `.gitignore` fix).
- First baseline: a plain model (no tools) on the 16-problem golden set.
- Wrote an infrastructure-as-code research note (Render Blueprint for the engine; Terraform for the rest).
- Merged Atharva's branch into `feature-harsh` and pushed it (date not recorded).

## 2. What I tried, and what I expected
- Tried: baseline run with the original scorer, then rescored by value and by asked quantities only.
- Expected (from my plan of action): the first "plain LLM vs. engine" number, which had never been produced before; and CI running `ci_check.py` on every pull request.

## 3. Where it resisted, and what I did next
- The baseline scored 3 of 16 under the original scorer. Reading the outputs showed it rejected correct answers over naming, intermediate quantities and units. Rescored: 11 of 16 by value, 15 to 16 of 16 on asked quantities. The third rule was chosen after seeing the results, and the document says so.
- About 90 frontend files showed as modified after switching branches (line endings and a rebuilt `dist/`). I confirmed with `git diff --ignore-cr-at-eol` that nothing real had changed, then restored them.
- `git add .` would have staged `frontend/.env.local` on branches cut from `main`, so I stage files by name.
- A key and a token were pasted into a chat at some point between 19 and 27 Oct (weeks 03 and 04). The key was replaced; I stopped pasting secrets.

## 4. What Claude or another person contributed (accepted, changed, rejected)
- Claude wrote the scoring and rescoring scripts, the methodology and the research notes from the output I pasted back. I ran everything and checked the numbers against the files.
- Claude pointed out that the third scoring rule was chosen after seeing results; I kept that caveat in the document.
- Nothing else recorded as rejected or changed.

## 5. What I understand now, and what I still don't
- Understand now: a low score can come from the scorer and not the system. The baseline run date (about 19 Oct) is inferred, not logged.
- Still unsure: how much the plain-model baseline says about the parser on harder problems.

## Evidence
- [PR #4](https://github.com/jashshah127/humanitariansai/pull/4)
- [baseline-methodology.md](https://github.com/jashshah127/humanitariansai/blob/feature-harsh/physics-engine/docs/baseline-methodology.md) (the final version is dated 28 Oct)
- [iac-research.md](https://github.com/jashshah127/humanitariansai/blob/feature-harsh/physics-engine/docs/iac-research.md)
