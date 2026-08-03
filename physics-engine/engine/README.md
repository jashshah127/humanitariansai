# Physics problem-solving engine — working prototype

A first real implementation of the pipeline in the brief: **Retrieve → Plan → Solve → Verify →
Solution object.** Not a spec, not a mock — this runs, and its answers are checked against the
Phase-0 golden set.

## Run it

```bash
cd engine
python3 demo.py
```

Solves all 16 Phase-0 golden-set problems and checks each result against the value already
verified there. Currently: **16/16 match**, plus one deliberate "missing known" case showing the
gap → curation-queue path instead of a silent wrong answer.

## Files

| File | What it is |
|---|---|
| `models.py` | `FormulaCard` shape, and the `solution_object()` assembler (the "Solution object" node in the brief's system diagram). |
| `formula_kb.py` | The 16 starter cards — one per Phase-0 golden-set problem. Each has required knowns, solvable unknowns, its actual equations (built fresh per call), output units, pitfalls, and a verify function where an independent check exists. |
| `pipeline.py` | `retrieve()`, `plan()` (closure check), `solve()` (SymPy only), `verify()`, and `solve_physics_problem()` — the one function meant to be exposed as a tool. |
| `demo.py` | Runs all 16 + the gap case, checks answers against the golden set. |
| `tool_schema.json` | The Anthropic tool-use schema for `solve_physics_problem` — literally "exposed as a tool that both product surfaces call." |

## What's real vs. what's a placeholder

**Real:** Retrieve, Plan (with an actual closure check — it tries to solve the system and only
proceeds if it resolves), Solve (100% SymPy, zero hardcoded arithmetic), and Verify (a generic
residual check on every card, a positivity sanity check where physically required, plus a true
independent second path for 6 of the 16 cards — boundary continuity, Kirchhoff's current law,
period computed two different ways, etc.).

**Placeholder, by design:** **Parse.** The brief's own architecture has the LLM (Claude, inside
either product surface) do problem understanding and hand this tool already-structured `knowns`/`unknowns`
— this tool was built to assume that's already happened, the same way `demo.py` hands it in
directly rather than including a free-text parser. That's not a shortcut so much as the correct
division of labor per the brief: *this* tool's job starts at Retrieve.

## V2 — script-vs-LLM routing (determinism)

V1 didn't say how the system should decide, per problem, whether to trust the script alone
or involve the LLM. V2 makes that decision explicit instead of implicit. `solve_physics_problem`
now always returns a `route`:

| `route` | Meaning | What should call the LLM |
|---|---|---|
| `deterministic_script` | Exactly one formula card reached closure. | Nothing — this answer is final. |
| `no_deterministic_path` | Zero cards reached closure (missing knowns, or nothing in the KB covers this). | Yes — LLM (or human) handles it directly, AND it's logged as a coverage gap for the curate loop. |
| `ambiguous_multiple_deterministic_paths` | More than one card reached closure for the same requested unknown. | Yes — but to *arbitrate which formula applies*, not to redo the arithmetic. Every candidate's answer is included. |

**Why this matters (the part flagged as not-yet-understood in V1 feedback):** SymPy itself has no
randomness — given the same equations and the same numbers, it returns the same answer every
time, full stop. So "the same problem produces different outputs" can't actually come from the
solver being flaky. It can only come from **which formula gets selected being unstable** (more
than one card could plausibly apply, and nothing picks between them) — or from an LLM doing part
of the reasoning and sampling differently across calls. That reframing is why the fix here isn't
"run it twice and check if the answers match" (expensive, and it would never catch anything on the
script side, since SymPy can't disagree with itself) — it's "check *before solving* how many
independent deterministic paths exist for this problem." That check is itself cheap and stable.

This is also why determinism is worth defending at all, concretely, for this system:
- **Grading fairness.** Grade mode compares a student's work against a reference solution. Two
  students with the identical problem must be graded against the identical reference — not
  "whichever answer the LLM happened to sample that day."
- **Debuggability.** A wrong answer with a `route` and a `matched_card` tells you exactly what to
  fix (a card, or a missing known). A wrong answer with no routing information could be anywhere.
- **Cost.** LLM calls are slower and pricier than a symbolic solve. Routing on "does a deterministic
  path exist" instead of "call the LLM by default" is also the cheaper option, not just the more
  rigorous one.

**Proof, not assertion:** `demo.py` runs the Atwood-machine problem 10 times and diffs the full
output — byte-identical every time. It also runs a constructed case where the same knowns
legitimately satisfy two unrelated cards (kinematics and spring energy) for a shared unknown `v`,
producing v=30.0 via one path and v≈2.37 via the other — and confirms the engine reports both and
asks for arbitration rather than silently returning one.

**This also resolves the symbol-collision limitation below, in practice if not in principle:** the
ambiguity route doesn't stop irrelevant cards from being retrieved (that root cause is still there),
but it does guarantee that if two colliding-symbol cards both actually close, the system flags it
instead of silently trusting whichever one happened to sort first.

## Known limitation — read before growing the card count

**Symbol names aren't namespaced by physical meaning, only by string.** `T` means *tension* on the
Atwood card and *orbital/cyclotron period* on two others. Right now `retrieve()` still finds the
right card because topic_hint and "which knowns are actually available" both happen to sort the
correct one first — verified this doesn't misfire on any of the 16 — but it's a coincidence of
this specific KB's knowns, not a structural guarantee. At 150–300 cards, some `T`-shaped or
`v`-shaped collision *will* eventually rank a wrong card first. Before scaling the KB, this needs
either a semantic tag per output variable (`"T": "tension"` vs `"T": "period"`) or fully namespaced
symbols. Flagging now, deliberately not fixing it silently, since it changes the `unknowns` input
shape other things would need to agree on.

**Units are declarative, not derived.** Each card states its `output_units` as a label; nothing
does true dimensional analysis of the underlying equations (that's what `pint`/`sympy.physics.units`
would add — `pint` isn't installed in this sandbox, and wiring `sympy.physics.units` through every
equation was left out to keep this prototype's scope to what could be fully verified today).

**Retrieve/Plan judgment is currently rule-based, not LLM-assisted.** Fine at 16 cards; the brief's
tier-2 formula retrieval likely wants embedding-based search over cards once the KB is large enough
that keyword/tag matching stops being reliable.

## Natural next steps

1. Wire a real `parse()` — a Claude call that turns raw problem text into the `knowns`/`unknowns`
   shape this tool expects (JSON output, matching `tool_schema.json`'s input).
2. Decide on the symbol-namespacing fix above before adding cards past this starter set.
3. Once real course problems exist (Q3 in the brief) and get logged as cards here, the golden-set ×
   engine cross-check this demo does becomes the actual Phase 1 "measured against baseline" step.
