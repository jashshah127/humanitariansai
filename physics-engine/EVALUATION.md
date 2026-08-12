# How to evaluate this

Written for a reviewer who wants to check the claims rather than take them on trust.
Everything below runs in about two minutes and needs no API key.

```bash
git clone https://github.com/jashshah127/humanitariansai.git
cd humanitariansai/physics-engine
pip install -r requirements.txt

python3 eval/ci_check.py        # every claim, as a pass/fail
python3 eval/demo_phase1.py     # the walkthrough, raw text in
```

## The four claims, and how to falsify each

**1. It never returns a confidently wrong answer.**
This is the whole point of the project, so it deserves the hardest look. The engine
computes only when exactly one formula in its library fits. When several fit, it returns
all of them flagged for arbitration; when none fit, it says so.

*Check it:* `ci_check.py` constructs a case where two unrelated formulas both legitimately
apply to the same requested unknown and produce different numbers (30.0 vs 2.37). It must
report both, not pick one. `demo_phase1.py` also runs a damped-oscillator problem that is
outside the library — it should come back **Unverified** and get logged as a coverage gap.

*How to break it:* type any physics problem the 16-card library doesn't cover into
`PhysicsEngineMode.solve()`. A confident answer to something it can't actually solve would
be a real failure. It should say it doesn't know.

**2. It is deterministic.**
Same problem, same answer, always — which matters because grade mode has to evaluate two
students with the same problem against the same reference, not against whatever got
sampled that day.

*Check it:* `ci_check.py` runs one problem ten times and diffs the full output for
byte-identical results. Run it repeatedly if you want; SymPy has no sampling in it.

**3. It gets the physics right.**
16 problems across mechanics and E&M, each answer computed symbolically and cross-checked
— several by an independent second derivation (boundary continuity, Kirchhoff's current
law, a period computed two unrelated ways).

*Check it:* `ci_check.py` reports 16/16 against the golden set. Independently: the Atwood
example from OpenStax *University Physics Vol. 1* (m₁=2.00 kg, m₂=4.00 kg) has a published
answer of a=3.27 m/s², T=26.1 N. The engine returns 3.2667 and 26.133.

**4. Its own design flaws are machine-detectable, not just documented.**
The formula library reuses symbol names — `T` means tension on one card and period on two
others. That's a dimensional contradiction (force vs. time), and `units.py` finds it
automatically by auditing declared units against the glossary.

*Check it:* the unit-consistency line in `ci_check.py`. It currently passes because the
glossary was corrected once the audit surfaced the conflict; the audit is what turns
"namespace the symbols eventually" from a judgement call into a trigger with evidence.

## What is NOT proven — please read before forming a view

**Parse quality is unmeasured.** The demo runs on a stub with canned parses. It proves the
plumbing (normalization, constant injection, routing, rendering, logging); it proves
nothing about whether a real language model reads problems correctly. "5/5 from raw text"
honestly means *5/5 given a correct parse*. Swapping in the real model is one line and
needs an API key:

```python
from parse import ClaudeLLM
from physics_mode import PhysicsEngineMode
mode = PhysicsEngineMode(ClaudeLLM())
```

**There is no baseline number.** Nobody has yet measured plain chain-of-thought accuracy on
these same problems, so "better than an LLM doing the arithmetic itself" is currently an
argument, not a measurement. `eval/baseline_eval.py` is written and waiting on a key.

**Coverage is thin and measured.** 16 formula cards against 1,226 real UGPhysics problems.
79% of those fall in a topic with at least one card, but that's a generous ceiling — one
rotation card against 180 rigid-body problems isn't coverage. Details, including the
largest gap (Vibrations and Waves: 179 problems, zero cards), are in `COVERAGE.md`.

**Nothing is deployed.** No running service, no integration into Medhavy, no student has
used this. `engine/physics_mode_api.json` is a contract, not an endpoint.

## The three questions worth asking

1. Is the routing decision the right one, or is it just a way of avoiding hard problems?
   (The argument: SymPy can't be non-deterministic, so instability can only come from
   formula selection or model sampling — which is why the check happens *before* solving
   rather than by running it twice.)
2. Does the coverage ceiling justify continuing on this architecture, or does 16 cards
   against 1,226 problems suggest the card-based approach doesn't scale?
3. What's the acceptable rate of **Unverified** answers before the mode stops feeling
   useful to a student?
