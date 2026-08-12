"""
The physics problem-solving engine's pipeline logic.

    solve_physics_problem(...) is the single function that would be "exposed as a tool
    that Medhavy calls" per the brief. It assumes Parse has already happened
    (knowns/unknowns extracted) — in production that's an LLM (Claude) reasoning over the
    raw problem text, per the brief's own architecture ("LLM handles problem understanding
    ... a symbolic/numeric solver handles computation"). This module is that solver: it
    never evaluates arithmetic by guessing, only via sympy.
"""
import sympy as sp
from formula_kb import ALL_CARDS
from models import solution_object

TOL = 1e-6


def retrieve(unknowns_wanted, knowns_available, topic_hint=None):
    """Pull candidate formula cards that can solve for at least one requested unknown.
    Deliberately does NOT check whether required knowns are actually present — that
    check belongs to Plan's closure check, so a missing-known problem surfaces as a
    diagnosable 'gap' with a reason, not a silent retrieval miss."""
    wanted = set(unknowns_wanted)
    have = set(knowns_available)
    candidates = [card for card in ALL_CARDS if set(card.solves_for) & wanted]
    candidates.sort(key=lambda c: (
        0 if (topic_hint and c.topic == topic_hint) else 1,
        0 if set(c.required_knowns) <= have else 1,
    ))
    return candidates


def plan(card, knowns):
    """Match the card's conditions against what's known, log assumptions, and run the
    closure check (can every requested unknown actually be pinned down?)."""
    missing = [k for k in card.required_knowns if k not in knowns]
    assumptions = [card.applicability]
    if missing:
        return {"matched_card": card.id, "assumptions": assumptions,
                "closure": "gap", "reason": f"missing knowns: {missing}"}

    try:
        eqs = card.build_equations(knowns)
        unknown_syms = [sp.Symbol(name) for name in card.solves_for]
        sols = sp.solve(eqs, unknown_syms, dict=True)
    except Exception as e:
        return {"matched_card": card.id, "assumptions": assumptions,
                "closure": "gap", "reason": f"solver raised {type(e).__name__}: {e}"}

    if not sols:
        return {"matched_card": card.id, "assumptions": assumptions,
                "closure": "gap", "reason": "system did not resolve to a determinate solution"}
    return {"matched_card": card.id, "assumptions": assumptions,
            "closure": "solvable", "reason": None}


def solve(card, knowns):
    """Solve via SymPy only — this function never evaluates arithmetic by anything
    other than the symbolic engine. Returns both the numeric result AND the symbolic
    equations actually used, so the output is 'numeric and symbolic', not just a number."""
    eqs = card.build_equations(knowns)
    symbolic_form = [f"{eq.lhs} = {eq.rhs}" for eq in eqs]
    unknown_syms = [sp.Symbol(name) for name in card.solves_for]
    sols = sp.solve(eqs, unknown_syms, dict=True)

    def is_real(d):
        return all(sp.im(v) == 0 for v in d.values())

    real_sols = [d for d in sols if is_real(d)] or sols

    def satisfies_positivity(d):
        return all(float(d[sp.Symbol(name)]) > 0 for name in card.must_be_positive
                   if sp.Symbol(name) in d)

    chosen = next((d for d in real_sols if satisfies_positivity(d)), real_sols[0])
    solved = {str(sym): float(val) for sym, val in chosen.items()}
    ambiguous = len(sols) > 1
    return solved, ambiguous, len(sols), symbolic_form


def verify(card, knowns, solved):
    """Residual check (generic, always run) + positivity sanity + card-specific
    independent path/limiting-case check, where one exists."""
    eqs = card.build_equations(knowns)
    subs = {sp.Symbol(k): v for k, v in solved.items()}
    residual_details = []
    residual_ok = True
    for eq in eqs:
        val = complex((eq.lhs - eq.rhs).subs(subs).evalf())
        ok = abs(val) < 1e-4
        residual_ok = residual_ok and ok
        residual_details.append(f"{eq.lhs} = {eq.rhs}  ->  residual {val.real:.2e}")

    positivity_ok = True
    positivity_details = []
    for name in card.must_be_positive:
        v = solved.get(name)
        ok = v is not None and v > 0
        positivity_ok = positivity_ok and ok
        positivity_details.append(f"{name} = {v:.4g} {'> 0 OK' if ok else 'FAILED positivity check'}")

    independent = None
    if card.verify_fn:
        ind_ok, ind_msg = card.verify_fn(knowns, solved)
        independent = {"ok": ind_ok, "detail": ind_msg}

    overall_ok = residual_ok and positivity_ok and (independent is None or independent["ok"])
    return {
        "residual_check": {"ok": residual_ok, "detail": residual_details},
        "positivity_check": {"ok": positivity_ok, "detail": positivity_details} if card.must_be_positive else None,
        "independent_path_check": independent if independent else "not applicable for this card",
        "units": card.output_units,
        "status": "verified" if overall_ok else "flagged",
    }


def _solve_and_verify(card, knowns):
    solved, ambiguous, n_solutions, symbolic_form = solve(card, knowns)
    verify_result = verify(card, knowns, solved)
    solve_stage = {"solved_values": solved, "symbolic_form": symbolic_form,
                   "ambiguous_multiple_roots": ambiguous, "n_symbolic_solutions": n_solutions,
                   "method": "sympy.solve"}
    return solved, solve_stage, verify_result


def solve_physics_problem(problem_id, raw_text, knowns, unknowns, topic_hint=None):
    """The single entry point — this is what gets exposed as the tool. V2: makes the
    script-vs-LLM decision an explicit, inspectable `route` instead of leaving it implicit.

    Routing rule (this is the actual determinism fix, not a cosmetic one):
      - Exactly one card reaches closure  -> route="deterministic_script". Same input will
        ALWAYS produce this exact output — nothing here is sampled or guessed.
      - Zero cards reach closure          -> route="no_deterministic_path". No script can
        own this problem yet; an LLM (or a human, via the curation queue) has to handle it,
        and every such call is logged as a coverage gap, not silently patched over.
      - More than one card reaches closure at once for the SAME requested unknown -> that
        IS the "same problem, different outputs" case from the V2 note: two independent
        deterministic paths both claim an answer. Rather than picking one arbitrarily (which
        would be non-deterministic in effect, just hidden), this returns ALL candidate
        answers and flags route="ambiguous_multiple_deterministic_paths" for LLM/human
        arbitration on which formula actually applies.
    """
    candidates = retrieve(unknowns, list(knowns.keys()), topic_hint)

    if not candidates:
        return solution_object(
            problem_id, raw_text,
            parse_stage={"knowns": knowns, "unknowns": unknowns},
            retrieve_stage={"candidates_considered": []},
            plan_stage={"closure": "gap", "reason": "no card matched"},
            solve_stage=None, verify_stage=None, final_answer=None,
            status="unresolved", route="no_deterministic_path",
        )

    attempts, closing = [], []
    for card in candidates:
        plan_result = plan(card, knowns)
        attempts.append({"card_id": card.id, "closure": plan_result["closure"], "reason": plan_result["reason"]})
        if plan_result["closure"] == "solvable":
            closing.append((card, plan_result))

    if not closing:
        return solution_object(
            problem_id, raw_text,
            parse_stage={"knowns": knowns, "unknowns": unknowns},
            retrieve_stage={"candidates_considered": [c.id for c in candidates]},
            plan_stage={"closure": "gap", "reason": "all candidates failed closure", "attempts": attempts},
            solve_stage=None, verify_stage=None, final_answer=None,
            status="unresolved", route="no_deterministic_path",
        )

    if len(closing) == 1:
        card, plan_result = closing[0]
        solved, solve_stage, verify_result = _solve_and_verify(card, knowns)
        return solution_object(
            problem_id, raw_text,
            parse_stage={"knowns": knowns, "unknowns": unknowns},
            retrieve_stage={"candidates_considered": [c.id for c in candidates],
                            "matched": card.id, "other_attempts": [a for a in attempts if a["card_id"] != card.id]},
            plan_stage=plan_result,
            solve_stage=solve_stage,
            verify_stage=verify_result,
            final_answer={k: solved[k] for k in card.solves_for},
            status="solved" if verify_result["status"] == "verified" else "solved — flagged for review",
            route="deterministic_script",
        )

    # More than one candidate reached closure: solve all of them and report every answer —
    # this is the concrete, provable version of "same problem, different outputs."
    per_candidate = []
    for card, plan_result in closing:
        solved, solve_stage, verify_result = _solve_and_verify(card, knowns)
        per_candidate.append({
            "card_id": card.id, "card_name": card.name,
            "final_answer": {k: solved[k] for k in card.solves_for},
            "verify_status": verify_result["status"],
        })
    shared_keys = set(closing[0][0].solves_for)
    for card, _ in closing[1:]:
        shared_keys &= set(card.solves_for)
    disagreement = {}
    for k in shared_keys:
        vals = {pc["card_id"]: pc["final_answer"][k] for pc in per_candidate}
        if max(vals.values()) - min(vals.values()) > 1e-6:
            disagreement[k] = vals

    return solution_object(
        problem_id, raw_text,
        parse_stage={"knowns": knowns, "unknowns": unknowns},
        retrieve_stage={"candidates_considered": [c.id for c in candidates],
                        "multiple_matched": [c.id for c, _ in closing]},
        plan_stage={"closure": "solvable — but ambiguous", "attempts": attempts},
        solve_stage={"per_candidate_results": per_candidate},
        verify_stage={"disagreement_on_shared_unknowns": disagreement or "candidates agree numerically, "
                      "but two independent formulas both claiming this unknown is itself the signal — "
                      "agreement here may be coincidental to these particular input values"},
        final_answer=None,
        status="needs_llm_arbitration",
        route="ambiguous_multiple_deterministic_paths",
    )
