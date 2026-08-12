# Physics problem-solving engine

A deterministic-first physics solver Medhavy calls as a tool. SymPy/SciPy do every
calculation; a language model is used only for reading the problem. Every call returns an
explicit **route** — so "did this get verified, or not?" is always answered, never implied.

Design reasoning: [`docs/Physics_Engine_Brief_v2.md`](docs/Physics_Engine_Brief_v2.md) ·
[`docs/Gru_SDD_Physics_Engine.md`](docs/Gru_SDD_Physics_Engine.md)
Phase 1 detail: [`PHASE1.md`](PHASE1.md)

## Quick start

```bash
pip install -r requirements.txt
python3 eval/ci_check.py        # all 7 invariants, Phase 0 + Phase 1
python3 eval/demo_phase1.py     # raw problem text -> rendered answer
python3 eval/demo.py            # Phase 0 core: 16/16 + determinism + ambiguity
```

## Structure

```
engine/   Solver core (Phase 0) + parse, event log, mode layer, units (Phase 1)
eval/     ci_check.py, both demos, baseline harness, dataset puller
golden_set/  16 verified problems, locked topic scope
docs/     Brief and design writeup
```

## Status

**Phase 0 — done, on `physics-engine` branch.** Topic scope locked. 16-card formula KB.
16/16 golden-set problems solved. Determinism proven (10 identical runs). Ambiguity
routing catches conflicting formulas instead of guessing. One external crosscheck against
OpenStax matched exactly.

**Phase 1 — this upload.** Raw problem text now goes in the front. Parse stage (LLM,
injectable). Event log with identity scoping enforced in code. Physics Engine mode with
solve and tutor rendering. Unit/dimension auditing. Seven CI invariants, all green.

**Open, and not papered over:**
- Parse quality is unmeasured — the demo uses a stub LLM. Real-model accuracy needs an API key.
- No baseline number yet, so "better than plain chain-of-thought" remains unquantified.
- 1,226 UGPhysics problems pulled, never run through the engine.
- Q6 (data processing agreement / IRB) still open with Prof. Sri and Prof. Nik. No
  student-linked data should flow until it's answered.
- Medhavy's backend still unseen from here; integration effort unestimated.

## Data licensing

UGPhysics is CC-BY-NC-SA-4.0 (NonCommercial). Fine to pull locally and evaluate against;
the accuracy numbers are ours to keep. The raw problem text shouldn't be committed here —
hence `ugphysics_*.csv` in `.gitignore`. Worth a second look before this repo ever goes public.
