"""
GRADE MODE -- the third surface, and the Phase 2 deliverable.

Solve mode answers. Tutor mode hints. Grade mode does neither: it takes a student's OWN
work and says where it went wrong. That is a different question from "what is the answer,"
and it is the one instructors actually need.

WHY THIS IS WORTH MORE THAN A RIGHT/WRONG CHECK:
Anything can mark an answer wrong. What a student needs is WHERE they went wrong, and what
an instructor needs is WHICH mistake, aggregated across a class. This module produces both,
using material the engine already has:

  * the verified reference answer (so "wrong" is never a guess);
  * the symbolic general formula (so a student's answer can be tested against specific
    WRONG formulas, not just against the right one);
  * each card's `pitfalls` text, which already names the classic error for that formula.

That last point is the interesting one. Knowing a student got 3.27 instead of 1.96 is
weak feedback. Knowing they used g(m1+m2)/(m1-m2) -- inverted the mass difference, the
exact error the Atwood card warns about -- is teaching.

IDENTITY AND FERPA: grading is the one surface that inherently needs student identity,
which the original brief flagged. This module therefore does NOT store anything. It takes a
submission, returns an assessment, and forgets. Persisting graded work is a separate
decision gated on Q6 (data processing agreement / IRB), still open -- so the capability
exists while the storage question stays unanswered, rather than the reverse.
"""
import sys
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sympy as sp

from pipeline import solve_physics_problem, symbolic_solution
from formula_kb import ALL_CARDS

_CARDS_BY_ID = {c.id: c for c in ALL_CARDS}

# Relative tolerance for calling a student's number "right". Deliberately loose:
# students round intermediate values, and marking 3.2 wrong when the answer is 3.2026
# teaches nothing except that the grader is pedantic.
TOL = 0.02


class Assessment:
    CORRECT = "correct"
    WRONG_VALUE = "wrong_value"
    WRONG_METHOD = "wrong_method"          # matched a known misconception
    INCOMPLETE = "incomplete"              # every value given is right, but some are missing
    NOT_ASSESSABLE = "not_assessable"      # engine couldn't verify a reference


# The badge rule from physics_mode_api.json, applied to grading: "verified" only when the
# grade was made against a symbolically verified reference. not_assessable never is.
_GRADED = {Assessment.CORRECT, Assessment.WRONG_VALUE, Assessment.WRONG_METHOD,
           Assessment.INCOMPLETE}


@dataclass
class GradeResult:
    assessment: str
    per_quantity: dict = field(default_factory=dict)
    reference_answer: Optional[dict] = None
    reference_formula: Optional[str] = None
    divergence: Optional[dict] = None
    misconception: Optional[str] = None
    feedback: str = ""
    confidence: str = ""
    missing: list = field(default_factory=list)   # asked-for quantities the student left out
    verification: str = ""
    badge: str = ""

    def __post_init__(self):
        if self.assessment in _GRADED:
            self.verification = "verified"
            self.badge = "Verified - graded against a symbolically checked answer"
        else:
            self.verification = "unverified"
            self.badge = "Unverified - not graded"

    def to_dict(self):
        return asdict(self)


def _close(a, b, tol=TOL):
    if a is None or b is None:
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) / abs(b) < tol


def _candidate_misconceptions(card, knowns, correct_value, target):
    """Generate plausible WRONG values a student might produce for `target`, by applying
    known error patterns to the card's own symbolic solution.

    This is the part that turns grading into diagnosis. Rather than only asking "is the
    student's number right", it asks "is the student's number what you'd get from a
    specific, nameable mistake" -- and the mistakes are derived from the formula itself,
    not from a hand-written list per problem.

    Patterns implemented reflect errors this KB's cards explicitly warn about:
      sign_flip        -- reversed a difference (m1-m2 vs m2-m1); the Atwood pitfall
      reciprocal       -- inverted the whole expression; classic with periods/frequencies
      dropped_factor_2 -- lost or gained a factor of 2; escape vs orbital velocity,
                          open vs closed pipe
      sqrt_forgotten   -- returned the argument instead of its square root
    """
    sym_sols, simplified, _ = symbolic_solution(card)
    if not simplified:
        return []
    expr = simplified[0].get(target)
    if expr is None:
        return []

    subs = {sp.Symbol(k): v for k, v in knowns.items()}
    out = []

    def evaluate(e, label, explanation):
        try:
            val = float(sp.N(e.subs(subs)))
        except Exception:
            return
        if val == 0 or not _finite(val):
            return
        if _close(val, correct_value):
            return          # not a distinguishable error
        out.append({"value": val, "pattern": label, "explanation": explanation})

    # Plain negation -- the single most common sign error, and the one a student gets
    # by writing (m1 - m2) where the formula wants (m2 - m1) in a lone difference.
    evaluate(-expr, "sign_flip",
             "reversed a difference -- check the order of subtraction")

    # Flip differences ONE AT A TIME. Flipping every Add at once is wrong: negating both
    # numerator and denominator cancels out and reproduces the original expression, so
    # the candidate is identical to the correct answer and nothing is ever detected.
    # Found exactly that way -- a sign-flipped Atwood answer went unmatched.
    try:
        for sub in expr.atoms(sp.Add):
            if len(sub.args) == 2:
                evaluate(expr.subs(sub, -sub), "sign_flip",
                         "reversed a difference -- check the order of subtraction")
    except Exception:
        pass

    evaluate(1 / expr, "reciprocal",
             "inverted the relationship -- check which quantity is in the numerator")
    evaluate(expr * 2, "factor_2_high",
             "answer is off by a factor of 2 -- check for a missing or extra 1/2")
    evaluate(expr / 2, "factor_2_low",
             "answer is off by a factor of 2 -- check for a missing or extra 1/2")
    # sqrt(2) factors show up wherever an energy relation sits next to a force relation.
    # The escape-vs-orbital velocity confusion is exactly this, and the gravitation card
    # names it, so it is worth detecting rather than just warning about after the fact.
    evaluate(expr / sp.sqrt(2), "sqrt2_low",
             "answer is off by a factor of sqrt(2) -- a classic sign of using the orbital "
             "relation where the escape relation applies, or vice versa")
    evaluate(expr * sp.sqrt(2), "sqrt2_high",
             "answer is off by a factor of sqrt(2) -- a classic sign of using the orbital "
             "relation where the escape relation applies, or vice versa")

    if isinstance(expr, sp.Pow) and expr.exp == sp.Rational(1, 2):
        evaluate(expr.base, "sqrt_forgotten",
                 "returned the quantity under the square root without taking the root")

    return out


def _finite(x):
    return x == x and abs(x) != float("inf")


def grade(problem_id, raw_problem, knowns, unknowns, student_answer,
          student_steps=None, topic_hint=None):
    """student_answer: {quantity_name: numeric_value} -- what the student submitted.
    student_steps:  optional {quantity_name: value} of intermediate results, used to
                    locate WHERE the work diverged rather than only that it did.

    Returns a GradeResult. Never stores anything.
    """
    solution = solve_physics_problem(problem_id, raw_problem, knowns, unknowns,
                                     topic_hint=topic_hint)

    # If the engine cannot verify a reference, it must not grade. Marking a student
    # wrong against an unverified reference is worse than declining to grade at all --
    # it is the same confidently-wrong failure this project exists to prevent, aimed
    # at someone's transcript.
    # route alone is not enough: a card can close and still fail its own verification
    # ("solved -- flagged for review"). Grading against that would break the same rule.
    if solution["route"] != "deterministic_script" or solution["status"] != "solved":
        return GradeResult(
            assessment=Assessment.NOT_ASSESSABLE,
            feedback=("No verified reference solution exists for this problem, so it "
                      "cannot be graded automatically. Routed for human review."),
            confidence="none",
        )

    card = _CARDS_BY_ID[solution["retrieve"]["matched"]]
    # The card solves for everything it can (an orbit card returns r, v and T), but the
    # student was only asked for `unknowns`. Grade, report and reveal only those, or a
    # student who answered the one question asked gets told they left two out.
    asked = [u for u in unknowns if u in solution["final_answer"]] or list(solution["final_answer"])
    reference = {k: solution["final_answer"][k] for k in asked}
    symbolic = solution["solve"].get("symbolic_answer") or {}

    # If the reference came back as a formula rather than a number, the problem was
    # stated symbolically and there is nothing numeric to grade against. Comparing a
    # student's number to an expression would crash, or worse, silently coerce and mark
    # them wrong against a meaningless comparison.
    if solution["solve"].get("symbolic_mode"):
        return GradeResult(
            assessment=Assessment.NOT_ASSESSABLE,
            reference_answer=reference,
            reference_formula=card.name,
            # The reference is in reference_answer; it is NOT repeated in feedback, so the
            # UI decides when a student sees it (see ui_guidance.grade in the contract).
            feedback=("This problem is written with symbols, not numbers, so its answer is a "
                      "formula. Only numeric answers can be graded for now."),
            confidence="none",
        )

    per_quantity, wrong, missing = {}, [], []
    for name, ref_val in reference.items():
        if name not in student_answer:
            missing.append(name)
            continue
        got = student_answer[name]
        ok = _close(got, ref_val)
        per_quantity[name] = {"submitted": got, "reference": ref_val, "correct": ok}
        if not ok:
            wrong.append((name, got, ref_val))

    if not per_quantity:
        # The problem IS gradable; the student just sent nothing for it. Calling that
        # not_assessable would put an "Unverified" badge on a verified problem.
        return GradeResult(
            assessment=Assessment.INCOMPLETE,
            reference_answer=reference,
            reference_formula=card.name,
            missing=missing,
            feedback="No answer was given for: " + ", ".join(missing) + ".",
            confidence="high",
        )

    if not wrong and missing:
        return GradeResult(
            assessment=Assessment.INCOMPLETE,
            per_quantity=per_quantity,
            reference_answer=reference,
            reference_formula=card.name,
            missing=missing,
            feedback=("Every value you gave is right. Still missing: "
                      + ", ".join(missing) + "."),
            confidence="high",
        )

    if not wrong:
        return GradeResult(
            assessment=Assessment.CORRECT,
            per_quantity=per_quantity,
            reference_answer=reference,
            reference_formula=card.name,
            feedback=(f"Correct. Solved using {card.name}; every value matches a "
                      f"symbolically verified reference."),
            confidence="high",
        )

    # Wrong -- try to name the mistake rather than only report it.
    name, got, ref_val = wrong[0]
    misconception, explanation = None, None
    for cand in _candidate_misconceptions(card, knowns, ref_val, name):
        if _close(got, cand["value"]):
            misconception, explanation = cand["pattern"], cand["explanation"]
            break

    divergence = None
    if student_steps:
        # Walk intermediate values and find the FIRST that departs from the reference.
        # Everything after a first error is downstream of it, so reporting the earliest
        # divergence is the only useful pointer.
        for step_name, step_val in student_steps.items():
            if step_name in reference and not _close(step_val, reference[step_name]):
                divergence = {"first_wrong_quantity": step_name,
                              "submitted": step_val,
                              "reference": reference[step_name]}
                break

    if misconception:
        feedback = (f"Not correct. The value submitted for {name} matches what you get "
                    f"from a specific error: {explanation}. "
                    f"For this problem, {card.pitfalls}")
        assessment = Assessment.WRONG_METHOD
    else:
        # No numbers in this text: the correct value is in reference_answer, and the UI
        # decides when to show it. Putting it here would show it on the first wrong try.
        # (It also removes the old `{ref_val:.4g}` format, which crashed on sympy values.)
        general = symbolic.get(name)
        feedback = (f"Not correct. Your value for {name} doesn't match the verified answer."
                    + (f" The relationship is {name} = {general}." if general else "")
                    + f" Worth checking: {card.pitfalls}")
        assessment = Assessment.WRONG_VALUE

    if missing:
        feedback += " You also left out: " + ", ".join(missing) + "."

    return GradeResult(
        assessment=assessment,
        per_quantity=per_quantity,
        reference_answer=reference,
        reference_formula=card.name,
        divergence=divergence,
        misconception=misconception,
        feedback=feedback,
        confidence="high",
        missing=missing,
    )
