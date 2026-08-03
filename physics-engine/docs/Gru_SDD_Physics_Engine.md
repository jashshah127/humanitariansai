# Physics problem-solving engine — Gru-format design document

**Team:** Medhavy (Jash, Product Lead)
**Reviewer voice:** Gru

*Integrating the V2 brief and the routing-engine prototype into one document, structured the way we structure things, not the way it arrived. Where we're reorganizing existing decisions, we say so. Where we're making a new call, we say that too.*

## /v0 — naming the thing being built

A stateless, deterministic-first physics problem-solving service that both product surfaces call as a tool: symbolic computation (SymPy/SciPy) owns every calculation with no exceptions, and the LLM is invoked only when no single verified formula path exists for a problem, or more than one plausibly does.

**Gate check:** that sentence names one system. It doesn't describe a tutoring app, a grading app, or a generic "AI physics helper" — it names the arbitration boundary between script and LLM, which is the thing actually under review right now. Passes /v0.

## Problem Formulation

**The specific failure mode this exists to close:** plain LLM chain-of-thought silently produces wrong arithmetic/algebra on physics problems — not "sometimes wrong," but wrong in a way that looks exactly as confident as when it's right, which is the dangerous case for a tutoring product a student is meant to trust. This isn't a generic "make an AI tutor" problem; it's specifically the silent-computation-error problem, which is why the design principle is "the LLM never computes" rather than "the LLM tries harder."

**Users:**
- Students in solve mode (Medhavy) — need a correct final answer.
- Students in tutor mode — need progressive hints, not just an answer, without the hints themselves being wrong.
- Instructors, eventually (grade mode) — need a trustworthy reference solution to grade against, and problem-linting before problems reach students.

**Business need:** an EdTech tool that gets caught giving confidently-wrong math once is a tool students stop trusting — which is worse than one that's occasionally slow. Reproducibility also isn't optional once grade mode exists: two students with the identical problem have to be evaluated against the identical reference answer, which is a fairness requirement, not a nice-to-have.

**This Problem Formulation fails the "describes ten systems" test if it stops at "AI physics tutor."** It passes because the actual claim is narrower: a routing boundary between a solver that cannot be wrong in a way that varies (SymPy) and a reasoner that can (the LLM), with an explicit rule for which handles which problem.

## Component → User/Business-need map (confirmed before documenting any of them below)

| Component | Maps to |
|---|---|
| Parse (LLM) | Student need: problem understood correctly before anything is computed |
| Retrieve (formula-card KB) | Business need: auditable "why this formula" trail, not an opaque LLM guess |
| Plan + closure check | Business need: never send an under-determined problem downstream |
| Solve (SymPy only) | Student + business need: zero silent arithmetic error, the core failure mode above |
| Verify (residual + independent path + positivity) | Business need: catch a wrong *formula choice* even when the arithmetic on top of it is correct |
| **Route** (`deterministic_script` / `ambiguous_multiple_deterministic_paths` / `no_deterministic_path`) | Business need: this is the actual review feedback — an explicit, auditable answer to "script or LLM, and why," replacing an implicit one |
| Event log → 4 loops (curate/teach/learn/model) | Business need: production failures become roadmap inputs instead of disappearing |
| Telemetry table | Business + compliance need: FERPA/IRB exposure stays scoped to named decisions, not open-ended collection |

Every section below only exists because it has a row above. Nothing is documented on the theory that it might be useful someday.

## Systems & Architecture

**Pipeline:** Parse → Retrieve → Plan (closure check, loops back to Retrieve on a gap) → Solve (SymPy/SciPy, never the LLM) → Verify → Solution object. One object renders three ways: full answer (solve mode), progressive hints (tutor mode), comparison against student work (grade mode).

**The routing layer (V2, direct response to review feedback):** every solver call now resolves to one of three routes, decided *before* solving:

- `deterministic_script` — exactly one formula card closes. Final, reproducible — proven by running the same call 10× and diffing byte-identical output, not asserted.
- `ambiguous_multiple_deterministic_paths` — more than one card closes on the same requested unknown. This is the literal "same problem, different outputs" case reviewers flagged. Proven with a constructed case: knowns satisfying both a kinematics card and a spring-energy card for a shared unknown `v` correctly return both candidates (30.0 and 2.37) instead of silently picking one.
- `no_deterministic_path` — nothing in the KB covers it yet. LLM handles it, logged as a curate-loop coverage gap.

**Why the rule is what it is, not just that it exists:** SymPy has no randomness — it cannot itself produce different outputs for the same inputs. So "same problem, different outputs" can only come from unstable formula-selection or from LLM sampling variance. That's why the check is "does exactly one verified path exist" (cheap, asked before solving) rather than "solve it twice and diff" (expensive, and incapable of catching anything on the script side, since the script can't disagree with itself).

## Domain & API

**Formula-card knowledge base:** 16 starter cards (8 Mechanics, 8 E&M), each carrying required knowns, solvable unknowns, its actual equations, expected output units, common pitfalls, and — for 6 of the 16 — an independent verification path (boundary continuity, Kirchhoff's law, a quantity computed two unrelated ways).

**Tool contract:** `solve_physics_problem(problem_id, raw_problem, knowns, unknowns, topic_hint)` → Solution object including `route`. Parse is explicitly out of this tool's job — the calling LLM does that before invoking it, per the "LLM understands, script computes" boundary above. Full schema is in `tool_schema.json`.

**Named domain risk, not smoothed over:** symbol names aren't namespaced by physical meaning — `T` means tension on one card, orbital/cyclotron period on two others. Hasn't misfired across the 16-card KB yet; the ambiguous-route logic is a real safety net for it (catches it *if* it happens) but doesn't prevent the underlying collision. Needs semantic tagging before the KB scales past this starter set.

## Scope & Production

**Phasing:** Phase 0 (weeks 1–2) topic scope + 150–300 problem golden set + baseline — currently a 16-problem starter, explicitly not sourced from Prof. Sri/Nik's actual course material yet. Phase 1 (weeks 2–4) MVP pipeline — largely built ahead of schedule as the V2 response. Phase 2 (weeks 4–8) full KB + grade mode + thermo/quantum. Phase 3 conditional on eval plateau (fine-tuning).

**Decisions carried forward from the brief, now seven:** stateless shared service; LLM never computes; mechanics+E&M before quantum; tier-3 fine-tuning deferred until evals plateau; curate→teach→learn→model strictly sequenced; telemetry scoped to named decisions only; and the new one — route on "does exactly one deterministic path exist" rather than "run it twice and diff," because only the former is cheap and actually matches where non-determinism can originate.

**Governance still open, not resolved here:** data processing agreement covering the foundation model API's exposure to parse/plan content, and whether IRB applies given the UCL-study publication angle. Flagged as Q6 to Prof. Sri/Nik, not decided unilaterally — that's a call above this document's pay grade.

## Supervisory retrospective — the five capacities, applied, not just defined

- **PA (Plausibility Auditing):** the wrong note that *should* have been caught earlier and wasn't, on this exact project — a two-word answer to an open scoping question got read as a locked decision, and a supporting justification got invented and attributed to us, which we'd never given. That's the textbook PA failure: verification happened, but only after the wrong note had already been written into a document three reviewers were going to read. Caught this time by us pushing back, not by the process catching it upstream. Worth being blunt about, since it's the cleanest example in this whole project of what PA is for.
- **PF (Problem Formulation):** the mission is "close the silent-computation-error failure mode," not "build an AI tutor" — that's the distinction the Problem Formulation section above depends on, and it's the reason quantum got explicitly deprioritized rather than quietly dropped.
- **TO (Tool Orchestration):** golden set before engine before routing layer — each step needed the last one's output (verified answers to check the engine against; a working engine to check the routing logic against).
- **IJ (Interpretive Judgment):** the calls Claude cannot make, and we correctly didn't try to make either — surface sequencing, whether the DPA/IRB question gets escalated, what "worthy" or "done" means for this project. We left those as open questions to Prof. Sri/Nik, rather than letting them get decided by default or dressed up as done.
- **EI (Executive Integration):** the north star (concepts mastered per student per week) and the guardrail (golden-set accuracy never regresses) are what all of the above has to serve at once — a routing layer that's technically correct but slows down grading, or a golden set that grows without instructor buy-in, both fail EI even if they pass their own local check.

## Compiling — not reached yet

No production deployment spec, no actual wiring into either surface's runtime, no live DPA. That's Phase 4 territory and comes after Prof. Sri/Nik respond to what's already in front of them.
