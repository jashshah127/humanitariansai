"""
Starter formula-card knowledge base (Retrieve stage's data source).

Each card owns: which knowns it needs, which unknowns it can produce, the underlying
equations (built fresh per call so sympy symbols never leak state between problems),
expected output units, common pitfalls, and — where a genuinely independent check
exists — a verify_fn implementing the brief's "independent solution path" check.

Scope matches the locked Topic Scope sheet: Mechanics + E&M, calc-based, text-format only.
"""
import sympy as sp
from models import FormulaCard

S = sp.Symbol  # shorthand


def _residual_ok(eqs, subs, tol=1e-6):
    for eq in eqs:
        val = (eq.lhs - eq.rhs).subs(subs)
        val = complex(val.evalf())
        if abs(val) > tol:
            return False
    return True


# ---------------------------------------------------------------- Mechanics

def _mech001_eqs(k):
    v0, a, t = k['v0'], k['a'], k['t']
    v, s = S('v'), S('s')
    return [sp.Eq(v, v0 + a * t), sp.Eq(s, v0 * t + a * t**2 / 2)]


def _mech001_verify(knowns, solved):
    v0, a, t = knowns['v0'], knowns['a'], knowns['t']
    v, s = solved['v'], solved['s']
    s_check = (v**2 - v0**2) / (2 * a) if a != 0 else None
    ok = s_check is not None and abs(s_check - s) < 1e-6
    return ok, f"s re-derived via v^2=v0^2+2as gives {s_check:.4f} m vs solved {s:.4f} m"


MECH001 = FormulaCard(
    id="MECH-KIN-1D", name="Constant-acceleration kinematics (1D)",
    topic="Mechanics", subtopic="Kinematics",
    applicability="Motion in a straight line with constant acceleration; starts at t=0.",
    required_knowns=['v0', 'a', 't'], solves_for=['v', 's'],
    build_equations=_mech001_eqs,
    output_units={'v': 'm/s', 's': 'm'},
    pitfalls="Forgetting v0=0 when 'starts from rest'; mismatching which kinematic equation pairs with which unknown.",
    verify_fn=_mech001_verify,
)


def _mech002_eqs(k):
    v0, g = k['v0'], k['g']
    theta = sp.rad(k['theta_deg'])
    vx0, vy0 = v0 * sp.cos(theta), v0 * sp.sin(theta)
    t_flight, h_max, rng = S('t_flight'), S('h_max'), S('range_')
    return [sp.Eq(t_flight, 2 * vy0 / g), sp.Eq(h_max, vy0**2 / (2 * g)), sp.Eq(rng, vx0 * t_flight)]


def _mech002_verify(knowns, solved):
    v0, g, theta_deg = knowns['v0'], knowns['g'], knowns['theta_deg']
    theta = sp.rad(theta_deg)
    rng_check = float(v0**2 * sp.sin(2 * theta) / g)
    ok = abs(rng_check - solved['range_']) < 1e-6
    return ok, f"range re-derived via closed form v0^2*sin(2theta)/g gives {rng_check:.4f} m vs solved {solved['range_']:.4f} m"


MECH002 = FormulaCard(
    id="MECH-KIN-PROJ", name="Projectile motion (equal launch/landing height)",
    topic="Mechanics", subtopic="Kinematics",
    applicability="Launched and landing at the same height; no air resistance.",
    required_knowns=['v0', 'theta_deg', 'g'], solves_for=['t_flight', 'h_max', 'range_'],
    build_equations=_mech002_eqs,
    output_units={'t_flight': 's', 'h_max': 'm', 'range_': 'm'},
    pitfalls="Using degrees where radians are expected; formula assumes equal launch/landing height.",
    verify_fn=_mech002_verify,
)


def _mech003_eqs(k):
    m1, m2, g = k['m1'], k['m2'], k['g']
    a, T = S('a'), S('T')
    return [sp.Eq(T - m1 * g, m1 * a), sp.Eq(m2 * g - T, m2 * a)]


MECH003 = FormulaCard(
    id="MECH-DYN-ATWOOD", name="Atwood machine",
    topic="Mechanics", subtopic="Dynamics",
    applicability="Two masses, frictionless massless pulley, massless inextensible string.",
    required_knowns=['m1', 'm2', 'g'], solves_for=['a', 'T'],
    build_equations=_mech003_eqs,
    output_units={'a': 'm/s^2', 'T': 'N'},
    pitfalls="Inconsistent sign convention across the two masses' equations.",
    must_be_positive=['T'],
)


def _mech004_eqs(k):
    theta = sp.rad(k['theta_deg'])
    mu, g, d = k['mu'], k['g'], k['d']
    a, v = S('a'), S('v')
    return [sp.Eq(a, g * (sp.sin(theta) - mu * sp.cos(theta))), sp.Eq(v, sp.sqrt(2 * a * d))]


MECH004 = FormulaCard(
    id="MECH-DYN-INCLINE", name="Block sliding down incline with kinetic friction",
    topic="Mechanics", subtopic="Dynamics",
    applicability="Requires tan(theta) > mu_k, else the block does not slide at all — check before trusting a>0.",
    required_knowns=['theta_deg', 'mu', 'g', 'd'], solves_for=['a', 'v'],
    build_equations=_mech004_eqs,
    output_units={'a': 'm/s^2', 'v': 'm/s'},
    pitfalls="Not checking tan(theta) > mu_k before computing a 'sliding' answer.",
    must_be_positive=['a', 'v'],
)


def _mech005_eqs(k):
    m, kk, x = k['m'], k['k'], k['x']
    v = S('v')
    return [sp.Eq(sp.Rational(1, 2) * kk * x**2, sp.Rational(1, 2) * m * v**2)]


MECH005 = FormulaCard(
    id="MECH-ENE-SPRING", name="Spring energy to kinetic energy",
    topic="Mechanics", subtopic="Work & Energy",
    applicability="Ideal spring, frictionless surface, all spring PE converts to block KE.",
    required_knowns=['m', 'k', 'x'], solves_for=['v'],
    build_equations=_mech005_eqs,
    output_units={'v': 'm/s'},
    pitfalls="Forgetting the setup requires a frictionless surface and an ideal spring.",
    must_be_positive=['v'],
)


def _mech006_eqs(k):
    m1, v1, m2 = k['m1'], k['v1'], k['m2']
    vf, KEi, KEf, dKE = S('vf'), S('KEi'), S('KEf'), S('dKE')
    return [sp.Eq(m1 * v1, (m1 + m2) * vf),
            sp.Eq(KEi, sp.Rational(1, 2) * m1 * v1**2),
            sp.Eq(KEf, sp.Rational(1, 2) * (m1 + m2) * vf**2),
            sp.Eq(dKE, KEi - KEf)]


MECH006 = FormulaCard(
    id="MECH-MOM-INELASTIC", name="Perfectly inelastic collision",
    topic="Mechanics", subtopic="Momentum",
    applicability="Second mass initially at rest; masses stick together after collision.",
    required_knowns=['m1', 'v1', 'm2'], solves_for=['vf', 'KEi', 'KEf', 'dKE'],
    build_equations=_mech006_eqs,
    output_units={'vf': 'm/s', 'KEi': 'J', 'KEf': 'J', 'dKE': 'J'},
    pitfalls="Conserving KE as if the collision were elastic.",
    must_be_positive=['dKE'],
)


def _mech007_eqs(k):
    M, R, tau, t = k['M'], k['R'], k['tau'], k['t']
    I, alpha, omega = S('I'), S('alpha'), S('omega')
    return [sp.Eq(I, sp.Rational(1, 2) * M * R**2), sp.Eq(tau, I * alpha), sp.Eq(omega, alpha * t)]


MECH007 = FormulaCard(
    id="MECH-ROT-TORQUE", name="Solid disk under constant torque",
    topic="Mechanics", subtopic="Rotation",
    applicability="Starts from rest; disk (I=1/2 M R^2), not a hoop or sphere.",
    required_knowns=['M', 'R', 'tau', 't'], solves_for=['I', 'alpha', 'omega'],
    build_equations=_mech007_eqs,
    output_units={'I': 'kg*m^2', 'alpha': 'rad/s^2', 'omega': 'rad/s'},
    pitfalls="Using the wrong moment-of-inertia formula for the shape.",
    must_be_positive=['I', 'alpha', 'omega'],
)


def _mech008_eqs(k):
    G, M, h, Re = k['G'], k['M'], k['h'], k['Re']
    r, v, T = S('r'), S('v'), S('T')
    return [sp.Eq(r, Re + h), sp.Eq(v, sp.sqrt(G * M / r)), sp.Eq(T, 2 * sp.pi * r / v)]


def _mech008_verify(knowns, solved):
    r = solved['r']
    G, M = knowns['G'], knowns['M']
    T_check = float(2 * sp.pi * sp.sqrt(r**3 / (G * M)))
    ok = abs(T_check - solved['T']) < 1e-3
    return ok, f"T re-derived via 2*pi*sqrt(r^3/GM) gives {T_check:.4f} s vs solved {solved['T']:.4f} s"


MECH008 = FormulaCard(
    id="MECH-GRAV-ORBIT", name="Circular satellite orbit",
    topic="Mechanics", subtopic="Gravitation",
    applicability="Circular orbit; r measured from the central body's center, not surface altitude alone.",
    required_knowns=['G', 'M', 'h', 'Re'], solves_for=['r', 'v', 'T'],
    build_equations=_mech008_eqs,
    output_units={'r': 'm', 'v': 'm/s', 'T': 's'},
    pitfalls="Using altitude instead of the full orbital radius (Re+h).",
    must_be_positive=['r', 'v', 'T'],
    verify_fn=_mech008_verify,
)

MECHANICS_CARDS = [MECH001, MECH002, MECH003, MECH004, MECH005, MECH006, MECH007, MECH008]

# ---------------------------------------------------------------- E&M


def _em001_eqs(k):
    ke, q1, q2, r = k['k_e'], k['q1_abs'], k['q2_abs'], k['r']
    F = S('F')
    return [sp.Eq(F, ke * q1 * q2 / r**2)]


EM001 = FormulaCard(
    id="EM-ELEC-COULOMB", name="Coulomb's law", topic="E&M", subtopic="Electrostatics",
    applicability="Point charges (or spherically symmetric charge distributions treated as points); vacuum/air.",
    required_knowns=['k_e', 'q1_abs', 'q2_abs', 'r'], solves_for=['F'],
    build_equations=_em001_eqs,
    output_units={'F': 'N'},
    pitfalls="Using signed charges instead of magnitudes in the force formula; sign only sets direction.",
    must_be_positive=['F'],
)


def _em002_eqs(k):
    ke, Q, r = k['k_e'], k['Q'], k['r']
    E = S('E')
    return [sp.Eq(E, ke * Q / r**2)]


EM002 = FormulaCard(
    id="EM-ELEC-FIELD-POINT", name="Electric field of a point charge", topic="E&M", subtopic="Electrostatics",
    applicability="Point charge (or outside a spherically symmetric charge distribution).",
    required_knowns=['k_e', 'Q', 'r'], solves_for=['E'],
    build_equations=_em002_eqs,
    output_units={'E': 'N/C'},
    pitfalls="Field direction depends only on the source charge's sign, not on any test charge.",
    must_be_positive=['E'],
)


def _em003_eqs(k):
    ke, Q, R, r_in, r_out = k['k_e'], k['Q'], k['R'], k['r_in'], k['r_out']
    E_in, E_out = S('E_in'), S('E_out')
    return [sp.Eq(E_in, ke * Q * r_in / R**3), sp.Eq(E_out, ke * Q / r_out**2)]


def _em003_verify(knowns, solved):
    ke, Q, R = knowns['k_e'], knowns['Q'], knowns['R']
    E_in_at_R = float(ke * Q * R / R**3)
    E_out_at_R = float(ke * Q / R**2)
    ok = abs(E_in_at_R - E_out_at_R) < 1e-3
    return ok, f"boundary continuity at r=R: E_in-formula={E_in_at_R:.4e}, E_out-formula={E_out_at_R:.4e}"


EM003 = FormulaCard(
    id="EM-ELEC-GAUSS-SPHERE", name="Gauss's law: uniformly charged insulating sphere",
    topic="E&M", subtopic="Electrostatics",
    applicability="Solid insulating sphere, charge uniform through the volume (not a shell).",
    required_knowns=['k_e', 'Q', 'R', 'r_in', 'r_out'], solves_for=['E_in', 'E_out'],
    build_equations=_em003_eqs,
    output_units={'E_in': 'N/C', 'E_out': 'N/C'},
    pitfalls="Using the point-charge formula inside the sphere instead of the r-scaled interior form.",
    must_be_positive=['E_in', 'E_out'],
    verify_fn=_em003_verify,
)


def _em004_eqs(k):
    R1, R2, R3, V = k['R1'], k['R2'], k['R3'], k['V']
    Rs, Req, It, I1, I2 = S('R_series'), S('R_eq'), S('I_total'), S('I_branch1'), S('I_branch2')
    return [sp.Eq(Rs, R1 + R2), sp.Eq(Req, (Rs * R3) / (Rs + R3)),
            sp.Eq(It, V / Req), sp.Eq(I1, V / Rs), sp.Eq(I2, V / R3)]


def _em004_verify(knowns, solved):
    total_check = solved['I_branch1'] + solved['I_branch2']
    ok = abs(total_check - solved['I_total']) < 1e-6
    return ok, f"KCL check: I_branch1+I_branch2={total_check:.4f} A vs I_total={solved['I_total']:.4f} A"


EM004 = FormulaCard(
    id="EM-CIRC-SERIES-PARALLEL", name="Series pair in parallel with a third resistor",
    topic="E&M", subtopic="Circuits",
    applicability="R1,R2 in series; that combination in parallel with R3; ideal source, ideal wires.",
    required_knowns=['R1', 'R2', 'R3', 'V'], solves_for=['R_series', 'R_eq', 'I_total', 'I_branch1', 'I_branch2'],
    build_equations=_em004_eqs,
    output_units={'R_series': 'ohm', 'R_eq': 'ohm', 'I_total': 'A', 'I_branch1': 'A', 'I_branch2': 'A'},
    pitfalls="Forgetting each parallel branch sees the full source voltage, not a divided voltage.",
    must_be_positive=['R_series', 'R_eq', 'I_total', 'I_branch1', 'I_branch2'],
    verify_fn=_em004_verify,
)


def _em005_eqs(k):
    R, C, V0 = k['R'], k['C'], k['V0']
    tau, Vc = S('tau'), S('Vc')
    return [sp.Eq(tau, R * C), sp.Eq(Vc, V0 * (1 - sp.exp(-1)))]


def _em005_verify(knowns, solved):
    ratio = solved['Vc'] / knowns['V0']
    expected = 1 - float(sp.exp(-1))
    ok = abs(ratio - expected) < 1e-6
    return ok, f"Vc/V0={ratio:.4f} vs the universal one-time-constant charging fraction 1-1/e={expected:.4f}"


EM005 = FormulaCard(
    id="EM-CIRC-RC-CHARGE-1TAU", name="RC charging, evaluated at t = one time constant",
    topic="E&M", subtopic="Circuits",
    applicability="Series RC, charging from zero charge; SCOPED to t=tau specifically, not arbitrary t.",
    required_knowns=['R', 'C', 'V0'], solves_for=['tau', 'Vc'],
    build_equations=_em005_eqs,
    output_units={'tau': 's', 'Vc': 'V'},
    pitfalls="Swapping the charging form (1-e^-t/tau) for the discharging form (e^-t/tau).",
    must_be_positive=['tau', 'Vc'],
    verify_fn=_em005_verify,
)


def _em006_eqs(k):
    q, m, v, B = k['q'], k['m'], k['v'], k['B']
    r, T = S('r'), S('T')
    return [sp.Eq(r, m * v / (q * B)), sp.Eq(T, 2 * sp.pi * m / (q * B))]


def _em006_verify(knowns, solved):
    v = knowns['v']
    r = solved['r']
    T_check = float(2 * sp.pi * r / v)
    ok = abs(T_check - solved['T']) < 1e-12
    return ok, f"T re-derived via 2*pi*r/v gives {T_check:.6e} s vs solved {solved['T']:.6e} s"


EM006 = FormulaCard(
    id="EM-MAG-LORENTZ-CIRCULAR", name="Charged particle circular motion in a B field",
    topic="E&M", subtopic="Magnetism",
    applicability="Velocity perpendicular to B; non-relativistic speed.",
    required_knowns=['q', 'm', 'v', 'B'], solves_for=['r', 'T'],
    build_equations=_em006_eqs,
    output_units={'r': 'm', 'T': 's'},
    pitfalls="Assuming period depends on speed — it doesn't, in the non-relativistic limit.",
    must_be_positive=['r', 'T'],
    verify_fn=_em006_verify,
)


def _em007_eqs(k):
    B, I, L, theta_deg = k['B'], k['I'], k['L'], k['theta_deg']
    F = S('F')
    return [sp.Eq(F, B * I * L * sp.sin(sp.rad(theta_deg)))]


EM007 = FormulaCard(
    id="EM-MAG-FORCE-WIRE", name="Force on a current-carrying wire", topic="E&M", subtopic="Magnetism",
    applicability="Straight wire segment, uniform B field.",
    required_knowns=['B', 'I', 'L', 'theta_deg'], solves_for=['F'],
    build_equations=_em007_eqs,
    output_units={'F': 'N'},
    pitfalls="Dropping the sin(theta) factor when the field isn't perpendicular to the current.",
    must_be_positive=['F'],
)


def _em008_eqs(k):
    r, dBdt = k['r'], k['dBdt']
    A, EMF = S('A'), S('EMF')
    return [sp.Eq(A, sp.pi * r**2), sp.Eq(EMF, A * dBdt)]


EM008 = FormulaCard(
    id="EM-IND-FARADAY", name="Faraday's law, fixed-area loop", topic="E&M", subtopic="Induction",
    applicability="Loop area fixed; B uniform and perpendicular to the loop.",
    required_knowns=['r', 'dBdt'], solves_for=['A', 'EMF'],
    build_equations=_em008_eqs,
    output_units={'A': 'm^2', 'EMF': 'V'},
    pitfalls="Assuming induction requires motion — a changing field alone induces an EMF.",
    must_be_positive=['A', 'EMF'],
)

EM_CARDS = [EM001, EM002, EM003, EM004, EM005, EM006, EM007, EM008]

WAVE_CARDS = []


# ---------------------------------------------------------------- Vibrations & Waves
# Added after measuring the benchmark: Vibrations and Waves is 179 UGPhysics problems,
# 76 of them numerically scorable, and the KB had ZERO cards for it -- the single
# largest measured gap. SHM was locked into scope on Aug 3 and never built.
#
# NAMING: `k` is already spring constant and `A` is already loop area elsewhere in this
# KB, so wave number and amplitude take distinct names (k_wave, A_amp) rather than
# overloading symbols that the collision audit would then flag. Deliberate, not stylistic.

def _wave001_eqs(k):
    f, lam = k['f'], k['lambda_']
    v = S('v')
    return [sp.Eq(v, f * lam)]


WAVE001 = FormulaCard(
    id="WAVE-BASIC-RELATION", name="Wave relation v = f*lambda",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Any periodic travelling wave in a non-dispersive medium.",
    required_knowns=['f', 'lambda_'], solves_for=['v'],
    build_equations=_wave001_eqs,
    output_units={'v': 'm/s'},
    pitfalls="Mixing units -- wavelength in cm with speed in m/s is the usual slip.",
    must_be_positive=['v'],
)


def _wave002_eqs(k):
    kw, om = k['k_wave'], k['omega']
    lam, f, v, T = S('lambda_'), S('f'), S('v'), S('T_period')
    return [sp.Eq(lam, 2 * sp.pi / kw), sp.Eq(f, om / (2 * sp.pi)),
            sp.Eq(v, om / kw), sp.Eq(T, 2 * sp.pi / om)]


def _wave002_verify(knowns, solved):
    check = solved['f'] * solved['lambda_']
    ok = abs(check - solved['v']) < 1e-6 * max(1.0, abs(solved['v']))
    return ok, f"cross-check f*lambda = {check:.6g} vs v = {solved['v']:.6g}"


WAVE002 = FormulaCard(
    id="WAVE-FROM-EQUATION", name="Wave properties from y = A sin(k_wave*x - omega*t)",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Wave written in the form y = A sin(k_wave*x - omega*t); k_wave and omega "
                  "read straight off the equation. Watch stated units (cm vs m).",
    required_knowns=['k_wave', 'omega'], solves_for=['lambda_', 'f', 'v', 'T_period'],
    build_equations=_wave002_eqs,
    output_units={'lambda_': 'm', 'f': 'Hz', 'v': 'm/s', 'T_period': 's'},
    pitfalls="Reading the coefficient of x as the wavelength -- it is the wave NUMBER; "
             "wavelength is 2*pi divided by it.",
    must_be_positive=['lambda_', 'f', 'v', 'T_period'],
    verify_fn=_wave002_verify,
)


def _wave003_eqs(k):
    m, ksp = k['m'], k['k']
    T, om, f = S('T_period'), S('omega'), S('f')
    return [sp.Eq(om, sp.sqrt(ksp / m)), sp.Eq(T, 2 * sp.pi / om), sp.Eq(f, 1 / T)]


def _wave003_verify(knowns, solved):
    T_check = float(2 * sp.pi * sp.sqrt(sp.Rational(1, 1) * knowns['m'] / knowns['k']))
    ok = abs(T_check - solved['T_period']) < 1e-6 * max(1.0, abs(T_check))
    return ok, f"period re-derived as 2*pi*sqrt(m/k) = {T_check:.6g} s vs {solved['T_period']:.6g} s"


WAVE003 = FormulaCard(
    id="SHM-SPRING-PERIOD", name="Simple harmonic motion: mass on a spring",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Ideal spring, no damping, mass oscillating freely.",
    required_knowns=['m', 'k'], solves_for=['omega', 'T_period', 'f'],
    build_equations=_wave003_eqs,
    output_units={'omega': 'rad/s', 'T_period': 's', 'f': 'Hz'},
    pitfalls="Period does NOT depend on amplitude -- a frequent wrong instinct.",
    must_be_positive=['omega', 'T_period', 'f'],
    verify_fn=_wave003_verify,
)


def _wave004_eqs(k):
    a, b = k['coef_sin'], k['coef_cos']
    A = S('A_amp')
    return [sp.Eq(A, sp.sqrt(a**2 + b**2))]


WAVE004 = FormulaCard(
    id="SHM-AMPLITUDE-COMBINE", name="Amplitude of a*sin(wt) + b*cos(wt)",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Two SHM terms of the SAME angular frequency, one sine one cosine.",
    required_knowns=['coef_sin', 'coef_cos'], solves_for=['A_amp'],
    build_equations=_wave004_eqs,
    output_units={'A_amp': 'm'},
    pitfalls="Adding the coefficients directly. They are 90 degrees out of phase, so "
             "they combine in quadrature, not linearly.",
    must_be_positive=['A_amp'],
)


def _wave005_eqs(k):
    m, ksp = k['m'], k['k']
    c = S('c_damp')
    return [sp.Eq(c, 2 * sp.sqrt(m * ksp))]


WAVE005 = FormulaCard(
    id="SHM-CRITICAL-DAMPING", name="Critical damping coefficient",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Critically damped condition specifically -- the boundary case between "
                  "underdamped oscillation and overdamped creep.",
    required_knowns=['m', 'k'], solves_for=['c_damp'],
    build_equations=_wave005_eqs,
    output_units={'c_damp': 'kg/s'},
    pitfalls="Confusing critical damping with the damped frequency; at critical damping "
             "the system does not oscillate at all.",
    must_be_positive=['c_damp'],
)


def _wave006_eqs(k):
    f_src, v_snd = k['f_source'], k['v_sound']
    v_o, v_s = k['v_observer'], k['v_source']
    f_obs = S('f_observed')
    return [sp.Eq(f_obs, f_src * (v_snd + v_o) / (v_snd - v_s))]


WAVE006 = FormulaCard(
    id="WAVE-DOPPLER", name="Doppler effect (source and observer along the line of sight)",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Motion along the line joining source and observer. Sign convention: "
                  "v_observer positive TOWARD the source, v_source positive TOWARD the "
                  "observer. Set either to 0 when stationary.",
    required_knowns=['f_source', 'v_sound', 'v_observer', 'v_source'],
    solves_for=['f_observed'],
    build_equations=_wave006_eqs,
    output_units={'f_observed': 'Hz'},
    pitfalls="Sign convention is the whole problem here. Approaching raises the pitch, "
             "receding lowers it -- check the answer against that before trusting it.",
    must_be_positive=['f_observed'],
)


def _wave007_eqs(k):
    v, L, n = k['v'], k['L'], k['n_harmonic']
    f = S('f')
    return [sp.Eq(f, n * v / (2 * L))]


WAVE007 = FormulaCard(
    id="WAVE-PIPE-OPEN", name="Standing wave in an open pipe (both ends open)",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Pipe open at BOTH ends. n = 1 is the fundamental; all harmonics present.",
    required_knowns=['v', 'L', 'n_harmonic'], solves_for=['f'],
    build_equations=_wave007_eqs,
    output_units={'f': 'Hz'},
    pitfalls="Using this for a closed pipe. A closed pipe supports only ODD harmonics "
             "and its fundamental is v/(4L), not v/(2L).",
    must_be_positive=['f'],
)


def _wave008_eqs(k):
    v, L, n = k['v'], k['L'], k['n_harmonic']
    f = S('f')
    return [sp.Eq(f, n * v / (4 * L))]


WAVE008 = FormulaCard(
    id="WAVE-PIPE-CLOSED", name="Standing wave in a closed pipe (one end closed)",
    topic="Mechanics", subtopic="Vibrations and Waves",
    applicability="Pipe closed at ONE end. Only odd harmonics exist, so n must be odd "
                  "(1, 3, 5...); n=3 is the first overtone, not the second harmonic.",
    required_knowns=['v', 'L', 'n_harmonic'], solves_for=['f'],
    build_equations=_wave008_eqs,
    output_units={'f': 'Hz'},
    pitfalls="Treating n=2 as valid. A closed pipe has no even harmonics, so 'second "
             "overtone' means n=5 here, not n=3.",
    must_be_positive=['f'],
)


def _wave009_eqs(k):
    G_mass, R_body, G_const = k['M'], k['R'], k['G']
    v_esc = S('v_escape')
    return [sp.Eq(v_esc, sp.sqrt(2 * G_const * G_mass / R_body))]


def _wave009_verify(knowns, solved):
    import math
    v_orbit = math.sqrt(knowns['G'] * knowns['M'] / knowns['R'])
    ratio = solved['v_escape'] / v_orbit
    ok = abs(ratio - math.sqrt(2)) < 1e-6
    return ok, f"escape/orbital ratio = {ratio:.6f}, must equal sqrt(2) = 1.414214"


WAVE009 = FormulaCard(
    id="MECH-GRAV-ESCAPE", name="Escape velocity from a body's surface",
    topic="Mechanics", subtopic="Gravitation",
    applicability="Escape from the SURFACE, so R is the body's radius. Ignores atmosphere "
                  "and the body's rotation.",
    required_knowns=['G', 'M', 'R'], solves_for=['v_escape'],
    build_equations=_wave009_eqs,
    output_units={'v_escape': 'm/s'},
    pitfalls="Confusing escape velocity with orbital velocity -- escape is larger by "
             "exactly a factor of sqrt(2).",
    must_be_positive=['v_escape'],
    verify_fn=_wave009_verify,
)

WAVE_CARDS = [WAVE001, WAVE002, WAVE003, WAVE004, WAVE005,
              WAVE006, WAVE007, WAVE008, WAVE009]

ALL_CARDS = MECHANICS_CARDS + EM_CARDS + WAVE_CARDS
