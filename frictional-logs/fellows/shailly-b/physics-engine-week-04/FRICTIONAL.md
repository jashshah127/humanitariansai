# Week 04 · 2026-10-26 to 2026-11-01 · Medhavy infrastructure documentation

*Written 2026-11-10, reconstructed from the medhavi-hub pull request, my mid-term report, plan of action and my chats with Claude. Not written at the time.*

**Planned:** 32 hours (plan Week 4: API contract, regression pass, coordinate with the frontend and CI/CD teammates, Milestone 1 demo). **Meetings:** 2 (Mon 26 Oct, Thu 29 Oct). Medhavy documentation: 8–10 hours, my own estimate (given on 4 Nov).

**Plan for this week** (from my mid-term report; hours are plan estimates):

| Planned task | Hours | Status | Done in |
|---|---|---|---|
| Document the login/signup API contract for the frontend | 6 | Complete, 3 Nov | week 05 |
| Full regression pass on auth and classification | 6 | Complete, 3 Nov | week 05 |
| Coordinate with the frontend teammate: wire his login UI to this backend | 6 | Complete, 4 Nov (local test; joint session pending) | week 05 |
| Coordinate with the CI/CD teammate: confirm this runs through his pipeline | 4 | Complete, 4 Nov (PR #9 CI passes) | week 05 |
| MILESTONE 1: live integrated demo | 10 | Partly (works locally; team demo pending) | week 05 |

**Additional work this week** (from my report): Medhavy infrastructure documentation with Gaurav Bakale, 8–10 hours, PR #19 merged 26 Oct (details below).
The plan Week 4 tasks were done in week 05 (3–4 Nov), not this week.

## 1. What I worked on
- Medhavy (separate from the Physics Engine), with Gaurav Bakale: infrastructure reference `docs/overall_infrastructure.md` in Medhavy/medhavi-hub. Covers AWS servers and deployment, Supabase, Clerk login, other services.
- Changes requested in review: removed all usernames, passwords and other credentials, every blank placeholder, and the Risks section.
- Branch `docs/overall-infrastructure` from `development`; PR #19 into `development`, merged 26 Oct.
- My time (estimate): about 2 h understanding the platform and talking to Gaurav, 4–5 h reading, 2–3 h writing and revising.
- Physics Engine: attended the team meetings on Mon 26 Oct and Thu 29 Oct; the integrated demo with real login was shown on 29 Oct (from my report's meeting table).
- No other Physics Engine work recorded for 27 Oct – 1 Nov: no commits and no findings-log entries.

## 2. What I tried, and what I expected
- Tried: turning my infrastructure notes into a reference the whole team could use. Expected it to be usable without exposing any credentials.

## 3. Where it resisted, and what I did next
- Some facts in my draft didn't match the `development` branch (number of servers, auto-deploy, the Electron Microscopy app's port). Corrected them against the repo before the PR.

## 4. What Claude or another person contributed — accepted, changed, rejected
- Gaurav Bakale walked me through the setup and asked for the credential, blank and Risks-section changes.
- Claude helped remove the credentials and blanks, check facts against `development`, and create the branch and PR. I wrote the original draft and reviewed the changes before they were pushed.

## 5. What I understand now, and what I still don't
- How Medhavy runs: separate dev and prod servers on AWS; merging to `development` auto-deploys dev, merging to `main` deploys prod; Supabase for data; Clerk for login.
- Medhavy's team workflow: branch from `development`, named `docs/…`, `feat/…` and so on, and every change goes through a PR.
- Still open: nothing recorded.

## Evidence
- Medhavy PR: https://github.com/Medhavy/medhavi-hub/pull/19
