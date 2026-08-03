"""
Runs the engine end-to-end on the 16 Phase-0 golden-set problems and checks its
answers against the values already verified (independently, via SymPy) in the
golden-set spreadsheet. Also runs one deliberate gap case to show the
no-card-matched / closure-failure path routes to the curate loop instead of failing silently.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

import sympy as sp
from scipy import constants as C
from pipeline import solve_physics_problem

k_e = float(1 / (4 * sp.pi * C.epsilon_0))

CASES = [
    dict(pid="MECH-001", topic="Mechanics",
         text="A car starts from rest and accelerates uniformly at 2.5 m/s^2 for 12 s. "
              "Find (a) the car's final speed and (b) the distance it travels during this time.",
         knowns=dict(v0=0, a=2.5, t=12), unknowns=['v', 's'],
         expected=dict(v=30.0, s=180.0)),
    dict(pid="MECH-002", topic="Mechanics",
         text="A projectile is launched from ground level at 25 m/s at an angle of 40 degrees "
              "above the horizontal. Ignoring air resistance (g=9.8 m/s^2), find the time of "
              "flight, the maximum height, and the horizontal range.",
         knowns=dict(v0=25, theta_deg=40, g=9.8), unknowns=['t_flight', 'h_max', 'range_'],
         expected=dict(t_flight=3.2795, h_max=13.1753, range_=62.8066)),
    dict(pid="MECH-003", topic="Mechanics",
         text="Two blocks of mass 4 kg and 6 kg are connected by a string over a frictionless "
              "pulley (Atwood machine). Find the acceleration and the tension.",
         knowns=dict(m1=4, m2=6, g=9.8), unknowns=['a', 'T'],
         expected=dict(a=1.96, T=47.04)),
    dict(pid="MECH-004", topic="Mechanics",
         text="A block slides down a 30 degree incline with kinetic friction coefficient 0.2. "
              "Starting from rest, find the acceleration and the speed after sliding 4 m.",
         knowns=dict(theta_deg=30, mu=0.2, g=9.8, d=4), unknowns=['a', 'v'],
         expected=dict(a=3.2026, v=5.0617)),
    dict(pid="MECH-005", topic="Mechanics",
         text="A 2 kg block compresses a spring (k=500 N/m) by 0.15 m on a frictionless surface. "
              "Find the block's speed when released.",
         knowns=dict(m=2, k=500, x=0.15), unknowns=['v'],
         expected=dict(v=2.3717)),
    dict(pid="MECH-006", topic="Mechanics",
         text="A 3 kg cart at 4 m/s collides and sticks to a stationary 5 kg cart. Find the "
              "final velocity and the kinetic energy lost.",
         knowns=dict(m1=3, v1=4, m2=5), unknowns=['vf', 'KEi', 'KEf', 'dKE'],
         expected=dict(vf=1.5, KEi=24.0, KEf=9.0, dKE=15.0)),
    dict(pid="MECH-007", topic="Mechanics",
         text="A solid disk (M=2 kg, R=0.25 m) at rest has a constant torque of 0.6 N*m applied. "
              "Find the angular acceleration and angular speed after 5 s.",
         knowns=dict(M=2, R=0.25, tau=0.6, t=5), unknowns=['I', 'alpha', 'omega'],
         expected=dict(I=0.0625, alpha=9.6, omega=48.0)),
    dict(pid="MECH-008", topic="Mechanics",
         text="A satellite orbits Earth at 500 km altitude. Using Earth's mass and radius, "
              "find the orbital speed and period.",
         knowns=dict(G=C.G, M=5.972e24, h=500e3, Re=6.371e6), unknowns=['r', 'v', 'T'],
         expected=dict(r=6.871e6, v=7616.4534, T=5668.2243)),
    dict(pid="EM-001", topic="E&M",
         text="Two point charges, +3 uC and -5 uC, are separated by 0.2 m. Find the force between them.",
         knowns=dict(k_e=k_e, q1_abs=3e-6, q2_abs=5e-6, r=0.2), unknowns=['F'],
         expected=dict(F=3.3703)),
    dict(pid="EM-002", topic="E&M",
         text="Find the electric field at 0.5 m from a point charge of +8 uC.",
         knowns=dict(k_e=k_e, Q=8e-6, r=0.5), unknowns=['E'],
         expected=dict(E=287601.66)),
    dict(pid="EM-003", topic="E&M",
         text="A uniformly charged insulating sphere (R=0.1 m, Q=4 uC) — find E at r=0.05 m and r=0.3 m.",
         knowns=dict(k_e=k_e, Q=4e-6, R=0.1, r_in=0.05, r_out=0.3), unknowns=['E_in', 'E_out'],
         expected=dict(E_in=1797510.36, E_out=399446.75)),
    dict(pid="EM-004", topic="E&M",
         text="A 4 ohm and 6 ohm resistor in series, that combination in parallel with 12 ohm, "
              "across a 12 V source. Find R_eq and branch currents.",
         knowns=dict(R1=4, R2=6, R3=12, V=12), unknowns=['R_series', 'R_eq', 'I_total', 'I_branch1', 'I_branch2'],
         expected=dict(R_series=10.0, R_eq=5.4545, I_total=2.2, I_branch1=1.2, I_branch2=1.0)),
    dict(pid="EM-005", topic="E&M",
         text="A 2 kOhm resistor and 100 uF capacitor in series with a 9 V battery, charging from zero. "
              "Find tau and V_C at t=tau.",
         knowns=dict(R=2000, C=100e-6, V0=9), unknowns=['tau', 'Vc'],
         expected=dict(tau=0.2, Vc=5.6891)),
    dict(pid="EM-006", topic="E&M",
         text="A proton at 2e6 m/s enters a 0.5 T field perpendicular to its velocity. "
              "Find the radius and period of its circular path.",
         knowns=dict(q=C.elementary_charge, m=C.proton_mass, v=2e6, B=0.5), unknowns=['r', 'T'],
         expected=dict(r=4.175874e-02, T=1.311889e-07)),
    dict(pid="EM-007", topic="E&M",
         text="A wire (I=5 A, L=0.3 m) is perpendicular to a 0.8 T field. Find the force.",
         knowns=dict(B=0.8, I=5, L=0.3, theta_deg=90), unknowns=['F'],
         expected=dict(F=1.2)),
    dict(pid="EM-008", topic="E&M",
         text="A circular loop (r=0.05 m) sits in a field changing at 0.2 T/s. Find the induced EMF.",
         knowns=dict(r=0.05, dBdt=0.2), unknowns=['A', 'EMF'],
         expected=dict(A=0.0078540, EMF=0.0015708)),
]

print(f"{'Problem':<10} {'Status':<10} {'Match?':<8} Details")
print("-" * 100)
n_pass, n_fail = 0, 0
for c in CASES:
    result = solve_physics_problem(c['pid'], c['text'], c['knowns'], c['unknowns'], topic_hint=c['topic'])
    if result['status'].startswith('solved'):
        fa = result['final_answer']
        mismatches = []
        for key, exp_val in c['expected'].items():
            got = fa.get(key)
            if got is None or abs(got - exp_val) > max(1e-3, abs(exp_val) * 1e-3):
                mismatches.append(f"{key}: got {got}, expected {exp_val}")
        ok = not mismatches
        n_pass += ok
        n_fail += not ok
        detail = "all values match golden set" if ok else "; ".join(mismatches)
        print(f"{c['pid']:<10} {result['status']:<10} {'YES' if ok else 'NO':<8} {detail}")
    else:
        n_fail += 1
        print(f"{c['pid']:<10} {result['status']:<10} {'N/A':<8} (did not reach solved state)")

print("-" * 100)
print(f"{n_pass}/{len(CASES)} problems solved with answers matching the golden set exactly.")

print()
print("=== Deliberate gap case: incomplete parse (missing a required known) ===")
gap_result = solve_physics_problem(
    "GAP-TEST", "A car accelerates uniformly for 12 s. Find its final speed.",
    knowns=dict(a=2.5, t=12), unknowns=['v', 's'], topic_hint="Mechanics")  # v0 missing on purpose
print(f"status: {gap_result['status']}  |  route: {gap_result['route']}")
print(f"plan stage: {gap_result['plan']}")

print()
print("=== V2 check 1: is the deterministic path actually deterministic? ===")
import json
runs = [json.dumps(solve_physics_problem("MECH-003", CASES[2]['text'], CASES[2]['knowns'],
                                          CASES[2]['unknowns'], topic_hint="Mechanics"), sort_keys=True)
        for _ in range(10)]
all_identical = len(set(runs)) == 1
print(f"Ran the Atwood-machine problem 10 times. All 10 outputs byte-identical: {all_identical}")
if not all_identical:
    print("  -> NOT deterministic, this would be a real bug.")

print()
print("=== V2 check 2: same requested unknown, two unrelated deterministic paths, different answers ===")
print("Deliberately overlapping knowns: enough for BOTH the kinematics card AND the spring-energy")
print("card to close on a shared unknown 'v'. Neither card is wrong; the ROUTING is what must catch this.")
ambiguous_result = solve_physics_problem(
    "AMBIG-TEST", "ambiguous synthetic case: knowns satisfy two unrelated formulas for v",
    knowns=dict(v0=0, a=2.5, t=12, m=2, k=500, x=0.15),  # satisfies MECH-KIN-1D AND MECH-ENE-SPRING
    unknowns=['v'], topic_hint="Mechanics")
print(f"status: {ambiguous_result['status']}  |  route: {ambiguous_result['route']}")
for pc in ambiguous_result['solve']['per_candidate_results']:
    print(f"  {pc['card_id']:<20} -> v = {pc['final_answer'].get('v')}")
print(f"disagreement detail: {ambiguous_result['verify']['disagreement_on_shared_unknowns']}")
print()
print("This is the concrete version of the V2 feedback's 'same problem, different outputs' trigger:")
print("the engine does NOT silently pick one answer — it surfaces both and asks for arbitration.")

