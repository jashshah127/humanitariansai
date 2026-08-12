"""
Phase 1 end-to-end demo: RAW PROBLEM TEXT in, rendered answer out.

Phase 0 started at Retrieve and assumed knowns/unknowns were already extracted. This
starts one stage earlier, at raw text, which is what Phase 1 adds.

The canned parses below deliberately use NATURAL variable names -- `initial_velocity`,
`angle`, `resistance` -- rather than the card names (`v0`, `theta_deg`, `R`). That is
what a real model actually emits, and it means this demo exercises the normalization
layer instead of quietly bypassing it by pre-writing the right answer.

WHAT THIS PROVES: the plumbing -- normalization, constant injection, routing, rendering,
event logging, identity scoping.
WHAT IT DOES NOT PROVE: that a real LLM parses well. That needs the API and is the
first open item in the Phase 1 README.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine"))

from parse import StubLLM
from physics_mode import PhysicsEngineMode, Verification
from event_log import EventLog, ScopeViolation
from variable_glossary import audit_symbol_collisions
from formula_kb import ALL_CARDS

# Canned parses keyed by a distinctive phrase. Natural names on purpose -- see docstring.
CANNED = {
    "accelerates uniformly at 2.5": {
        "topic_hint": "Mechanics",
        "knowns": {
            "initial_velocity": {"value": 0, "source": "starts from rest"},
            "acceleration": {"value": 2.5, "source": "accelerates uniformly at 2.5 m/s^2"},
            "time": {"value": 12, "source": "for 12 s"},
        },
        "unknowns": ["final_velocity", "distance"],
        "notes": "",
    },
    "40 degrees above the horizontal": {
        "topic_hint": "Mechanics",
        "knowns": {
            "initial_speed": {"value": 25, "source": "launched at 25 m/s"},
            "angle": {"value": 40, "source": "40 degrees above the horizontal"},
        },
        "unknowns": ["time_of_flight", "max_height", "horizontal_range"],
        "notes": "g not stated; assumed standard gravity",
    },
    "frictionless pulley": {
        "topic_hint": "Mechanics",
        "knowns": {
            "mass_1": {"value": 4, "source": "4 kg"},
            "mass_2": {"value": 6, "source": "6 kg"},
        },
        "unknowns": ["acceleration", "tension"],
        "notes": "",
    },
    "100 microfarad capacitor": {
        "topic_hint": "E&M",
        "knowns": {
            "resistance": {"value": 2000, "source": "2 kOhm resistor"},
            "capacitance": {"value": 100e-6, "source": "100 microfarad capacitor"},
            "V_battery": {"value": 9, "source": "9 V battery"},
        },
        "unknowns": ["time_constant", "V_capacitor"],
        "notes": "",
    },
    "coefficient of kinetic friction": {
        "topic_hint": "Mechanics",
        "knowns": {
            "angle": {"value": 30, "source": "30 degree incline"},
            "mu_k": {"value": 0.2, "source": "coefficient of kinetic friction of 0.2"},
            "slide_distance": {"value": 4, "source": "sliding 4 m"},
        },
        "unknowns": ["acceleration", "final_speed"],
        "notes": "",
    },
    # --- deliberately outside the 16-card KB: a damped oscillator
    "damping constant": {
        "topic_hint": "Mechanics",
        "knowns": {
            "mass": {"value": 0.5, "source": "0.5 kg mass"},
            "spring_constant": {"value": 200, "source": "spring constant 200 N/m"},
            "damping_coefficient": {"value": 1.2, "source": "damping constant 1.2 kg/s"},
        },
        "unknowns": ["damped_frequency"],
        "notes": "damped SHM",
    },
}

PROBLEMS = [
    ("P1", "A car starts from rest and accelerates uniformly at 2.5 m/s^2 for 12 s. "
           "Find its final speed and the distance travelled."),
    ("P2", "A projectile is launched at 25 m/s at 40 degrees above the horizontal. "
           "Find the time of flight, maximum height, and horizontal range."),
    ("P3", "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. "
           "Find the acceleration and the tension."),
    ("P4", "A 2 kOhm resistor and a 100 microfarad capacitor are in series with a 9 V "
           "battery. Find the time constant and the capacitor voltage at t = tau."),
    ("P5", "A block slides down a 30 degree incline with a coefficient of kinetic "
           "friction of 0.2. Find its acceleration and speed after sliding 4 m."),
    ("P6", "A 0.5 kg mass on a spring of constant 200 N/m has a damping constant of "
           "1.2 kg/s. Find the damped oscillation frequency."),
]

EXPECTED = {
    "P1": {"v": 30.0, "s": 180.0},
    "P2": {"t_flight": 3.2795, "h_max": 13.1753, "range_": 62.8066},
    "P3": {"a": 1.96, "T": 47.04},
    "P4": {"tau": 0.2, "Vc": 5.6891},
    "P5": {"a": 3.2026, "v": 5.0617},
}

llm = StubLLM(CANNED)
log = EventLog()
mode = PhysicsEngineMode(llm, event_log=log)

print("=" * 78)
print("PHASE 1 -- raw problem text -> parsed -> routed -> rendered")
print("=" * 78)

passed = failed = 0
for pid, text in PROBLEMS:
    r = mode.solve(text, session_id="sess-demo", problem_id=pid)
    print(f"\n[{pid}] {text[:66]}...")
    print(f"   badge      : {r.badge}")
    if r.answer:
        print(f"   answer     : " + ", ".join(f"{k}={v:.4g}" for k, v in r.answer.items()))
        print(f"   formula    : {r.formula_used}")
    if r.candidates:
        for c in r.candidates:
            print(f"   candidate  : {c['principle']} -> {c['answer']}")
    if r.verification == Verification.UNVERIFIED:
        print(f"   -> handed back to Medhavy's model, labelled unverified")

    exp = EXPECTED.get(pid)
    if exp:
        bad = [k for k, v in exp.items()
               if r.answer is None or abs(r.answer.get(k, 1e9) - v) > max(1e-3, abs(v) * 1e-3)]
        if bad:
            failed += 1
            print(f"   MISMATCH   : {bad}")
        else:
            passed += 1
            print(f"   verified against golden set: OK")

print("\n" + "-" * 78)
print(f"{passed}/{len(EXPECTED)} problems parsed from raw text AND solved correctly "
      f"({failed} mismatched)")

# ---- normalization actually did work? -------------------------------------
print("\n=== Did normalization actually fire (or did the demo cheat)? ===")
r = mode.solve(PROBLEMS[0][1], session_id="sess-demo", problem_id="norm-check")
from parse import parse_problem
p = parse_problem(PROBLEMS[0][1], llm)
print(f"  LLM emitted   : initial_velocity, acceleration, time / final_velocity, distance")
print(f"  card received : {sorted(k for k in p['knowns'] if k not in p['injected'])} "
      f"/ {sorted(p['unknowns'])}")
print(f"  renamed       : {p['normalization']['renamed']}")
print(f"  auto-injected : {list(p['injected'])} (never stated in the problem)")

# ---- tutor rendering -------------------------------------------------------
print("\n=== Tutor render: same solution object, hints instead of the answer ===")
t = mode.solve(PROBLEMS[2][1], session_id="sess-demo", render="tutor", problem_id="tutor-1")
for i, h in enumerate(t.hints, 1):
    print(f"  hint {i}: {h}")
print(f"  answer field withheld: {t.answer is None}")

# ---- event log -------------------------------------------------------------
print("\n=== Event log (the Phase 1 addition the roadmap loops read from) ===")
print(f"  events emitted : {len(log.events)}")
print(f"  route split    : {log.route_split()}")
lat = log.latency_summary()
print(f"  latency        : median {lat['median_ms']:.2f} ms, max {lat['max_ms']:.2f} ms "
      f"over {lat['n']} queries")
print(f"  coverage gaps  : {len(log.coverage_gaps())} -> curate loop")
for g in log.coverage_gaps():
    print(f"      unmatched unknowns {g['unknowns']} (topic {g['topic_hint']})")

print("\n=== Identity scoping is enforced, not just documented ===")
try:
    log.emit("curate.no_card_match", student_id="student-123", unknowns=["v"])
    print("  FAILED: scope violation was allowed through")
except ScopeViolation as e:
    print(f"  correctly refused: {str(e)[:88]}...")

print("\n=== Symbol-collision audit (derived from cards, run this in CI) ===")
a = audit_symbol_collisions(ALL_CARDS)
print(f"  undocumented card variables : {a['undocumented'] or '(none)'}")
print(f"  output collisions           : {len(a['output_collisions'])} "
      f"-> {list(a['output_collisions'])}")
print("  these are exactly what the ambiguity route arbitrates; when this list grows")
print("  past what arbitration can resolve, that is the signal to namespace symbols.")
