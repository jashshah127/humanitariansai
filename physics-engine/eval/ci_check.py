"""
One command, every invariant. Run before any push.

    python3 eval/ci_check.py

Exits non-zero on any failure, so it can gate a commit hook or an Action.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))

failures = []


def check(label, fn):
    try:
        ok, detail = fn()
    except Exception as e:  # noqa: BLE001 - a crashing check is a failing check
        ok, detail = False, f"{type(e).__name__}: {e}"
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {detail}")
    if not ok:
        failures.append(label)


def golden_set_16():
    out = subprocess.run([sys.executable, os.path.join(HERE, "demo.py")],
                         capture_output=True, text=True)
    hit = "16/16 problems solved" in out.stdout
    return hit, "16/16 golden-set problems" if hit else "golden set regressed"


def determinism():
    from pipeline import solve_physics_problem
    import json
    runs = {json.dumps(solve_physics_problem("d", "d", dict(m1=4, m2=6, g=9.8),
                                             ["a", "T"], topic_hint="Mechanics"),
                       sort_keys=True) for _ in range(10)}
    return len(runs) == 1, f"10 identical runs" if len(runs) == 1 else "NON-DETERMINISTIC"


def ambiguity_caught():
    from pipeline import solve_physics_problem
    r = solve_physics_problem("amb", "amb",
                              dict(v0=0, a=2.5, t=12, m=2, k=500, x=0.15), ["v"],
                              topic_hint="Mechanics")
    ok = r["route"] == "ambiguous_multiple_deterministic_paths"
    return ok, "conflicting formulas flagged, not silently resolved" if ok else r["route"]


def units_consistent():
    from units import audit_units
    from formula_kb import ALL_CARDS
    from variable_glossary import GLOSSARY
    f = audit_units(ALL_CARDS, GLOSSARY)
    n = len(f["unparseable"]) + len(f["card_vs_glossary"])
    return n == 0, "no unit/dimension contradictions" if n == 0 else f"{n} findings: {f}"


def glossary_covers_cards():
    from variable_glossary import audit_symbol_collisions
    from formula_kb import ALL_CARDS
    a = audit_symbol_collisions(ALL_CARDS)
    ok = not a["undocumented"]
    return ok, ("every card variable is documented; "
                f"{len(a['output_collisions'])} known output collisions under arbitration") \
        if ok else f"parser can't be told to emit: {a['undocumented']}"


def symbolic_coverage():
    from pipeline import symbolic_solution
    from formula_kb import ALL_CARDS
    missing = [c.id for c in ALL_CARDS if symbolic_solution(c)[0] is None]
    ok = not missing
    return ok, (f"all {len(ALL_CARDS)} cards solve symbolically (general formula, not just "
                f"a number)") if ok else f"no symbolic solution for: {missing}"


def identity_scoping_enforced():
    from event_log import EventLog, ScopeViolation
    log = EventLog()
    try:
        log.emit("curate.no_card_match", student_id="s1", unknowns=["v"])
        return False, "SCOPE VIOLATION ALLOWED -- student_id accepted on a none-scope event"
    except ScopeViolation:
        pass
    try:
        log.emit("not.a.registered.event", foo=1)
        return False, "unregistered event accepted"
    except ValueError:
        return True, "student_id rejected on none-scope events; unregistered events rejected"


def phase1_end_to_end():
    out = subprocess.run([sys.executable, os.path.join(HERE, "demo_phase1.py")],
                         capture_output=True, text=True)
    hit = "5/5 problems parsed from raw text AND solved correctly" in out.stdout
    gap = "coverage gaps  : 1" in out.stdout
    if hit and gap:
        return True, "raw text -> answer for all 5 in-scope; out-of-scope one logged as a gap"
    return False, "phase 1 end-to-end regressed"


if __name__ == "__main__":
    print("Phase 0 invariants")
    check("golden set", golden_set_16)
    check("determinism", determinism)
    check("ambiguity routing", ambiguity_caught)
    print("\nPhase 1 invariants")
    check("end-to-end from raw text", phase1_end_to_end)
    check("unit/dimension consistency", units_consistent)
    check("symbolic coverage", symbolic_coverage)
    check("glossary covers every card variable", glossary_covers_cards)
    check("identity scoping enforced", identity_scoping_enforced)

    print()
    if failures:
        print(f"FAILED: {len(failures)} -> {failures}")
        sys.exit(1)
    print("All checks passed.")
