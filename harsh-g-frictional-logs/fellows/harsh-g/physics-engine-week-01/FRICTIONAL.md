# Week 01 (2026-10-05 to 2026-10-11): getting up to speed and my own branch

*Written 2026-11-10, reconstructed from my plan of action, my dated work log, the CI run list, the commit history I remember, and my Claude chat history. Not written at the time.*

Planned: 32 hours. Meetings attended: 2 (Mon 5 Oct, Thu 8 Oct). Hours actually worked: not recorded.

## 1. What I worked on
- Read through the project files to understand the engine (a physics problem solver where the model only reads the problem and Python does the maths).
- Made my own branch, `feature-harsh`, starting from Atharva's `feature-atharva`.
- Looked at what pushing to GitHub needs (a token, and Jash adding me as a collaborator).

## 2. What I tried, and what I expected
- Tried: fetch the remote branches, create `feature-harsh` from `origin/feature-atharva`, pull in Atharva's work in PyCharm.
- Expected (from my plan of action for this week): clone the repo, run `ci_check.py` and confirm all 12 checks pass, and read the parser and scorer code in full.

## 3. Where it resisted, and what I did next
- A pull command failed because it was missing the remote name `origin`. Corrected it.
- Pushing needs authentication (a classic personal access token with repo scope; fine-grained tokens often fail against another account's repository) and Jash adding my GitHub account as a collaborator. Pulling and local branching did not. I found the number of steps frustrating for what felt like a simple task.
- Learned not to commit the `.idea` settings folder.
- The plan's week 1 checks, CI and staging tasks did not start this week; they were done from 19 Oct (weeks 03 and 04).

## 4. What Claude or another person contributed (accepted, changed, rejected)
- Claude summarised the project files and listed inconsistencies between the docs (card counts, benchmark results, golden-set size, a wrongly labelled slide file), and explained the Git and GitHub steps.
- I ran the commands myself. Accepted: Claude's correction of the pull command. Nothing else recorded as rejected or changed.

## 5. What I understand now, and what I still don't
- Understand now: pulling and branching are local; pushing needs a token and collaborator access.
- Not yet done or understood: the engine's checks, CI and staging. The plan put them in this week; they began on 19 Oct.

## Evidence
- Branch: [feature-harsh](https://github.com/jashshah127/humanitariansai/tree/feature-harsh)
- No linkable file for this week: the only record is my Claude chat of 2026-10-09 (not shared).
