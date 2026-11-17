# Week 05 (2026-11-02 to 2026-11-08): taxonomy, merging to main, the mid-term report

*Written 2026-11-10, reconstructed from my plan of action, my dated work log, the CI run list, the commit history I remember, and my Claude chat history. Not written at the time.*

Planned: 32 hours. Meetings attended: 1 (Mon 2 Nov). I did not attend the Thu 5 Nov meeting. Hours actually worked: 32 (my stated weekly hours, as in my mid-term report; not a logged figure).

## 1. What I worked on
- Error taxonomy: sorted 234 numeric problems by why they were declined (22 read by hand).
- Merged [PR #7](https://github.com/jashshah127/humanitariansai/pull/7) and [PR #6](https://github.com/jashshah127/humanitariansai/pull/6) (3 Nov) and Atharva's [PR #8](https://github.com/jashshah127/humanitariansai/pull/8) (4 Nov) into `main` through the CI gate, after testing his branch on staging.
- Read Shailly's backend infrastructure document (she gave it to me earlier; I shared it with Claude on 4 Nov) and checked her pull request #9: CI green, not yet tested on staging or merged.
- Built and sent the mid-term report (4 Nov).

## 2. What I tried, and what I expected
- Tried: add the Supabase settings to my `main`-tracking service before the merge, switch it to deploy after CI, merge in order #7, #6, #8. Expected (from my plan of action): confirm Atharva's frontend auto-deploys cleanly through the pipeline.
- Tried: look at Shailly's backend work through the same pipeline. Expected (from my plan of action): confirm her Supabase backend deploys through the same pipeline.
- Tried: sort the declined problems into groups. Expected (from my plan of action): an error-analysis taxonomy from the parse-accuracy results.
- Tried: test Atharva's value-table commit on a local branch before taking it. Expected: nothing recorded.

## 3. Where it resisted, and what I did next
- 77% of numeric problems are coverage gaps or poor card fits, so a prompt change cannot reach them.
- My `main` service had only two variables; sign-in would have worked and solves failed. Added the other two before merging.
- A probe of an old address returned 404 and told me nothing about the live service.
- The merge message opened in an editor I did not know how to leave (`Esc`, then `:wq`).
- I asked Claude to change document dates to the plan's. Claude declined, since a date records when work happened. I kept the real dates and the report shows the plan week beside the real completion date.
- Shailly's pull request #9 needs her confirmation that the branch is final and a new Render secret; her branch changed three times in a day, so I did not test it yet.
- After the merges, the live site showed the sign-in page, the Atwood example solved with its diagram, `/health` ok, and an invalid token got a 401.

## 4. What Claude or another person contributed (accepted, changed, rejected)
- Claude proposed the merge order, the checks before it, and drafted the report, the cover emails and the work-log entries. I ran every command and pasted the output.
- Accepted: the order and the checks. Changed: the meeting count (kept two a week), a sentence about a teammate's findings (removed), the long email (replaced by a short one), and the dates for one report row (removed). Rejected: taking Atharva's newer code into my branch before testing it.

## 5. What I understand now, and what I still don't
- Understand now: a merge to `main` is a deploy, so the checks come first.
- Still unsure: whether the team's own live service deployed #8 and has the three variables; whether new sign-ups work (the live address may not be in Supabase's redirect list).

## Evidence
- [PR #6](https://github.com/jashshah127/humanitariansai/pull/6), [PR #7](https://github.com/jashshah127/humanitariansai/pull/7), [PR #8](https://github.com/jashshah127/humanitariansai/pull/8)
- [d1fee32](https://github.com/jashshah127/humanitariansai/commit/d1fee32) (documents and analysis scripts, 3 Nov)
- [error-taxonomy.md](https://github.com/jashshah127/humanitariansai/blob/feature-harsh/physics-engine/docs/error-taxonomy.md)
- Mid-term report: sent to my manager on 4 Nov. It is not included in this public folder.
