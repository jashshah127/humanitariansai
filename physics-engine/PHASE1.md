# Phase 1 — LLM + tool use, raw text in

Phase 0 started at Retrieve and assumed knowns and unknowns had already been extracted.
Phase 1 starts one stage earlier, at **raw problem text**, and adds the surface Medhavy
attaches to its input box.

```bash
pip install -r requirements.txt
python3 eval/ci_check.py      # every invariant, Phase 0 and Phase 1
python3 eval/demo_phase1.py   # the end-to-end walkthrough
```

## What's new

| File | What it adds |
|---|---|
| `engine/parse.py` | The Parse stage. LLM reads raw text into structured knowns/unknowns. The LLM call is **injected**, so the engine stays testable with no network and the API key never lives in the package. Every value carries the phrase it came from. |
| `engine/variable_glossary.py` | The shared vocabulary between parser and cards, plus alias normalization and scoped constant injection. |
| `engine/event_log.py` | The event log the brief named as the Phase 1 addition. Identity scoping from the telemetry table is **enforced in code** — emitting a `none`-scope event with a `student_id` raises. |
| `engine/physics_mode.py` | Physics Engine mode: the toggle. Renders solve and tutor. |
| `engine/physics_mode_api.json` | The request/response contract for Medhavy's frontend. |
| `engine/units.py` | Dimensional consistency checking across cards and glossary. |
| `eval/ci_check.py` | All seven invariants in one command. |

## The mode toggle — what it actually changes

Off, a student gets an answer that reads like every other LLM answer: fluent, confident,
carrying no information about whether it's right. On, the student still always gets an
answer, but it arrives with its status visible:

- **Verified** — a symbolic solver computed this; reproducible and correct.
- **Needs review** — several principles fit and disagree; every candidate shown, with the
  condition under which each applies.
- **Unverified** — nothing in the library covers this; this is AI reasoning, labelled.

**The floor never drops below "no tool at all,"** because the unverified path *is* no tool
at all, labelled. There's no input where turning this on makes the answer worse. That
asymmetry is the case for shipping it.

The most misimplementable field is `needs_llm_completion`. True means Medhavy's own model
must finish the answer — **under the badge given**, not as verified. Treating it as "fall
back silently" reintroduces the exact failure this engine exists to prevent.

## Verified in this phase

- 5/5 in-scope problems go from raw text to correct answer, matching the Phase 0 golden set.
- A 6th problem deliberately outside the KB (damped oscillator) correctly routes to
  unverified and lands in the coverage queue rather than getting a confident wrong answer.
- Normalization genuinely fires: the canned parses use `initial_velocity`, `angle`,
  `resistance` — what a real model emits — not the card names, so the layer is exercised
  rather than bypassed.
- Phase 0 is untouched: 16/16, determinism, ambiguity routing all still pass.
- Identity scoping rejects a `student_id` on a `none`-scope event.

**The unit audit found a real defect.** It independently rediscovered the `T` symbol
collision — tension (newtons) on one card, period (seconds) on two others — with
dimensional evidence. Force versus time can't be a false alarm. That collision was
previously known only because someone noticed it by hand; it's now machine-detectable,
which turns "namespace the symbols eventually" from a judgement call into a check with an
objective trigger.

## Three gaps, stated plainly

**1. Parse quality is unmeasured — the biggest one.** The demo runs on `StubLLM`, a test
double with canned parses. It proves the *plumbing* — normalization, constant injection,
routing, rendering, event logging. It proves **nothing** about whether a real model parses
well. Swap in `ClaudeLLM` and run against the golden set to find out:

```python
from parse import ClaudeLLM
from physics_mode import PhysicsEngineMode
mode = PhysicsEngineMode(ClaudeLLM())        # needs ANTHROPIC_API_KEY
```

Until that runs, "5/5 from raw text" means 5/5 *given a correct parse*.

**2. No baseline number.** Phase 1's brief deliverable is "measured against baseline," and
the baseline is still unrun — `eval/baseline_eval.py` has been ready since Phase 0 and
needs an API key. Without it there's no measurement of how much better this is than plain
chain-of-thought, which is the number the whole project is justified by.

**3. `pint` is not used, contrary to the brief's Phase 1 line.** It couldn't be installed
in the build environment (no outbound network), so rather than write code against a
library never executed once, `units.py` uses `sympy.physics.units`, which is present and
was actually run. Unit *declarations* are now verified. Unit *propagation through the
algebra* is not — the cards bake numeric values in before sympy sees them, so nothing
unit-carrying survives to propagate. Fixing that means rewriting cards to stay symbolic
until the last step: a real change, deliberately not smuggled in under a units ticket.

## Still open from earlier, unchanged

- The 1,226 UGPhysics problems were pulled but never run through the engine.
- Q6 (data processing agreement / IRB) is still open with Prof. Sri and Prof. Nik. No
  student-linked data should flow through this until it's answered — which is why
  `student_id` is accepted by the API and used by nothing.
- Medhavy's own backend is still unseen from here, so the integration effort behind
  `physics_mode_api.json` remains unestimated.
