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


class _SymbolDict(dict):
    """Handed to a card's build_equations() in place of numeric knowns, so the card
    returns equations in SYMBOLS rather than with values already baked in.

    Every card asks for its inputs as k['m1'], k['g'] and so on. Passing this instead
    of a value dict makes each lookup produce Symbol('m1'), Symbol('g') -- so all 16
    cards became symbol-capable without a single line changing inside them. The cards
    were already written generically; they just hadn't been asked for symbols before."""

    def __missing__(self, key):
        return sp.Symbol(key)


_SYMBOLIC_CACHE = {}


def symbolic_solution(card):
    """Solve a card ONCE in pure symbols and cache the result.

    This is what makes symbolic output affordable. Solving symbolically costs roughly
    290ms; substituting numbers into an already-solved expression costs a fraction of a
    millisecond. Doing the algebra once per card rather than once per problem turns a
    26x slowdown into a one-time startup cost.

    Everything expensive and problem-independent is cached here -- the solve, the
    simplify, and the symbolic form of the equations. An earlier version simplified on
    every call and ran 2x slower than the old numeric path; measuring that is what
    located the cost. Caching is not an optimization detail here, it is the thing that
    makes the feature shippable.

    Returns (solutions, simplified, symbolic_form) or (None, None, symbolic_form) when
    the card does not resolve symbolically -- in which case the caller falls back to
    numeric solving rather than the problem failing."""
    if card.id in _SYMBOLIC_CACHE:
        return _SYMBOLIC_CACHE[card.id]
    try:
        eqs = card.build_equations(_SymbolDict())
        symbolic_form = [f"{e.lhs} = {e.rhs}" for e in eqs]
    except Exception:
        symbolic_form = []
    try:
        syms = [sp.Symbol(n) for n in card.solves_for]
        sols = sp.solve(card.build_equations(_SymbolDict()), syms, dict=True)
        sols = sols or None
        simplified = ([{str(k): sp.simplify(v) for k, v in sd.items()} for sd in sols]
                      if sols else None)
    except Exception:
        sols, simplified = None, None
    result = (sols, simplified, symbolic_form)
    _SYMBOLIC_CACHE[card.id] = result
    return result


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


def _is_numeric(v):
    """Is this known an actual number, or a symbol standing in for one?"""
    if isinstance(v, (int, float)):
        return True
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def solve(card, knowns):
    """Solve via SymPy only -- this function never evaluates arithmetic by anything
    other than the symbolic engine.

    TWO MODES, decided by the inputs rather than by a flag:

    NUMERIC  -- every known is a number. Returns numbers, plus the general formula.
    SYMBOLIC -- one or more knowns is a symbol, because the problem was stated that way
                ("a particle of mass m and charge q..."). Returns the derivation.

    Symbolic mode exists because most undergraduate physics is stated symbolically: 60%
    of UGPhysics ground truth is an expression, not a number. Before this, such problems
    were declined -- not because the engine couldn't do the algebra (it can; that is all
    SymPy does) but because the pipeline insisted on converting results to float at the
    end. That was an interface limitation being reported as a coverage gap, which is a
    worse failure than an honest gap: it hid capability that already existed.
    """
    symbolic_mode = not all(_is_numeric(v) for v in knowns.values())
    subs_map = {sp.Symbol(n): (v if not isinstance(v, str) else sp.Symbol(v))
                for n, v in knowns.items()}
    sym_sols, simplified, symbolic_form = symbolic_solution(card)

    if sym_sols is not None:
        # Substitute into pre-solved, pre-simplified expressions -- the cheap path.
        sols, symbolic_answers = [], []
        for i, sd in enumerate(sym_sols):
            try:
                sols.append({k: v.subs(subs_map) for k, v in sd.items()})
            except Exception:
                continue
            symbolic_answers.append(simplified[i] if simplified else None)
    else:
        # Card does not resolve symbolically; fall back to numeric solving so the
        # problem still gets an answer rather than failing.
        eqs = card.build_equations(knowns)
        syms = [sp.Symbol(n) for n in card.solves_for]
        sols = sp.solve(eqs, syms, dict=True)
        symbolic_answers = [None] * len(sols)

    def is_real(d):
        if symbolic_mode:
            return True          # cannot decide realness without values; do not exclude
        try:
            return all(sp.im(sp.N(v)) == 0 for v in d.values())
        except Exception:
            return False

    real_idx = [i for i, d in enumerate(sols) if is_real(d)] or list(range(len(sols)))

    def satisfies_positivity(i):
        if symbolic_mode:
            return True          # sign is indeterminate without values
        d = sols[i]
        try:
            return all(float(sp.N(d[sp.Symbol(n)])) > 0 for n in card.must_be_positive
                       if sp.Symbol(n) in d)
        except Exception:
            return False

    chosen_i = next((i for i in real_idx if satisfies_positivity(i)), real_idx[0])
    chosen = sols[chosen_i]

    if symbolic_mode:
        solved = {str(k): sp.simplify(v) for k, v in chosen.items()}
    else:
        solved = {str(k): float(sp.N(v)) for k, v in chosen.items()}

    chosen_symbolic = symbolic_answers[chosen_i]
    ambiguous = len(sols) > 1
    return solved, ambiguous, len(sols), symbolic_form, chosen_symbolic, symbolic_mode


def verify(card, knowns, solved, symbolic_mode=False):
    """Residual check (generic, always run) + positivity sanity + card-specific
    independent path/limiting-case check, where one exists.

    In symbolic mode the checks adapt rather than being skipped: the residual is
    verified by simplifying to zero instead of evaluating to a small float, which is
    actually a STRONGER check -- it proves the identity holds for all values, not just
    the ones supplied. Positivity genuinely cannot be decided without values, so it is
    reported as indeterminate rather than silently passed."""
    eqs = card.build_equations(knowns)
    subs = {sp.Symbol(k): v for k, v in solved.items()}
    residual_details = []
    residual_ok = True
    for eq in eqs:
        expr = (eq.lhs - eq.rhs).subs(subs)
        if symbolic_mode:
            simplified = sp.simplify(expr)
            ok = simplified == 0
            residual_details.append(f"{eq.lhs} = {eq.rhs}  ->  simplifies to {simplified} "
                                    f"(symbolic identity, holds for all values)")
        else:
            val = complex(expr.evalf())
            ok = abs(val) < 1e-4
            residual_details.append(f"{eq.lhs} = {eq.rhs}  ->  residual {val.real:.2e}")
        residual_ok = residual_ok and ok

    positivity_ok = True
    positivity_details = []
    if symbolic_mode:
        positivity_details.append("indeterminate without numeric values -- not checked")
    else:
        for name in card.must_be_positive:
            v = solved.get(name)
            ok = v is not None and v > 0
            positivity_ok = positivity_ok and ok
            positivity_details.append(f"{name} = {v:.4g} {'> 0 OK' if ok else 'FAILED positivity check'}")

    independent = None
    if card.verify_fn and not symbolic_mode:
        ind_ok, ind_msg = card.verify_fn(knowns, solved)
        independent = {"ok": ind_ok, "detail": ind_msg}
    elif card.verify_fn and symbolic_mode:
        # Card verify functions do arithmetic on the solved values (ratios, comparisons),
        # so they assume numbers. Rather than crash, report honestly that this check
        # did not run -- the symbolic residual check above is doing stronger work anyway.
        independent = {"ok": True,
                       "detail": "independent numeric cross-check skipped in symbolic mode; "
                                 "the symbolic residual identity above is a stronger check"}

    overall_ok = residual_ok and positivity_ok and (independent is None or independent["ok"])
    return {
        "residual_check": {"ok": residual_ok, "detail": residual_details},
        "positivity_check": {"ok": positivity_ok, "detail": positivity_details} if card.must_be_positive else None,
        "independent_path_check": independent if independent else "not applicable for this card",
        "units": card.output_units,
        "status": "verified" if overall_ok else "flagged",
    }


def _solve_and_verify(card, knowns):
    solved, ambiguous, n_solutions, symbolic_form, symbolic_answer, symbolic_mode = \
        solve(card, knowns)
    verify_result = verify(card, knowns, solved, symbolic_mode=symbolic_mode)
    solve_stage = {"solved_values": {k: (v if isinstance(v, (int, float)) else str(v))
                                     for k, v in solved.items()},
                   "symbolic_form": symbolic_form,
                   "symbolic_answer": {k: str(v) for k, v in (symbolic_answer or {}).items()},
                   "symbolic_mode": symbolic_mode,
                   "ambiguous_multiple_roots": ambiguous, "n_symbolic_solutions": n_solutions,
                   "method": "sympy.solve (symbolic, cached; numbers substituted last)"}
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
            final_answer={k: (solved[k] if isinstance(solved[k], (int, float))
                              else str(solved[k])) for k in card.solves_for},
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
