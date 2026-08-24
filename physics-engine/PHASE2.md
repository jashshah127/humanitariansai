# Phase 2 — grade mode, scope expansion

The brief defines Phase 2 as: *formula knowledge base + retrieval, verify stage, grade mode,
expand to thermo/quantum.* Retrieval and verify shipped in Phase 0/1. This covers the rest.

```bash
python3 eval/ci_check.py     # 9 invariants across all three phases
```

## Grade mode — the third surface

Solve mode answers. Tutor mode hints. Grade mode takes a student's **own work** and says
where it went wrong. Different question, and the one instructors actually need.

**It diagnoses rather than marks.** Anything can mark an answer wrong. What makes this
useful is naming *which* mistake, by testing the student's value against specific wrong
formulas derived from the card's own symbolic solution:

| Pattern | What it catches |
|---|---|
| `sign_flip` | Reversed a difference — `g(m₁−m₂)` where the formula wants `g(m₂−m₁)` |
| `reciprocal` | Inverted the relationship — common with periods and frequencies |
| `factor_2_high` / `factor_2_low` | Lost or gained a factor of 2 — `MR²` instead of `½MR²` |
| `sqrt2_low` / `sqrt2_high` | The escape-vs-orbital velocity confusion, exactly √2 apart |
| `sqrt_forgotten` | Returned the quantity under the root without taking the root |

Worked example: a student submits a = −1.96 for the Atwood problem. Grade mode doesn't say
"wrong, should be 1.96." It says the value matches what you get from reversing a
difference, and quotes the card's own warning about sign convention across the two masses.

**Divergence detection.** Given intermediate steps, it reports the *first* quantity that
departs from the reference — everything after is downstream of that error, so the earliest
divergence is the only useful pointer. Tested: a student with I = 0.125 instead of 0.0625
gets pointed at the moment of inertia, not at the final angular speed.

**The invariant that matters most: it refuses to grade what it can't verify.** If no card
produces a verified reference, grade mode returns `not_assessable` and routes to human
review. Marking a student wrong against an unverified answer would be this project's own
failure mode aimed at someone's transcript. That refusal is a CI check, not a convention.

**Nothing is stored.** Grading inherently needs student identity — the brief flagged this
from the start. This module takes a submission, returns an assessment, and forgets.
Persisting graded work is a separate decision gated on Q6 (data processing agreement /
IRB), still open. The capability exists while the storage question stays unanswered, rather
than the reverse.

## Scope expansion: thermodynamics, not quantum

**Six thermo cards added** (31 total): ideal gas law, sensible heat, latent heat, Carnot
efficiency, isothermal entropy, first law. Each verified against known values — Carnot at
500K/300K gives 0.4, heating 2 kg of water by 30K gives 251,160 J, and so on.

Their pitfalls are the ones that actually cost students marks: Celsius where Kelvin is
required, `mc∆T` applied across a phase change, fusion versus vaporization latent heat, and
the first law's sign convention on W (which half of textbooks flip).

The Carnot card carries a real verification: efficiency must lie strictly between 0 and 1.
A Celsius temperature produces a value outside that range, which the check catches — the
second law used as a unit test.

**Quantum is deliberately not built**, on the brief's own stated reasoning: SymPy's quantum
tooling is thin, so QM would lean on curated worked derivations rather than symbolic
solving. Building weak quantum cards to claim the scope would be worse than not building
them — the coverage number would go up while the thing the engine is for got worse.

## Phase 3 should not be started

The brief makes tier-3 fine-tuning/RLVR **conditional**: *"only if evals plateau below
target with full KB coverage."* That trigger has not fired, and the benchmark run says why.

Across 60 UGPhysics problems the engine produced **zero wrong answers** — it declined
nearly everything, because coverage is thin and most of the benchmark asks for derivations.
Nothing plateaued. There is no evidence a better model would help, and considerable
evidence that more formula cards would.

Building Phase 3 now would be exactly the kind of decision the decision log exists to
prevent: doing the interesting work instead of the indicated work. The trigger is written
down; it should be honoured.

## Symbolic input mode — the coverage lever

The benchmark's clearest finding was that most of UGPhysics is stated in symbols, not
numbers: *"a particle of mass m, charge q, initial velocity v..."*. The engine used to
decline those, and the parser made it worse by inventing values — it reported `m=1.0,
q=1.0` for a problem that contained no numbers at all.

**Both are fixed, and they were the same bug wearing two hats.** The parser now reports a
symbolic quantity as symbolic instead of guessing a number, and the pipeline solves it:

```
Two masses m1 and m2 over a frictionless pulley. Find a and T.

  a = g*(m2 - m1)/(m1 + m2)
  T = 2*g*m1*m2/(m1 + m2)
  verify: T - g*m1 = a*m1  ->  simplifies to 0 (identity, holds for all values)
```

Worth noting what that verification line means: in symbolic mode the residual check
simplifies to zero rather than evaluating to a small float. That is a **stronger** check —
it proves the relation holds for *all* values, not just the ones supplied.

Mixed problems work too (`m1=4, m2` symbolic → `a = (9.8*m2 - 39.2)/(m2 + 4)`), and the
numeric path is unchanged.

**Why this matters more than adding cards.** Those problems were never beyond the engine's
mathematical reach — SymPy does symbolic algebra by default. They were declined because the
pipeline insisted on converting results to `float` at the very end. An interface limitation
was being reported as a coverage gap, which is worse than an honest gap: it hid capability
that already existed.

## Honest status across all phases

| | State |
|---|---|
| **Phase 0** — scope, golden set, baseline | Scope locked. Golden set is 31 cards, not the 150–300 problems originally scoped. Baseline harness now runs on the free tier but **has not been run** — that's the last genuine Phase 0 gap. |
| **Phase 1** — MVP pipeline, measured | Built and verified. Parse quality still unmeasured against a real model beyond spot checks, and it has a known bug (invents numeric values for symbolic problems). |
| **Phase 2** — KB, verify, grade, thermo | Built. Grade mode, 31 cards, thermo added, quantum deliberately excluded. |
| **Phase 3** — RLVR | **Correctly not started.** Trigger has not fired. |

**The real constraint is unchanged and now measured: coverage.** 31 cards against
undergraduate physics means the engine declines most of what it sees. That's honest
behaviour, not broken behaviour — but it's the thing standing between this and a student
finding it useful, and no amount of Phase 3 would fix it.
