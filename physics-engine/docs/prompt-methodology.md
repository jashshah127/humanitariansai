# Prompt-Engineering Methodology and A/B Results

**Author:** Harsh Gujarati · **Plan item:** Wk 5, A/B test parser prompt improvements and write up the methodology
**Status:** Draft v1, 9 November 2026 · **Audience:** Jash, Atharva, Shailly
No dataset text appears in this document. Problems are referred to by ID.

## 1. Question

Can a change to the parser prompt (`PARSE_PROMPT`) make the engine answer more problems correctly without making it answer more problems wrongly? A wrong answer with a Verified badge is worse than a decline, so wrong answers are counted first.

## 2. Setup

- **Test set:** 85 numeric problems from the UGPhysics benchmark (`eval/sample/ids_ab.txt`, IDs only), built by `eval/make_ab_set.py`: the 5 problems already answered (to catch regressions), 9 with a wave equation, 15 with an implied zero ("at rest"), 29 that mention a named object (proton, Earth, perpendicular, from rest), 18 one quantity short of an answer, and 20 random controls (groups overlap).
- **Parser model:** `gemini-flash-lite-latest`, temperature 0, 85 requests per run, about 10 minutes.
- **Prompt variants** are text files in `eval/prompts/`, run with `eval/run_variant.py` without editing the shared `engine/parse.py`. Each variant differs from the control by one added rule, and a fingerprint of the prompt is printed with every run.
- **Comparison tools:** `compare_runs.py` (two runs), `multi_compare.py` (a variant against several controls, and a stability table), `compare_injected.py` (where a value table fired), `guard_check.py` and `guard_check2.py` (offline guards).

## 3. Rules adopted

1. **Fix the code.** Record which commit a run used. The control must run on the same code as the variant. (See section 5.)
2. **Run the unchanged prompt more than once.** The same prompt and code do not give the same result twice (section 4).
3. **A new wrong answer** is one that is wrong in the variant and was never wrong in a control. **A lost right answer** is one that was right in every control and not in the variant. A variant passes only with none of either.
4. **Run each variant twice.**
5. **Report answered, right and wrong counts,** never an accuracy figure over five or twelve answered problems.

## 4. Noise

Three runs of the unchanged prompt and code (the batch, `v0`, `v0b`) gave 5, 5 and 6 answered problems, with 3 wrong each time, but **64% to 76% of problems had an identical outcome across runs, and only 3 of the 7 problems that were ever answered gave the same result every time.** The Doppler problem ClassicalMechanics-1665 was answered wrongly in one run (the parser wrote a source speed of +10 and the answer was 1,031 Hz) and rightly in another (−10, 971 Hz). One run cannot judge a change.

## 5. A confound found along the way

The `v2` runs were made after Atharva's value-table commit was merged into the branch, and the controls `v0` and `v0b` were made before. Comparing against them mixed the prompt change with his code change. The matching control is `named1`, which ran his commit with the unchanged prompt. **Always rerun the control after any code change.**

## 6. Variants and results

| Run | Code | Prompt | Answered | Right | Wrong | Note |
|---|---|---|---|---|---|---|
| batch, `v0`, `v0b` | before the merge | unchanged | 5, 5, 6 | 2, 2, 3 | 3, 3, 3 | Controls |
| `named1` | with Atharva's table | unchanged | 7 | 3 | 3 | 1 answered but not comparable. The table filled a value on 7 of 29 relevant problems; no new wrong answer attributable to it |
| `v1` | before the merge | decline when a quantity has more than one value | 4 | 2 | 2 | "No unknown found" rose from 10 to 25, one parse failure |
| `v2a`, `v2b` | with Atharva's table | apply the glossary sign convention; "at rest" is 0 | 12, 12 | 6, 6 | 6, 6 | See below |

**`v1` (decline on conflicting values).** Fixed one of three target problems (1565), left 1637 and 1744 wrong even though the rule named a perigee and an apogee as its example, over-triggered, and added a parse failure because the model began reasoning aloud in its notes. Not adopted. A model instruction is not a reliable control.

**`v2` (sign convention, at rest is 0), judged against `named1`.** Both runs gave the same verdict:
- **New right answers, in both runs:** 1583 (the wave unit problem), 1665 (the Doppler sign problem) and 2239.
- **New wrong answers, in both runs:** 2310 and 2761. **Flicker:** 1632 in one run and 2210 in the other.
- **Lost right answers:** none.
- **Verdict: fails the rule.** The rule makes the parser fill in more values, so the engine answers more problems, right and wrong.

**Causes of the new wrong answers.** In 2310 the engine answered the original orbit radius and ignored the stated energy loss; the problem gives only an altitude, and Earth's mass and radius came from the value table. In 2761 the engine used the two-mass pulley card and ignored the slope angle and the radius. In 2210 (an echo problem asking for a beat frequency) the card gives a single Doppler shift.

## 7. Guards tested offline

Both tests use saved results only, with no model calls.

- **Guard 1, an unused number in the problem text** (`guard_check.py`): on the two `v2` runs it would decline 7 of 12 wrong-answer rows and none of 12 right-answer rows.
- **Guard 2, a parsed quantity the chosen card does not use** (`guard_check2.py`, with the wave amplitude ignored): 6 of 12 wrong rows and none of 12 right rows. It catches 2310 (the energy-loss quantity) and 2761 (the angle and radius). It also flags the satellite mass in 1744, which is a distractor, so it is right for the wrong reason there.
- **Together, by problem:** they would decline 1565, 1637, 1744, 2310 and 2761 (5 of 7 wrong problems) and none of the 6 right ones. They would not catch the two flickering wrong answers, 1632 and 2210.
- **A hypothesis, not a result:** `v2` with both guards would answer 6 problems right and 1 wrong per run, against 3 right and 3 wrong for the control.

## 8. Conclusions

1. **A prompt rule can unlock right answers and wrong ones together.** `v2` found three reliable new right answers, among them the Doppler sign problem it was written for, and two reliable new wrong ones.
2. **A check in code is safer than a prompt instruction.** `v1` shows the model does not reliably follow a rule, and the guards act on what the parser actually returned.
3. **Recommendation:** adopt `v2` only together with the two guards, in the engine, and only after testing on problems outside this set. The next test is the full numeric stratum (234 problems), with the guards applied offline.
4. Raise the guards with Jash. They are an engine change and belong in the engine.

## 9. Limitations

- One model, 85 problems and two runs per variant. Counts of 3 to 6 answered problems cannot support rates.
- **Both guards were designed after seeing these answers, so their results are in-sample.** Ignoring the wave amplitude in guard 2 was chosen after seeing it would trigger false alarms on right answers.
- The controls and the `v2` runs used different API keys and different code (section 5). The model alias was the same.
- Flicker: single problems changed between runs, so a problem listed as new wrong or right in one run needs to appear in both before it is trusted.
- Only numeric problems were tested. Symbolic problems cannot be scored until the antlr4 path is validated.
