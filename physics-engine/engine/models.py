"""
Core data structures for the physics problem-solving engine.

Mirrors the brief's pipeline exactly:
    Raw problem -> Parse -> Retrieve -> Plan -> Closure check -> Solve -> Verify -> Solution object

A FormulaCard is one entry in the "curated knowledge base of cards (formula, applicability
conditions, common pitfalls)" the brief describes. Retrieve pulls candidates from a list of
these; Plan checks a candidate's conditions against the parsed problem.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional
import sympy as sp


@dataclass
class FormulaCard:
    id: str
    name: str
    topic: str                 # "Mechanics" | "E&M"
    subtopic: str
    applicability: str         # human-readable conditions, logged as an assumption when matched
    required_knowns: list       # symbol names (str) that must appear in the parsed knowns
    solves_for: list            # symbol names (str) this card can solve for
    build_equations: Callable   # knowns_dict (str->float) -> list[sympy.Eq], built fresh per call
    output_units: dict          # symbol name (str) -> unit string, e.g. {"v": "m/s"}
    pitfalls: str
    must_be_positive: list = field(default_factory=list)   # symbol names that should be > 0 physically
    verify_fn: Optional[Callable] = None
    # verify_fn signature: (knowns: dict, solved: dict) -> (bool, str)


def solution_object(problem_id, raw_text, parse_stage, retrieve_stage, plan_stage,
                     solve_stage, verify_stage, final_answer, status, route):
    """Assembles the five pipeline stages into one Solution object, matching node C
    in the brief's system-overview flowchart ('Solution object' -> Solve/Tutor/Grade mode).

    `route` is the V2 addition: an explicit, legible answer to "did this come from the
    deterministic script, or does it need the LLM?" — never left implicit."""
    return {
        "problem_id": problem_id,
        "raw_problem": raw_text,
        "status": status,   # "solved" | "unresolved" | "needs_llm_arbitration"
        "route": route,      # "deterministic_script" | "ambiguous_multiple_deterministic_paths" | "no_deterministic_path"
        "parse": parse_stage,
        "retrieve": retrieve_stage,
        "plan": plan_stage,
        "solve": solve_stage,
        "verify": verify_stage,
        "final_answer": final_answer,
    }
