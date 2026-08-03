# Physics problem-solving engine

A deterministic-first solver Medhavy calls as a tool: SymPy/SciPy do every calculation,
the LLM only handles problem understanding and formula selection, and every call
returns an explicit `route` — `deterministic_script`, `ambiguous_multiple_deterministic_paths`,
or `no_deterministic_path` — instead of leaving "script vs. LLM" implicit.

Full design reasoning: [`docs/Physics_Engine_Brief_v2.md`](docs/Physics_Engine_Brief_v2.md)
and [`docs/Gru_SDD_Physics_Engine.md`](docs/Gru_SDD_Physics_Engine.md).

## Structure

```
engine/       The solver itself. models.py, formula_kb.py (16 starter cards), pipeline.py.
golden_set/   16 verified problems (Phase 0 starter) + the locked topic-scope decisions.
eval/         demo.py (regression check), baseline_eval.py, pull_ugphysics_subset.py.
docs/         The brief and the design-doc writeup.
```

## Quick start

```bash
pip install -r requirements.txt
cd eval && python3 demo.py
```

Should print `16/16 problems solved with answers matching the golden set exactly`,
plus a determinism proof (same call ×10, byte-identical) and an ambiguity-detection
demo (two valid formulas, same unknown, correctly flagged instead of guessed).

## Current status (Aug 3, 2026)

- [x] Topic scope locked — `golden_set/Phase0_Starter_Kit_Topic_Scope_and_Golden_Set.xlsx`
- [x] Engine built, V2 routing responds to reviewer feedback on script-vs-LLM determinism
- [x] Crosschecked against one real external source (OpenStax Atwood-machine example — exact match)
- [ ] **Golden set is 16 problems, not the 150–300 Phase 0 calls for.** Two parallel paths:
      real course material (Q3 to Sri/Nik, still open) and/or UGPhysics's Classical
      Mechanics + Electromagnetism subsets (~2,450 problems, right difficulty level —
      see `eval/pull_ugphysics_subset.py`, needs to be run somewhere with network access)
- [ ] **No baseline number yet.** `eval/baseline_eval.py` measures plain LLM chain-of-thought
      accuracy (no tools) on the same problems — needs API keys, run wherever convenient
- [ ] Formula-card symbol collisions (`T` = tension on one card, period on two others) —
      caught by the ambiguity-routing logic so far, not yet fixed at the source; see
      the "Named domain risk" section in `engine/README.md` before adding cards past 16

## A note on data licensing

UGPhysics is CC-BY-NC-SA-4.0 (NonCommercial). Fine to pull locally and run the crosscheck
against; the accuracy *numbers* that comes out are ours to keep and share. The raw
problem/solution *text* shouldn't get committed into this repo, since it powers a
commercial product — that's why `ugphysics_*.csv` is gitignored. If this repo is ever
made public, worth a second look at anything derived from it before that happens.
