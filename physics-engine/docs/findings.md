# Findings So Far: Evaluation, Pipeline and Deployment

**Author:** Harsh Gujarathi · **Plan item:** Wk 3, document findings so far
**Status:** Draft v2, Oct 29, 2026 (v1 written Oct 28) · **Audience:** Sri, Nik, Jash

No dataset text appears in this document. Problems are referred to by ID.

## 1. Summary

1. **The engine answered 5 of the 234 numeric problems it was tried on (2.1%), and 3 of those 5 were wrong.** All three wrong answers carried the "Verified - solved symbolically" badge. The verification checks the solver, not whether the right card was chosen or the inputs were read correctly.
2. **Most numeric problems stop before an answer.** Of 234: 55% have a card that fits the unknown but the quantities do not close, 26% have no card, 17% had no unknown found.
3. **A hand reading of 11 numeric declines found mostly coverage gaps, not parser faults:** 5 coverage, 2 not solvable from the text, 4 parser or glossary related.
4. **On the 16 golden-set problems, a small free LLM with no tools got every quantity right when graded fairly.** The golden set does not separate the engine from a plain LLM on correctness.
5. **The deploy pipeline works on staging:** a good commit deploys after CI passes, a failing commit does not deploy.
6. **The parser's default model allows 20 requests a day on the free tier.** Both deployed services use it, so a demo could run out.
7. **Overnight monitoring of staging: 21 of 21 probes healthy, no errors.** Most probes found the free instance asleep, and the first answer took about 31 seconds (21 to 51 seconds).

## 2. Evaluation of the parser and engine at scale

### Setup
- Benchmark: UGPhysics, Classical Mechanics and Classical Electromagnetism, 1,226 problems.
- 305 are skipped before any model call (258 with no readable number, 47 true/false or multiple choice). **921 are attemptable**: 234 numeric and 687 symbolic. The numeric stratum is 224 problems with fully numeric answers plus 10 whose answer mixes a number and an expression.
- Parser model for all runs: `gemini-flash-lite-latest` (free tier, 500 requests a day). The parser's code default is `gemini-3.6-flash`, which allows only 20 a day, so it could not be used at this scale. **Results describe Flash Lite, not the default model.**
- Runs: a 100-problem pilot (26 numeric, 74 symbolic), then a batch of 250 (all 234 numeric plus 16 symbolic). Plan and tools: `docs/sampling-plan.md`.
- Parse accuracy is measured indirectly. The benchmark has no correct parse to compare against, so the signals are parse success, end-to-end answer rate, and the reasons problems were declined.

### Results
Batch of 250 (no API failures, no parse failures):

| Outcome | Numeric (234) | Symbolic (16) |
|---|---|---|
| Declined, missing knowns | 129 (55%) | 4 |
| Declined, no card | 61 (26%) | 7 |
| Parsed, no unknown found | 39 (17%) | 5 |
| Answered, matched | 2 (0.9%) | 0 |
| Answered, wrong | 3 (1.3%) | 0 |

Pilot (100 problems): 1 answered (wrong), 29 no unknown, 23 no card, 46 missing knowns, 1 bad output.

- **No accuracy figure is reported.** Five compared problems say nothing about a rate. The finding is the count of wrong answers and the breakdown of declines.
- 13 of 250 parses needed a JSON or LaTeX repair (5%). Only 5 of 201 declines used variable names outside the glossary.
- **Run-to-run variation:** 28 problems appear in both the pilot and the batch, and 25 had the same outcome (89%). The other 3 changed decline reason; none moved between answered and declined. Most of these are declines, so the agreement is partly built in.
- The symbolic stratum was only sampled (at most 90 of 687, from the pilot and the 16 in the batch). It cannot be scored for accuracy until the symbolic comparison path (antlr4) is validated.

### The three wrong answers
All three are real engine errors, checked by hand.

| Problem | What went wrong | Engine → benchmark |
|---|---|---|
| ClassicalMechanics-1565 | The parser kept one of two balls and dropped the meeting condition. A single-projectile card answered with that ball's full range | 8.49 m → 2.8 m |
| ClassicalMechanics-1583 | The wave number given per centimetre was converted the wrong way (0.0157 per metre instead of 157), so the wave speed was 10,000 times too large. Also, the benchmark answers in cm/s while the engine reports metres per second | 6,000 m/s → 60 (cm/s) |
| ClassicalMechanics-1637 | The parser dropped the condition on the damped frequency. The critical-damping card answered | 8 → 4 |

**The verification badge's scope.** "Verified - solved symbolically" means the answer satisfies the chosen card's own equations and is positive. A wave speed of 6,000 m/s, more than 17 times the speed of sound, passed. The wording may overstate what is checked.

### Why numeric problems were declined (hand reading of 11)
| Kind | Count | Examples (IDs) |
|---|---|---|
| Coverage: no card for the physics | 5 | EM-182 (ring), MECH-1798 (fluid velocity field), 2247, 2398, 2762 |
| Not solvable from the text (depends on a figure or an earlier part) | 2 | EM-405, MECH-2357 |
| Parser or glossary related | 4 | MECH-1566, 1643, 1665, 2014 |

Parser and glossary issues seen: the glossary names the central body's radius `Re` while the escape-velocity card needs `R` (a solvable problem declined, and by hand the card would give 2,374.6 m/s against the benchmark's 2.37 × 10³); coefficients inside a wave equation were not extracted; an observer at rest was not given as a zero speed; and a source "moving away" was given a positive speed. **Defaulting an unstated observer speed to zero would then expose the sign problem**: with the parser's +10 m/s the Doppler card gives 1,031 Hz against the correct 971 Hz.

This is a sample of 11 from one batch, so it is indicative, not a rate.

## 3. The 16-problem baseline

A plain LLM (`gemini-flash-lite-latest`, no tools) was scored on the golden set. Details: `docs/baseline-methodology.md`.

| Rule | Result |
|---|---|
| Strict (names must match) | 3/16 (18.8%) |
| By value (names ignored) | 11/16 (68.8%) |
| Asked quantities only (judged by hand) | 15/16 to 16/16 |

The strict result was dominated by a scoring artifact: the model wrote descriptive names and the scorer could only read single-word names and plain numbers. No final-answer value the model gave was wrong. The asked-only rule was defined after seeing the results. The engine's own 16/16 on the same set is not independent evidence, because the engine's CI check runs these problems.

## 4. Deployment and pipeline findings

- **CI-gated deploys work on staging.** Render's "After CI Checks Pass" deployed a good commit (CI run 12), did not deploy a failing one (run 13 failed at the type check), and deployed the revert (run 14).
- **A commit with zero checks is never deployed.** CI ran only on pull requests, so each tracked branch needed a `push` trigger. Done for `feature-harsh`. For `main` it needs PR #7, which is open.
- **A healthy `/health` does not mean a working service.** The first Render service had no `JWT_SECRET`, so every solve would have returned 401 while `/health` said ok. PR #6 declares it in `render.yaml`.
- **The frontend reads the Supabase settings at build time**, so each environment needs its own build and the committed `dist/` cannot serve two environments. Building on Render during deploy works on the free plan.
- **Free-tier limits:** 750 free instance hours a month shared by all free services; a service sleeps after 15 idle minutes. Measured cold start on the older service: 62 seconds.
- **The server answers HEAD requests with 501**, so a monitor that pings with HEAD would report a healthy service as failing.
- The staging service is described by a validated Blueprint (`infra/staging/render.yaml`, not applied) with a recreation guide.
- `ci_check.py` runs 14 checks, all passing.

### Monitoring
A health, latency and known-answer probe (`eval/monitor.py`) was run against both services. For staging it ran overnight: one probe every 30 minutes, 20 probes after a first test probe, from 8:19 PM to 6:03 AM local time.

| Measure (staging, `/health`) | Result |
|---|---|
| Probes | 21 |
| Uptime (healthy / probes) | 21/21 = 100% |
| Error rate | 0% |
| Latency, median / 95th percentile / max | 31.3 s / 51.3 s / 51.3 s |
| Probes over 10 seconds | 19 of 21 |
| The two fast probes | 239 ms and 320 ms |

- **What the latency is.** Free instances sleep after 15 idle minutes, and the probes were 30 minutes apart, so 19 of 21 woke a sleeping service. The latency is therefore mostly the **cold-start time**: 21 to 51 seconds, typically about 31. The two fast probes (239 and 320 ms) are the awake response, from the minutes after earlier use. A single probe on the older service earlier took 62 seconds.
- **What it does not show.** Only `/health` was checked, so this is uptime of the web process, not of solving. The known-answer solve check was not part of the overnight run, because each solve uses one of the 20 daily requests on the default parser model. Server-side error rate and latency under load are not measured.
- The overnight probes also used a small part of the 750 shared free instance hours.

## 5. Recommendations

1. **Narrow or reword the "Verified" badge**, and consider a guard that declines when a stated number or condition is never used, or when an answer has an implausible magnitude. This is a hypothesis; it would not have caught every wrong answer above (1583 used its numbers, wrongly).
2. **Make the parser's model a setting** and use a Flash Lite model on staging and for the demo, or use a key with billing. This also tests whether Flash Lite is good enough to switch to.
3. **Glossary and prompt fixes, each with a check against a wrong answer:** a radius name for any body, read coefficients from a stated equation, and imply a zero speed only with a sign check.
4. **Treat coverage as the main limit.** Most numeric problems need a card the library does not have, or a chain of two cards.
5. **Use a harder problem set for any comparison with a plain LLM.** The 16-problem golden set does not separate them.

## 6. Limitations

- One parser model (Flash Lite), one batch, one pilot; parser output varies between runs.
- Hand readings cover 11 declines and 3 wrong answers, not every problem.
- The symbolic stratum is mostly unmeasured.
- Google's usage page showed no requests although the key had been used, so the daily limits are taken from the quota page, not confirmed by observed exhaustion.
- Parse quality of the default model (`gemini-3.6-flash`) was not measured.

## 7. Next

Run the known-answer solve check once, make the parser model a setting on staging, decide how monitoring is scheduled and where alerts go, and bring the three wrong answers and the cold-start numbers to Thursday's meeting. The monitoring script and the overnight results are committed (commit `df35f1b`).
