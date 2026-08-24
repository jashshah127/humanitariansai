# Physics problem-solving engine

A deterministic-first physics solver Medhavy calls as a tool. SymPy/SciPy do every
calculation; a language model is used only for reading the problem. Every call returns an
explicit **route** — so "did this get verified, or not?" is always answered, never implied.

Design reasoning: [`docs/Physics_Engine_Brief_v2.md`](docs/Physics_Engine_Brief_v2.md) ·
[`docs/Gru_SDD_Physics_Engine.md`](docs/Gru_SDD_Physics_Engine.md)

| Doc | What it answers |
|---|---|
| [`EVALUATION.md`](EVALUATION.md) | How to verify every claim yourself in two minutes |
| [`MEASUREMENT.md`](MEASUREMENT.md) | Automated benchmark assessment — what UGPhysics can and can't measure |
| [`COVERAGE.md`](COVERAGE.md) | 16 cards against 1,226 real problems, by topic |
| [`MARKET.md`](MARKET.md) | Commercial read, including the MATLAB/Mathematica question |
| [`PHASE1.md`](PHASE1.md) | What Phase 1 added and what's still open |

## Quick start

```bash
pip install -r requirements.txt
python3 eval/ci_check.py        # all 7 invariants, Phase 0 + Phase 1
python3 eval/demo_phase1.py     # raw problem text -> rendered answer
python3 eval/demo.py            # Phase 0 core: 16/16 + determinism + ambiguity
```

## See it working

Real output, pasted verbatim from a clean clone — not a description of what it would do.

```
$ python3 eval/ci_check.py

Phase 0 invariants
  [PASS] golden set: 16/16 golden-set problems
  [PASS] determinism: 10 identical runs
  [PASS] ambiguity routing: conflicting formulas flagged, not silently resolved

Phase 1 invariants
  [PASS] end-to-end from raw text: raw text -> answer for all 5 in-scope; out-of-scope one logged as a gap
  [PASS] unit/dimension consistency: no unit/dimension contradictions
  [PASS] symbolic coverage: all 25 cards solve symbolically (general formula, not just a number)
  [PASS] glossary covers every card variable: every card variable is documented; 8 known output collisions under arbitration
  [PASS] identity scoping enforced: student_id rejected on none-scope events; unregistered events rejected

All checks passed.
```

Raw problem text in, routed answer out — note **P6**, which is deliberately outside the
formula library and refuses to guess rather than inventing a confident answer:

```
$ python3 eval/demo_phase1.py

[P1] A car starts from rest and accelerates uniformly at 2.5 m/s^2 for ...
   badge      : Verified - solved symbolically
   answer     : v=30, s=180
   formula    : Constant-acceleration kinematics (1D)
   verified against golden set: OK

[P3] Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find ...
   badge      : Verified - solved symbolically
   answer     : a=1.96, T=47.04
   formula    : Atwood machine
   verified against golden set: OK

[P6] A 0.5 kg mass on a spring of constant 200 N/m has a damping consta...
   badge      : Unverified - AI reasoning, not symbolically checked
   -> handed back to Medhavy's model, labelled unverified

5/5 problems parsed from raw text AND solved correctly (0 mismatched)
```

The parser emits natural names and the system maps them onto card vocabulary — so the
normalization layer is genuinely exercised, not bypassed by a demo pre-loaded with the
right answers:

```
=== Did normalization actually fire (or did the demo cheat)? ===
  LLM emitted   : initial_velocity, acceleration, time / final_velocity, distance
  card received : ['a', 't', 'v0'] / ['s', 'v']
  renamed       : {'initial_velocity': 'v0', 'acceleration': 'a', 'time': 't', ...}
  auto-injected : ['G', 'g'] (never stated in the problem)
```

Tutor mode renders the same solution object as a hint ladder and withholds the answer:

```
  hint 1: Start by listing what you're given and what you're solving for. Given: m1 = 4, m2 = 6. Find: a, T.
  hint 2: This is a dynamics problem. The principle that applies here: Atwood machine.
  hint 3: Check the conditions before using it -- Two masses, frictionless massless pulley...
  hint 4: The relationship you need: T - g*m1 = a*m1; -T + g*m2 = a*m2
  hint 5: Common mistake to avoid here: Inconsistent sign convention across the two masses' equations.
  hint 6: Rearranged for what you're solving for: T = 2*g*m1*m2/(m1 + m2); a = g*(-m1 + m2)/(m1 + m2)
  hint 7: Worked result: a = 1.96, T = 47.04
  answer field withheld: True
```

And the engine audits its own formula library, unprompted:

```
=== Symbol-collision audit (derived from cards, run this in CI) ===
  undocumented card variables : (none)
  output collisions           : 5 -> ['v', 'a', 'T', 'r', 'F']
```

## Symbolic answers, not just numbers

The engine returns the general formula alongside the number — because that's what most
undergraduate physics actually asks for, and it's the better thing to show a student:

```
MECH-DYN-ATWOOD     T = 2*g*m1*m2/(m1 + m2)      a = g*(m2 - m1)/(m1 + m2)
MECH-GRAV-ORBIT     v = sqrt(G*M/(Re + h))
EM-CIRC-RC          tau = C*R
```

Cards stay symbolic until a final substitution step. Each card's algebra is solved once and
cached, so steady state is **6.30 ms/problem — 43% faster than the previous numeric-only
path**, since substituting into a pre-solved expression beats re-solving every time.

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
solve and tutor rendering. Unit/dimension auditing. Eight CI invariants, all green.

**Post-Phase-1 additions.** Cards now stay symbolic until a final substitution, so every
card returns a general formula alongside the number — and steady state got 43% faster.
Formula library grew 16 -> 25 cards, closing the largest measured coverage gap
(Vibrations and Waves: 179 benchmark problems, previously zero cards). Automated
benchmark harness against UGPhysics with both numeric and symbolic comparison.

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
