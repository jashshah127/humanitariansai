# Week 04 (2026-10-26 to 2026-11-01): staging, the deploy gate, first evaluation runs

*Written 2026-11-10, reconstructed from my plan of action, my dated work log, the CI run list, the commit history I remember, and my Claude chat history. Not written at the time.*

Planned: 32 hours. Meetings attended: 1 (Mon 26 Oct). The Thursday 29 Oct meeting did not take place. Hours actually worked: 32 (my stated weekly hours, as in my mid-term report; not a logged figure).

## 1. What I worked on
- Built `physics-engine-staging` on Render and set it to deploy only after CI passes.
- Tested the gate with three commits, wrote staging as code (validated, not applied), and opened [PR #6](https://github.com/jashshah127/humanitariansai/pull/6) and [PR #7](https://github.com/jashshah127/humanitariansai/pull/7).
- Sampling plan, a 100-problem pilot and a 250-problem batch of the benchmark, a health-probe script and an overnight run, and a findings document.

## 2. What I tried, and what I expected
- Tried: a good commit, a deliberately failing commit, then a revert. Expected (from my plan of action): a dummy change deploys automatically, and the full pipeline works end to end.
- Tried: parse-accuracy runs on the real parser. Expected (from my plan of action): a number for the parser at scale, which had never been measured before; and uptime, error-rate and latency monitoring for the deployed engine.

## 3. Where it resisted, and what I did next
- The first Render service had no `JWT_SECRET`: `/health` said ok while every solve would return 401. Added it and later declared it in `render.yaml` ([PR #6](https://github.com/jashshah127/humanitariansai/pull/6)).
- Render never deploys a commit that has no checks, and CI only ran on pull requests. Hence a push trigger for `main` ([PR #7](https://github.com/jashshah127/humanitariansai/pull/7)).
- The parser's default model allows 20 requests a day on the free tier; evaluation runs use a model with 500 a day. This changed the sampling plan.
- The first batch stopped at 139 of 250 problems: the scorer crashed on a text value from the engine. Fixed and ran the rest separately.
- The engine answered 5 of 234 numeric problems and 3 of those were wrong, each with a Verified badge.
- Free instances sleep: a first request takes about 31 seconds. Overnight probe of staging: 21 of 21 healthy.
- Opening `/app` directly on staging returns `not found` (a known gap).
- Joint Milestone 1 demo was not held: the 29 Oct meeting did not take place.

## 4. What Claude or another person contributed (accepted, changed, rejected)
- Claude drafted the Render, CI and evaluation steps, the scripts (`monitor.py`, `run_sample.py` and others) and the documents. I ran them and pasted the real output.
- I decided to go ahead with staging without waiting for Jash. I suggested holding a push until the overnight probe finished, so a redeploy would not look like an outage, and Claude agreed.
- Nothing else recorded as rejected.

## 5. What I understand now, and what I still don't
- Understand now: a service can start and still be unusable (missing secret); deploys need a check that actually runs. Most declined problems are coverage gaps, not parser faults.
- Still unsure: whether the team's own live service has the same settings as mine; I can only see my own.

## Evidence
- [f064301](https://github.com/jashshah127/humanitariansai/commit/f064301) (good test commit)
- [809ca17](https://github.com/jashshah127/humanitariansai/commit/809ca17) (failing commit)
- [c1e4235](https://github.com/jashshah127/humanitariansai/commit/c1e4235) (revert)
- [dd3ecc2](https://github.com/jashshah127/humanitariansai/commit/dd3ecc2) and [474317f](https://github.com/jashshah127/humanitariansai/commit/474317f) (staging as code)
- [767ab33](https://github.com/jashshah127/humanitariansai/commit/767ab33) (evaluation tools)
- [df35f1b](https://github.com/jashshah127/humanitariansai/commit/df35f1b) (monitoring script and overnight results)
- [PR #6](https://github.com/jashshah127/humanitariansai/pull/6), [PR #7](https://github.com/jashshah127/humanitariansai/pull/7)
- [findings.md](https://github.com/jashshah127/humanitariansai/blob/feature-harsh/physics-engine/docs/findings.md)
- [sampling-plan.md](https://github.com/jashshah127/humanitariansai/blob/feature-harsh/physics-engine/docs/sampling-plan.md)
