# Baseline Methodology: Plain LLM vs. Physics Engine

**Author:** Harsh Gujarathi · **Plan item:** Wk 2, baseline run and methodology
**Status:** Draft v3, updated Oct 26, 2026 · **Audience:** Sri, Nik, Jash

## 1. Purpose

The engine's accuracy on the golden set (16/16) means little without a comparison. This baseline measures how often a plain LLM, with no tools, no SymPy and no verification step, solves the same 16 problems. It is the "no engine" reference point.

## 2. Setup

| Item | Value |
|---|---|
| Dataset | `golden_set/golden_set_16.csv`: 8 mechanics (MECH-001 to 008) and 8 electromagnetism (EM-001 to 008) problems, each with expected values in `expected_json` |
| Script | `eval/baseline_eval.py` (in the repo) |
| Model | `gemini-flash-lite-latest` (the script's default), free tier, no tool use |
| Settings | temperature 0, one run, one call per problem. A call is retried up to 4 times on API errors only, never because an answer was wrong. Tolerance 1% relative |
| Date run | Oct 19, 2026 |
| Raw output | `baseline_results_gemini.json` (kept local; gitignored by design) |

**Prompt given to the model** (verbatim from the script):

> Solve this physics problem. Show your work, then give your final answer(s) on their own line(s), one per requested quantity, in exactly this form: `FINAL ANSWER: <quantity name> = <value> <units>`. If there is only one quantity asked for, still use a quantity name (e.g. "v" or "F").

Note that the prompt does not give the model the variable names used in the golden set (`v`, `s`, `T`, `t_flight`, and so on).

## 3. Scoring rules

Three rules were applied to the same 16 saved replies.

| Rule | Definition | Where it comes from |
|---|---|---|
| **A. Strict** | A problem passes only if the model's quantity name matches the expected name exactly and every value is within 1% | The original `baseline_eval.py` scorer |
| **B. By value** | Names are ignored. A problem passes if every expected value is matched by a different `FINAL ANSWER` value within 1%. Units are ignored | `eval/rescore_baseline.py` (written after the strict result, not yet committed) |
| **C. Asked quantities only** | A problem passes if every quantity the problem text actually asks for is correct. Intermediate quantities the golden set lists but the problem does not ask for are not required | Judged by hand from each problem's wording |

**Important:** rules B and C were defined after seeing the strict result, because that result was dominated by a scoring artifact (see section 5). They are reported alongside rule A, not instead of it.

## 4. Results

| Rule | Result |
|---|---|
| A. Strict | **3/16 (18.8%)** |
| B. By value | **11/16 (68.8%)** |
| C. Asked quantities only | **15/16 (93.8%)**, or **16/16** if answers in different units are accepted |

Rule C is a range because of MECH-008 (see section 5).

Per problem:

| Problem | A | B | C | Note |
|---|---|---|---|---|
| MECH-001 | fail | pass | pass | Names differed (`final speed`, `distance`) |
| MECH-002 | fail | pass | pass | Names differed |
| MECH-003 | fail | pass | pass | Names differed (`acceleration`, `tension`) |
| MECH-004 | fail | pass | pass | Names differed |
| MECH-005 | pass | pass | pass | |
| MECH-006 | fail | fail | pass | KEi and KEf computed in the working, not listed in final answers |
| MECH-007 | fail | fail | pass | I computed in the working, not asked |
| MECH-008 | fail | fail | pass* | Answer given in km/s and minutes |
| EM-001 | fail | pass | pass | Name differed (`Force`) |
| EM-002 | pass | pass | pass | |
| EM-003 | fail | pass | pass | Names differed |
| EM-004 | fail | fail | pass | R_series and I_total not asked |
| EM-005 | fail | pass | pass | One name differed |
| EM-006 | fail | pass | pass | Names differed |
| EM-007 | pass | pass | pass | |
| EM-008 | fail | fail | pass | Area A computed in the working, not asked |

\* Counted as a pass if units are not required to be SI. See section 5.

## 5. Failure analysis

The raw replies for all five problems that failed rule B were read in full.

- **MECH-006, MECH-007, EM-004, EM-008 (4 problems):** the model computed every quantity correctly in its working, but listed in `FINAL ANSWER` only the quantities the problem asked for. The golden set also lists intermediates (initial and final kinetic energy, moment of inertia, series resistance and total current, loop area). Rule B demands them, and the problems never ask for them.
- **MECH-008:** the working gives v = 7616.5 m/s and T = 5666.6 s, both correct (the golden set has 5668.2 s, a 0.03% rounding difference). The model then restated the final answers as 7.62 km/s and 94.4 minutes. The problem does not specify units.
- **The other 8 failures under rule A** (MECH-001 to 004, EM-001, EM-003, EM-005, EM-006): the model's values were correct, but it wrote descriptive names where the scorer expected variable names.
- **Why names caused so many failures:** the original scorer's extraction pattern reads only single-word names and plain numbers (`[\w_]+` for the name, `[-\d.eE+]+` for the value). A line such as `FINAL ANSWER: final speed = 30 m/s` is not read at all, and a value written as `6.871 × 10^6` would be read as 6.871. The rescoring script reads both forms.

**Across all 16 problems, no value the model gave in its final answers was wrong.** Every failure under rules A and B traced to the scorer or to quantities the problem did not ask for. This was checked in two ways: the raw replies of the five problems that failed rule B were read in full, and every extracted final-answer value in all 16 problems was compared with the golden-set values. The only values that matched nothing were MECH-008's 7.62 and 94.4, which are the correct speed and period in km/s and minutes.

## 6. Interpretation

1. Under rule C, which was chosen after seeing the results, a small, free model gets 15 or 16 of these 16 intro-level problems right, against the engine's 16/16. On that reading this golden set does not separate the two on correctness.
2. The engine's advantages here are not raw accuracy: every number comes from a symbolic solver, it states whether an answer was verified, it behaves deterministically, and it declines out-of-scope problems instead of guessing.
3. A comparison that shows a real gap needs harder problems. This supports the request to move toward graduate-level problems.
4. Reporting only the strict 18.8% would have been misleading. Reporting only rule C would hide that it was chosen after seeing results. All three are reported for that reason.

## 7. Limitations

- **Sample size:** 16 problems, so each problem is 6.25 points of accuracy.
- **One run at temperature 0.** Run-to-run variation was not measured.
- **One small model.** A larger model would probably score at least as well.
- **Easy problems.** All 16 are single-concept intro problems.
- **Possible overlap with engine development:** the engine's CI check runs these same 16 problems. Whether the engine was tuned against them has not been confirmed, so the engine's 16/16 should not be treated as independent evidence.
- **Rule C is a human judgment** about which quantities a problem asks for.
- **Units:** rules A and B ignore units. Only MECH-008 was affected here.

## 8. Reproduce

From the `physics-engine` folder, with a free key from aistudio.google.com/apikey:

```powershell
$env:GEMINI_API_KEY="<your key>"
python eval/baseline_eval.py --input golden_set/golden_set_16.csv --model gemini
python eval/rescore_baseline.py baseline_results_gemini.json
```

The first command takes about 2 to 3 minutes (calls are spaced 6.5 seconds apart for the free-tier limit). The second makes no API calls.

## 9. Recommended next steps

1. Add a harder problem set (graduate level, or a stratified sample from UGPhysics). The repo already has `eval/run_benchmark.py` for that.
2. Change the baseline prompt to require the golden set's variable names, or have the scorer match by value, and make the extraction read multi-word names and scientific notation, so rule A stops penalizing correct answers.
3. Decide whether intermediate quantities belong in `expected_json`. The engine's grade mode grades asked quantities only, and the baseline should follow the same rule.
4. Repeat the run at least three times to measure variation, and add a second model.
5. Commit `rescore_baseline.py` to the repo through a PR.
