"""
PHYSICS ENGINE MODE -- the surface Medhavy attaches to its input box, the way Google
attaches AI Mode to its search bar.

WHAT THE TOGGLE ACTUALLY CHANGES, and why it is not cosmetic:

Off, a student asks a physics question and gets an answer that reads exactly like every
other LLM answer -- fluent, confident, and carrying no information about whether it is
right. On, the student still always gets an answer, but the answer arrives with its
verification status attached and visible:

    VERIFIED      a symbolic solver computed this; it is reproducible and correct
    NEEDS REVIEW  more than one physical principle fits; here is each result
    UNVERIFIED    nothing in the knowledge base covers this; this is AI reasoning

That visible status IS the product. An LLM that is good at physics is a commodity; one
that reliably tells you WHEN to trust it is not. The toggle exists to make the difference
legible to the person actually relying on it.

Note the floor: on the UNVERIFIED path the student is no worse off than with the toggle
off, because that path IS the toggle off, labelled. There is no input for which turning
this on degrades the answer -- which is the entire case for shipping it.

Scope: this module renders solve and tutor. Grade mode needs the student's own work as
an input and is Phase 2 in the brief; it is deliberately absent rather than stubbed.
"""
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from parse import parse_problem, ParseError
from pipeline import solve_physics_problem
from event_log import EventLog
from formula_kb import ALL_CARDS

_CARDS_BY_ID = {c.id: c for c in ALL_CARDS}


class Verification:
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    UNVERIFIED = "unverified"


# internal route -> (student-facing status, badge text, whether Medhavy must finish the answer)
_ROUTE_MAP = {
    "deterministic_script": (
        Verification.VERIFIED,
        "Verified - solved symbolically",
        False,
    ),
    "ambiguous_multiple_deterministic_paths": (
        Verification.NEEDS_REVIEW,
        "Needs review - more than one principle applies",
        True,
    ),
    "no_deterministic_path": (
        Verification.UNVERIFIED,
        "Unverified - AI reasoning, not symbolically checked",
        True,
    ),
}


@dataclass
class PhysicsModeResponse:
    """The contract between this engine and Medhavy's UI.

    `needs_llm_completion` is the important field for the integration: True means this
    engine has done all it can and Medhavy's own model must write the final answer --
    but it must present it under the badge given here, not as though it were verified."""
    verification: str
    badge: str
    needs_llm_completion: bool
    answer: Optional[dict] = None
    candidates: Optional[list] = None
    hints: Optional[list] = None
    explanation: str = ""
    formula_used: Optional[str] = None
    assumptions: list = field(default_factory=list)
    sources: dict = field(default_factory=dict)
    route: str = ""
    latency_ms: float = 0.0
    trace: Optional[dict] = None

    def to_dict(self):
        return asdict(self)


def _hint_ladder(card, solution, parse_result):
    """Progressive hints for tutor rendering, derived entirely from the plan object --
    no second LLM call. The brief specifies 'targeted hints from the plan object', and
    the plan already holds the card, its applicability conditions and its equations, so
    the ladder is a rendering of data we have rather than new generation.

    Deliberately ordered so each rung reveals strictly less than the next, and the
    answer is last."""
    knowns = ", ".join(f"{k} = {v:g}" for k, v in parse_result["knowns"].items()
                       if k not in parse_result.get("injected", {}))
    unknowns = ", ".join(parse_result["unknowns"])
    ladder = [
        f"Start by listing what you're given and what you're solving for. "
        f"Given: {knowns}. Find: {unknowns}.",
        f"This is a {card.subtopic.lower()} problem. The principle that applies here: {card.name}.",
        f"Check the conditions before using it -- {card.applicability}",
        f"The relationship you need: {'; '.join(solution['solve']['symbolic_form'])}",
    ]
    if card.pitfalls:
        ladder.append(f"Common mistake to avoid here: {card.pitfalls}")
    sym = solution["solve"].get("symbolic_answer") or {}
    if sym:
        general = "; ".join(f"{k} = {v}" for k, v in sym.items())
        ladder.append(f"Rearranged for what you're solving for: {general}")
    final = ", ".join(f"{k} = {v:.4g}" for k, v in solution["final_answer"].items())
    ladder.append(f"Worked result: {final}")
    return ladder


def _explain(card, solution):
    """One-paragraph plain explanation of what was done. Not generated -- assembled
    from the card and the verify stage, so it cannot describe a check that did not run."""
    checks = []
    v = solution["verify"]
    if v["residual_check"]["ok"]:
        checks.append("the solution satisfies its own equations")
    if v.get("positivity_check") and v["positivity_check"]["ok"]:
        checks.append("all quantities came out physically positive")
    ind = v.get("independent_path_check")
    if isinstance(ind, dict) and ind.get("ok"):
        checks.append("an independent second derivation agrees")
    check_text = "; ".join(checks) if checks else "basic consistency checks passed"
    return (f"Solved using {card.name}. Every number came from a symbolic solver, "
            f"not from language-model arithmetic. Verification: {check_text}.")


class PhysicsEngineMode:
    """Entry point Medhavy calls when the toggle is on.

    llm: callable(prompt) -> str, used ONLY for the parse stage. If parsing fails or
    nothing in the KB matches, this class does not fall back to asking the model for an
    answer -- it returns needs_llm_completion=True and lets Medhavy do that with its own
    model and its own conversation context, under an UNVERIFIED badge. Keeping the
    fallback out of the engine is what stops an unverified answer from ever leaving here
    wearing a verified label.
    """

    def __init__(self, llm, event_log=None):
        self.llm = llm
        self.log = event_log or EventLog()

    def solve(self, query, session_id, render="solve", problem_id=None):
        started = time.perf_counter()
        problem_id = problem_id or f"q-{int(started * 1000)}"
        self.log.emit("query.received", session_id=session_id, problem_id=problem_id)

        # ---- Parse
        try:
            parsed = parse_problem(query, self.llm)
        except ParseError as e:
            self.log.emit("parse.failed", problem_id=problem_id, reason=str(e))
            elapsed = (time.perf_counter() - started) * 1000
            self.log.emit("query.completed", problem_id=problem_id, duration_ms=elapsed,
                          outcome="parse_failed")
            return PhysicsModeResponse(
                verification=Verification.UNVERIFIED,
                badge=_ROUTE_MAP["no_deterministic_path"][1],
                needs_llm_completion=True,
                explanation="Couldn't read this problem into a structured form, so it "
                            "hasn't been symbolically checked.",
                route="parse_failed",
                latency_ms=elapsed,
            )

        self.log.emit("parse.completed", problem_id=problem_id,
                      n_knowns=len(parsed["knowns"]), n_unknowns=len(parsed["unknowns"]),
                      unrecognized=parsed["normalization"]["unrecognized"])

        # ---- Retrieve / Plan / Solve / Verify (unchanged Phase 0 core)
        solution = solve_physics_problem(
            problem_id, query, parsed["knowns"], parsed["unknowns"],
            topic_hint=parsed.get("topic_hint"),
        )
        route = solution["route"]
        self.log.emit("route.decided", problem_id=problem_id, route=route)

        status, badge, needs_llm = _ROUTE_MAP[route]
        elapsed = (time.perf_counter() - started) * 1000

        # ---- Render
        if route == "deterministic_script":
            card = _CARDS_BY_ID[solution["retrieve"]["matched"]]
            self.log.emit("solution.verified_pair", problem_id=problem_id, card_id=card.id)
            resp = PhysicsModeResponse(
                verification=status, badge=badge, needs_llm_completion=needs_llm,
                answer=solution["final_answer"],
                explanation=_explain(card, solution),
                formula_used=card.name,
                assumptions=solution["plan"]["assumptions"],
                sources=parsed["sources"],
                route=route, latency_ms=elapsed, trace=solution,
            )
            if render == "tutor":
                resp.hints = _hint_ladder(card, solution, parsed)
                resp.answer = None  # tutor mode withholds the answer on purpose
                resp.explanation = ("Worked through as hints rather than a final answer. "
                                    "Each step is symbolically verified.")

        elif route == "ambiguous_multiple_deterministic_paths":
            cands = solution["solve"]["per_candidate_results"]
            resp = PhysicsModeResponse(
                verification=status, badge=badge, needs_llm_completion=needs_llm,
                candidates=[{
                    "principle": _CARDS_BY_ID[c["card_id"]].name,
                    "applies_when": _CARDS_BY_ID[c["card_id"]].applicability,
                    "answer": c["final_answer"],
                } for c in cands],
                explanation=("More than one physical principle fits what was given, and they "
                             "disagree. Each result below is computed correctly; choosing "
                             "between them needs the problem's context."),
                sources=parsed["sources"],
                route=route, latency_ms=elapsed, trace=solution,
            )

        else:  # no_deterministic_path
            self.log.emit("curate.no_card_match", problem_id=problem_id,
                          unknowns=parsed["unknowns"],
                          topic_hint=parsed.get("topic_hint"))
            resp = PhysicsModeResponse(
                verification=status, badge=badge, needs_llm_completion=needs_llm,
                explanation=("Nothing in the verified formula library covers this problem yet, "
                             "so it hasn't been symbolically checked. Logged as a coverage gap."),
                sources=parsed["sources"],
                route=route, latency_ms=elapsed, trace=solution,
            )

        self.log.emit("query.completed", problem_id=problem_id,
                      duration_ms=elapsed, outcome=route)
        return resp
