# Week 07 (2026-11-16 to 2026-11-22): checking main, the cache branch, dependency scan (in progress)

*Written 2026-11-16 during the week, from my work log and my Claude chat. The week is not finished.*

Planned: 32 hours. Meetings attended so far: none recorded yet. The Mon 16 Nov meeting is at 4 PM EST. Hours actually worked so far: not recorded.

## 1. What I worked on
- Checked `main` after Atharva merged Shailly's PR #9 on 15 Nov. The live service is healthy and the Atwood example solved. Its log shows only health checks. The new problem log stays off until a server secret key is set, so no student text is being stored.
- Rebuilt the parse cache on top of the new `main` as its own branch, `add-parse-cache`.
- Ran dependency scans: `pip-audit` and `npm audit --omit=dev` both found nothing. Wrote a report-only scan as a GitHub workflow (`dependency-audit.yml`, in this folder). Not yet pushed or run.
- Checked whether I have access to the Supabase project. I do not.

## 2. What I tried, and what I expected
- Tried: copy three files from my branch onto a new branch cut from `main`. I expected a clean change of three files.
- Tried: the dependency scans. Expected (from my plan of action for week 7): dependency vulnerability scanning in CI.
- Tried: check my Supabase access. I had answered "supabase" when Claude asked what kind of access Shailly had given me, but I had not actually received it. Claude then built a plan on that answer; I corrected it when I realised.

## 3. Where it resisted, and what I did next
- The diff stat for the copied files showed 429 deleted lines. `main` had moved, so those copies were older than what is merged, and committing them would have removed others' work. Nothing was committed. I reset the branch to `origin/main` and applied the cache again as a small patch on top of `main`: `server.py` 15 lines, `ci_check.py` 137 lines added, one new file. All checks pass.
- Atharva asked me to hold the cache pull request while he adds tests to `ci_check.py`, which my change also edits. The cache stays on its own branch until his tests are in `main`, then I re-apply the patch.
- The backups task needs access to Shailly's Supabase project. I compared the project my app uses against the projects I can see in my Supabase account, and could not confirm I can see it. I asked Claude not to message Shailly about it until I had checked on my side.
- A command failed because my terminal was still inside the `frontend` folder, so a relative path pointed to the wrong place. Now I run `Get-Location` first.

## 4. What Claude or another person contributed (accepted, changed, rejected)
- Claude read `main`'s `_llm()` function from my paste, rebuilt a test copy shaped like it, adapted the patch, and wrote the scan workflow. I applied the patch and read the diff myself.
- Claude also gave me wrong instructions earlier in the day (copying whole files); the diff stat caught it.
- I stopped Claude when it moved ahead of me on the dependency scan and asked it to explain what the file was for and why before going on. I chose to update my records first.
- Atharva: the 2-day review rule, and the request to hold the pull request. I accepted both.

## 5. What I understand now, and what I still don't
- Understand now: others can merge into `main` at any time, so I check `main` and read the diff before building on it. A dependency scan only reports known flaws, and today it found none.
- Still unsure: when Atharva's tests will land and whether they will conflict; how I get access to the Supabase project; whether the problem log should store any student text at all, and how it is explained to students.

## Evidence
- [9ab3c09](https://github.com/jashshah127/humanitariansai/commit/9ab3c09) (the cache on `add-parse-cache`, no pull request)
- [40b57bf](https://github.com/jashshah127/humanitariansai/commit/40b57bf) (Atharva's merge of PR #9)
- `dependency-audit.yml`, in this folder
