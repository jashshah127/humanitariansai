# Week 01 · 2026-10-05 to 2026-10-11 · Onboarding (plan Week 1)

*Written 2026-11-10, reconstructed from my plan of action, mid-term report, commit history, my dated findings log, my chats with Claude and my own account of this week. Not written at the time.*

**Planned:** 32 hours (plan Week 1: run ci_check, explore Supabase, read event_log/formula_kb, design schema, research structured output, pipeline plan, dev setup). **Meetings:** 2 (Mon 5 Oct, Thu 8 Oct).

**Plan for this week** (from my mid-term report; hours are plan estimates):

| Planned task | Hours | Status | Done in |
|---|---|---|---|
| Run `eval/ci_check.py`, confirm all checks pass | 1 | Complete, 13 Oct | week 02 |
| Set up a Supabase project; explore Auth, Database, pgvector | 6 | Complete, 13–14 Oct | week 02 |
| Read `event_log.py` and `formula_kb.py` topic/subtopic fields | 3 | Complete | weeks 02–03 |
| Design the schema: users with roles, de-identified `problems_log` | 8 | Complete, 15–22 Oct | weeks 02–03 |
| Research structured-output approaches for tagging | 6 | Complete, 14–15 Oct | week 02 |
| One-page plan for the classification pipeline | 5 | Complete, 22 Oct | week 03 |
| Local dev environment and the Supabase CLI | 3 | Complete, 15 Oct | week 02 |

**Before week 01** (from my report): start date 24 Sept; project work began the following week. Meetings held before week 01: Thu 24 Sept, Mon 28 Sept, Thu 1 Oct.

> This week was getting started: cloning, reading the repository and setting up my environment (my own account). My findings log and commits start on 13 Oct (week 02), and the plan Week 1 tasks in the table were completed in weeks 02–03.

## 1. What I worked on
- 8 Oct: cloned the project repository (`jashshah127/humanitariansai`) to my laptop (git history).
- Read through the repository to understand the project.
- Set up my development environment for the project.

## 2. What I tried, and what I expected
- Tried: reading the repo end to end and getting it set up on my laptop before starting my own tasks.
- Expected: to understand how a problem goes from text to a verified answer, and where my backend work (sign-in, data, AI tagging) would fit.

## 3. Where it resisted, and what I did next
- No setup problems recorded this week. The first ones I logged came in week 02 (for example, Supabase test users failing with `email_not_confirmed`).

## 4. What Claude or another person contributed — accepted, changed, rejected
- Got details about the repository from Jash Shah (manager) when I needed them.
- No help from Claude this week; my work sessions with Claude start on 13 Oct.

## 5. What I understand now, and what I still don't
- How the engine works: AI only reads the problem; Python (sympy) solves it with a matching formula card; every answer is labelled Verified, Needs Review or Unverified.
- The server uses only Python's standard library, and the engine has 31 formula cards, each with a topic and subtopic.
- Still unclear: how sign-in, the problem log and the AI tagging would plug into the existing server. Worked out in weeks 02–03.

## Evidence
- Repository: https://github.com/jashshah127/humanitariansai (cloned 8 Oct)
