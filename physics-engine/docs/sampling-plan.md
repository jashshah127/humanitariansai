# Sampling Plan for the Parse-Accuracy Evaluation

**Author:** Harsh Gujarathi · **Plan item:** Wk 3, stratified sampling plan
**Status:** Draft v1, Oct 27, 2026 · **Audience:** Sri, Nik, Jash

## 1. What this plan is for

The engine has never been run at scale with a real parser. This plan decides which UGPhysics problems go into that run, how many, and how the results are reported so they cannot be blended into one misleading number.

UGPhysics has no "correct parse" to compare against, only final answers. So parse accuracy is measured indirectly, through three signals:

1. **Parse success:** did the model's reply become usable knowns and unknowns.
2. **End-to-end accuracy** on problems the engine can be scored on today: a wrong parse produces a wrong or missing answer.
3. **Decline analysis:** a decline with unrecognised variable names points at the parser; a decline after a clean parse points at missing formula cards.

A hand-labelled check of about 20 parses, planned with the Week 4 error taxonomy, would calibrate these three.

## 2. Population

| | Count |
|---|---|
| UGPhysics problems (Classical Mechanics 836, Classical Electromagnetism 390) | 1,226 |
| Skipped by the runner: no readable number in the answer | 258 |
| Skipped by the runner: true/false or multiple choice | 47 |
| **Attemptable (sent to the parser)** | **921** |

Attemptable problems split into two strata:

| Stratum | Count | What it can measure today |
|---|---|---|
| **Numeric** (numeric-scorable 224, partially numeric 10) | 234 | Parse success and accuracy |
| **Symbolic** (expression, equation, interval answers) | 687 | Parse success and declines only. Accuracy needs the antlr4 comparison path, planned for Wk 5 |

By topic (attemptable, of which numeric):

| Topic | Attemptable | Numeric |
|---|---|---|
| Particle Dynamics | 240 | 45 |
| Vibrations and Waves | 140 | 77 |
| Electrostatics | 132 | 22 |
| Rigid-Body Dynamics | 128 | 25 |
| Magstatics | 125 | 14 |
| Fluid Mechanics | 65 | 19 |
| Central Force Motion | 53 | 8 |
| Circuit Analysis | 38 | 24 |

## 3. Design

**A census, not a sample, for the full run.** Parsing all 921 problems takes about 100 minutes of pacing at the free tier's 6.5 seconds per call (budget 2 to 2.5 hours with latency). A sample of 300 would still leave per-topic estimates about 20 points wide, while the census gives every topic a real count and no sampling error.

**A stratified pilot first.** 100 problems, about 11 minutes, to catch harness, quota or prompt problems before the long run.

| Topic | Pilot size |
|---|---|
| Particle Dynamics | 25 |
| Vibrations and Waves | 15 |
| Electrostatics | 14 |
| Rigid-Body Dynamics | 14 |
| Magstatics | 14 |
| Fluid Mechanics | 7 |
| Central Force Motion | 6 |
| Circuit Analysis | 5 |

Within each topic, the pilot is split between the numeric and symbolic strata in proportion, with at least one of each where both exist. Problems are drawn at random with seed 2026, so the same files always give the same list.

**The pilot is run twice** to measure run-to-run variation. The Gemini parser uses temperature 0 but identical output is not guaranteed.

**The full run goes in batches of 250**, numeric problems first, so a quota cut-off still leaves the most valuable results. The runner saves what it has and stops after three failed model calls in a row.

## 4. What is reported

Every number is reported **per stratum**, never pooled, and always with its denominator:

| Measure | Definition (from `run_benchmark.py`) |
|---|---|
| Parse success | problems parsed / problems attempted |
| Answer rate | problems answered / problems attempted |
| Accuracy | matches / problems compared, numeric stratum only |
| Declines | no card, missing knowns, and how many had unrecognised variable names |

Also reported: ambiguous routes, solve errors, and parse failures split into API failures and bad output.

## 5. Statistical notes

- **Numeric stratum (234):** this is the whole stratum, so there is no sampling error. The model's own run-to-run variation is separate and is measured by the repeated pilot.
- **Pilot (100 of 921):** an overall rate has a margin of about ±9 points at 95% confidence. Per-topic pilot estimates (5 to 25 problems) are about ±20 points or wider, so they are indicative only.
- **Full run:** per-topic rates are exact counts of what happened on that run, not estimates.
- **Model:** the parser's default model is `gemini-3.6-flash`. The baseline in `baseline-methodology.md` used `gemini-flash-lite-latest`, so the two should not be compared as one model.

## 6. Procedure

From `physics-engine/`, with the two `ugphysics_*.csv` files in `eval/`:

```powershell
python eval/make_sample_ids.py
python eval/run_sample.py --ids eval/sample/ids_pilot.txt --dry
$env:GEMINI_API_KEY="<your key>"
python eval/run_sample.py --ids eval/sample/ids_pilot.txt --out benchmark_pilot_run1.json
python eval/run_sample.py --ids eval/sample/ids_pilot.txt --out benchmark_pilot_run2.json
python eval/run_sample.py --ids eval/sample/ids_full_01.txt --out benchmark_full_01.json
```

then `ids_full_02.txt` to `ids_full_04.txt`, with outputs named `benchmark_full_02.json` and so on. The scripts are `eval/make_sample_ids.py` (writes the ID lists) and `eval/run_sample.py` (runs a list through the existing `run_benchmark.full_run` unchanged). Each result file records which ID list produced it.

## 7. Data handling

- The ID lists contain only problem IDs, no problem text, so they can be committed.
- UGPhysics is licensed non-commercially. The CSVs stay local (gitignored) and only the numbers travel.
- The Gemini free tier may use prompts to improve Google's products. That is acceptable for public benchmark data and not for student work.
- Result files hold the benchmark's answer strings, which are dataset content. They are named `benchmark_*.json` so the repo's existing `.gitignore` pattern keeps them out of Git. Only the numbers from them go into documents.

## 8. Limitations and open items

- Parse accuracy here is indirect. Hand-labelling about 20 parses is needed to check the three signals.
- The symbolic stratum has no accuracy until the antlr4 comparison path is validated (Wk 5), and should be re-run then.
- The free daily quota (about 1,500 requests per day was assumed in the parser's notes) has not been checked against the current model. The pilot twice plus the full run is about 1,120 calls, before retries.
- Problems with no readable number (258) and true/false or multiple-choice problems (47) are outside what this evaluation measures.
- The numeric stratum is small for some topics (Magstatics 14, Central Force Motion 8), so per-topic accuracy there rests on few problems.
