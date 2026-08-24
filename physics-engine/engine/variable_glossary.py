"""
The shared vocabulary between the LLM parser (Phase 1) and the formula-card KB (Phase 0).

WHY THIS EXISTS -- the failure mode it prevents:
The cards expect exact variable names: `v0`, `theta_deg`, `k_e`, `range_`. An LLM reading
raw problem text will naturally emit `initial_velocity`, `angle`, `coulomb_constant`,
`horizontal_range`. Both are "correct"; they just don't match, and the closure check would
report a gap for a problem the KB actually covers. That is a silent capability loss --
exactly the class of failure this project exists to avoid -- so the vocabulary is made
explicit here rather than left to prompt luck.

Two jobs:
  1. GLOSSARY  -- canonical name -> (description, unit, aliases). Fed into the parse prompt
                  so the LLM is told the vocabulary instead of guessing it, and used to
                  normalize whatever it returns anyway.
  2. CONSTANTS -- physical constants a student never states but a card requires. "Launched
                  at 25 m/s at 40 degrees" never mentions g=9.8, but MECH-KIN-PROJ needs it.
                  Injected automatically rather than expecting the LLM to remember.
"""
import sympy as sp
from scipy import constants as C

# ---------------------------------------------------------------------------
# Physical constants -- injected automatically, never parsed from problem text.
# Values come from scipy.constants (CODATA), not from memory.
# ---------------------------------------------------------------------------
CONSTANTS = {
    "g": 9.8,                                    # standard gravity, textbook convention
    "G": C.G,                                    # gravitational constant
    "k_e": float(1 / (4 * sp.pi * C.epsilon_0)), # Coulomb constant, derived not memorized
    "epsilon_0": C.epsilon_0,
    "mu_0": C.mu_0,
    "e_charge": C.elementary_charge,
    "m_proton": C.proton_mass,
    "m_electron": C.electron_mass,
}

# Constants that are so routinely implicit we inject them whenever a card wants them.
AUTO_INJECT = {"g", "G", "k_e", "epsilon_0", "mu_0"}


# ---------------------------------------------------------------------------
# Canonical variable glossary.
# entry: canonical -> dict(desc, unit, aliases)
# ---------------------------------------------------------------------------
GLOSSARY = {
    # --- kinematics
    "v0":       dict(desc="initial speed / velocity at t=0", unit="m/s",
                     aliases=["initial_velocity", "initial_speed", "u", "vi", "v_initial", "v_0"]),
    "v":        dict(desc="final or instantaneous speed", unit="m/s",
                     aliases=["final_velocity", "final_speed", "vf", "v_final", "speed"]),
    "a":        dict(desc="linear acceleration", unit="m/s^2",
                     aliases=["acceleration", "accel", "linear_acceleration"]),
    "t":        dict(desc="elapsed time", unit="s",
                     aliases=["time", "duration", "elapsed_time"]),
    "s":        dict(desc="distance travelled along the path", unit="m",
                     aliases=["distance", "displacement", "d_travelled", "x"]),
    "d":        dict(desc="distance slid or travelled (incline problems)", unit="m",
                     aliases=["slide_distance", "path_length"]),
    "theta_deg": dict(desc="angle in DEGREES (not radians)", unit="deg",
                     aliases=["angle", "theta", "angle_deg", "incline_angle", "launch_angle",
                              "angle_degrees", "elevation_angle"]),
    "t_flight": dict(desc="total projectile time of flight", unit="s",
                     aliases=["time_of_flight", "flight_time", "total_time"]),
    "h_max":    dict(desc="maximum height reached by a projectile", unit="m",
                     aliases=["max_height", "maximum_height", "peak_height", "apex"]),
    "range_":   dict(desc="horizontal range of a projectile", unit="m",
                     aliases=["range", "horizontal_range", "horizontal_distance", "R"]),

    # --- dynamics
    "m":        dict(desc="mass of the single object in the problem", unit="kg",
                     aliases=["mass", "M_object"]),
    "m1":       dict(desc="mass of the first / lighter object", unit="kg",
                     aliases=["mass1", "mass_1", "m_1", "first_mass"]),
    "m2":       dict(desc="mass of the second / heavier object", unit="kg",
                     aliases=["mass2", "mass_2", "m_2", "second_mass"]),
    "mu":       dict(desc="coefficient of kinetic friction", unit="dimensionless",
                     aliases=["friction", "mu_k", "coefficient_of_friction", "friction_coefficient"]),
    # `T` is the worst collision in the KB: string tension (N, force) on the Atwood card,
    # orbital period and cyclotron period (s, time) on two others. Force vs time is a
    # DIMENSIONAL contradiction, not just a naming overlap -- units.audit_units() detects
    # it automatically and independently, which is what makes it the objective trigger for
    # namespacing rather than a matter of taste. It is survivable today only because all
    # three are outputs and the ambiguity route arbitrates between them; the moment two of
    # them can close on the same problem, that route is the only thing standing between a
    # student and a tension value labelled as a period.
    "T":        dict(desc="string TENSION (N) in pulley/rope problems, OR orbital / cyclotron "
                          "PERIOD (s) in orbit and magnetic-field problems -- read which from "
                          "the problem",
                     unit="N or s",
                     aliases=["tension", "string_tension", "period", "orbital_period",
                              "cyclotron_period", "time_period"]),
    "M":        dict(desc="mass of an extended body (disk, sphere, planet)", unit="kg",
                     aliases=["body_mass", "planet_mass", "central_mass"]),

    # --- energy / momentum
    "k":        dict(desc="spring constant", unit="N/m",
                     aliases=["spring_constant", "stiffness", "k_spring"]),
    "x":        dict(desc="spring compression or extension", unit="m",
                     aliases=["compression", "extension", "displacement_spring", "x_compression"]),
    "v1":       dict(desc="initial velocity of the first object (collisions)", unit="m/s",
                     aliases=["velocity1", "v_1", "u1"]),
    "vf":       dict(desc="final common velocity after an inelastic collision", unit="m/s",
                     aliases=["final_common_velocity", "v_combined", "v_f"]),
    "KEi":      dict(desc="initial kinetic energy", unit="J", aliases=["KE_initial", "ke_i"]),
    "KEf":      dict(desc="final kinetic energy", unit="J", aliases=["KE_final", "ke_f"]),
    "dKE":      dict(desc="kinetic energy lost", unit="J",
                     aliases=["energy_lost", "KE_lost", "delta_KE", "kinetic_energy_lost"]),

    # --- rotation
    # `R` carries two unrelated meanings across this card set: radius (rotation,
    # Gauss's law) and resistance (RC circuits). Both are inputs, so retrieval never has
    # to choose -- the solves_for filter separates them. But the glossary MUST state both,
    # or a parser told "R = radius" never emits R for a 2 kOhm resistor and the RC card is
    # unreachable for a problem the KB actually covers. See SYMBOL_COLLISIONS.
    "R":        dict(desc="radius of a disk/sphere/loop (m), OR resistance in an RC circuit (ohm) "
                          "-- read which from the problem",
                     unit="m or ohm",
                     aliases=["radius", "disk_radius", "sphere_radius", "resistance",
                              "resistor", "R_resistance", "series_resistance"]),
    "tau":      dict(desc="applied torque (N*m) when GIVEN; RC time constant (s) when ASKED FOR",
                     unit="N*m or s", aliases=["torque", "moment", "time_constant", "RC_constant"]),
    "I":        dict(desc="moment of inertia", unit="kg*m^2",
                     aliases=["moment_of_inertia", "rotational_inertia"]),
    "alpha":    dict(desc="angular acceleration", unit="rad/s^2",
                     aliases=["angular_acceleration", "ang_accel"]),
    "omega":    dict(desc="angular speed", unit="rad/s",
                     aliases=["angular_velocity", "angular_speed", "w"]),

    # --- gravitation
    "h":        dict(desc="altitude ABOVE a surface (not orbital radius)", unit="m",
                     aliases=["altitude", "height_above_surface"]),
    "Re":       dict(desc="radius of the central body (e.g. Earth)", unit="m",
                     aliases=["R_earth", "earth_radius", "planet_radius", "R_planet"]),
    "r":        dict(desc="radial distance / separation / loop radius", unit="m",
                     aliases=["separation", "distance_between", "radial_distance", "loop_radius"]),

    # --- vibrations & waves
    # `k` is spring constant and `A` is loop area elsewhere in this KB, so wave number
    # and amplitude take distinct names rather than overloading them. The collision
    # audit is what makes that discipline checkable rather than a convention someone
    # remembers.
    "f":         dict(desc="frequency", unit="Hz",
                      aliases=["frequency", "freq", "nu"]),
    "lambda_":   dict(desc="wavelength", unit="m",
                      aliases=["wavelength", "lambda", "wave_length"]),
    "k_wave":    dict(desc="wave NUMBER, the coefficient of x in y=A sin(kx-wt). NOT the "
                           "spring constant", unit="1/m",
                      aliases=["wave_number", "wavenumber", "k_w", "angular_wavenumber"]),
    "T_period":  dict(desc="period of oscillation or of a wave", unit="s",
                      aliases=["period", "oscillation_period", "wave_period", "time_period"]),
    "A_amp":     dict(desc="amplitude of an oscillation or wave. NOT loop area", unit="m",
                      aliases=["amplitude", "peak_displacement", "A_amplitude"]),
    "coef_sin":  dict(desc="coefficient of the sine term in a*sin(wt)+b*cos(wt)", unit="m",
                      aliases=["sine_coefficient", "a_sin", "sin_coeff"]),
    "coef_cos":  dict(desc="coefficient of the cosine term in a*sin(wt)+b*cos(wt)", unit="m",
                      aliases=["cosine_coefficient", "b_cos", "cos_coeff"]),
    "c_damp":    dict(desc="damping coefficient", unit="kg/s",
                      aliases=["damping", "damping_coefficient", "damping_constant", "b_damp"]),
    "f_source":  dict(desc="frequency emitted by the source (Doppler)", unit="Hz",
                      aliases=["source_frequency", "emitted_frequency", "f_emitted"]),
    "f_observed": dict(desc="frequency heard by the observer (Doppler)", unit="Hz",
                       aliases=["observed_frequency", "heard_frequency", "apparent_frequency"]),
    "v_sound":   dict(desc="speed of sound in the medium", unit="m/s",
                      aliases=["sound_speed", "speed_of_sound", "c_sound"]),
    "v_observer": dict(desc="observer's speed, POSITIVE when moving toward the source",
                       unit="m/s", aliases=["observer_speed", "v_obs", "listener_speed"]),
    "v_source":  dict(desc="source's speed, POSITIVE when moving toward the observer",
                      unit="m/s", aliases=["source_speed", "v_src"]),
    "n_harmonic": dict(desc="harmonic number. Open pipe: any integer. Closed pipe: ODD only",
                       unit="dimensionless",
                       aliases=["harmonic", "harmonic_number", "mode_number", "n"]),
    "v_escape":  dict(desc="escape velocity from a body's surface", unit="m/s",
                      aliases=["escape_velocity", "escape_speed", "v_esc"]),

    # --- thermodynamics
    # `T` already means tension and period in this KB, so temperature takes T_temp
    # rather than overloading a symbol that is already carrying two meanings.
    "T_temp":     dict(desc="absolute temperature in KELVIN, never Celsius", unit="K",
                       aliases=["temperature", "temp", "T_kelvin", "abs_temperature"]),
    "T_hot":      dict(desc="hot reservoir temperature in KELVIN", unit="K",
                       aliases=["hot_temperature", "T_h", "source_temperature"]),
    "T_cold":     dict(desc="cold reservoir temperature in KELVIN", unit="K",
                       aliases=["cold_temperature", "T_c", "sink_temperature"]),
    "delta_T":    dict(desc="temperature CHANGE (a difference, so Celsius and Kelvin "
                            "intervals are numerically equal here)", unit="K",
                       aliases=["temperature_change", "dT", "temp_change"]),
    "P":          dict(desc="pressure", unit="Pa",
                       aliases=["pressure", "p_pressure"]),
    "V":          dict(desc="volume (thermo). NOTE: V also means voltage in the circuit "
                            "cards -- read which from the problem", unit="m^3",
                       aliases=["volume", "vol"]),
    "n_moles":    dict(desc="amount of substance in moles", unit="dimensionless",
                       aliases=["moles", "n_mol", "amount", "num_moles"]),
    "R_gas":      dict(desc="universal gas constant, 8.314 J/(mol*K)", unit="J/K",
                       aliases=["gas_constant", "R_universal", "ideal_gas_constant"]),
    "Q_heat":     dict(desc="heat energy transferred", unit="J",
                       aliases=["heat", "Q", "thermal_energy", "heat_energy"]),
    "W_work":     dict(desc="work done BY the system (check the sign convention)", unit="J",
                       aliases=["work", "W", "work_done"]),
    "delta_U":    dict(desc="change in internal energy", unit="J",
                       aliases=["internal_energy_change", "dU", "delta_internal_energy"]),
    "delta_S":    dict(desc="change in entropy", unit="J/K",
                       aliases=["entropy_change", "dS"]),
    "c_specific": dict(desc="specific heat capacity", unit="J/K",
                       aliases=["specific_heat", "heat_capacity", "c_heat", "specific_heat_capacity"]),
    "L_latent":   dict(desc="latent heat (fusion for melting, vaporization for boiling)",
                       unit="J", aliases=["latent_heat", "L_fusion", "L_vaporization", "latent"]),
    "efficiency": dict(desc="thermal efficiency, between 0 and 1", unit="dimensionless",
                       aliases=["eff", "thermal_efficiency", "carnot_efficiency"]),

    # --- electrostatics
    "q1_abs":   dict(desc="MAGNITUDE of the first charge (always positive)", unit="C",
                     aliases=["q1", "charge1", "charge_1", "q_1"]),
    "q2_abs":   dict(desc="MAGNITUDE of the second charge (always positive)", unit="C",
                     aliases=["q2", "charge2", "charge_2", "q_2"]),
    "Q":        dict(desc="source charge creating a field", unit="C",
                     aliases=["source_charge", "total_charge", "charge"]),
    "F":        dict(desc="force magnitude", unit="N", aliases=["force"]),
    "E":        dict(desc="electric field magnitude", unit="N/C",
                     aliases=["electric_field", "field_strength", "E_field"]),
    "r_in":     dict(desc="radius INSIDE a charged sphere (r < R)", unit="m",
                     aliases=["r_inside", "radius_inside", "r_internal"]),
    "r_out":    dict(desc="radius OUTSIDE a charged sphere (r > R)", unit="m",
                     aliases=["r_outside", "radius_outside", "r_external"]),
    "E_in":     dict(desc="field magnitude inside the sphere", unit="N/C", aliases=["E_inside"]),
    "E_out":    dict(desc="field magnitude outside the sphere", unit="N/C", aliases=["E_outside"]),

    # --- circuits
    "R1":       dict(desc="first resistance", unit="ohm", aliases=["resistance1", "R_1"]),
    "R2":       dict(desc="second resistance", unit="ohm", aliases=["resistance2", "R_2"]),
    "R3":       dict(desc="third resistance", unit="ohm", aliases=["resistance3", "R_3"]),
    "V":        dict(desc="source voltage / EMF of the supply", unit="V",
                     aliases=["voltage", "emf_source", "V_source", "battery_voltage"]),
    "V0":       dict(desc="battery voltage in an RC circuit", unit="V",
                     aliases=["V_battery", "V_supply", "V_0"]),
    "C":        dict(desc="capacitance", unit="F", aliases=["capacitance", "cap"]),
    "R_series": dict(desc="equivalent resistance of the series pair", unit="ohm", aliases=[]),
    "R_eq":     dict(desc="total equivalent resistance", unit="ohm",
                     aliases=["equivalent_resistance", "R_total", "R_equivalent"]),
    "I_total":  dict(desc="total current from the source", unit="A",
                     aliases=["total_current", "I_source"]),
    "I_branch1": dict(desc="current through the series branch", unit="A", aliases=[]),
    "I_branch2": dict(desc="current through the third-resistor branch", unit="A", aliases=[]),
    # `tau` intentionally covers BOTH torque and the RC time constant, because the cards
    # do. It survives only because torque is always an input and the time constant is
    # always an output, so retrieval never has to choose between them. That is a property
    # of these 16 cards, not a guarantee -- see SYMBOL_COLLISIONS below.
    "Vc":       dict(desc="voltage across the capacitor", unit="V",
                     aliases=["V_capacitor", "V_C", "capacitor_voltage"]),

    # --- magnetism / induction
    "B":        dict(desc="magnetic field magnitude", unit="T",
                     aliases=["magnetic_field", "B_field", "flux_density"]),
    "q":        dict(desc="charge of the moving particle", unit="C",
                     aliases=["particle_charge", "charge_particle"]),
    "L":        dict(desc="length of a current-carrying wire", unit="m",
                     aliases=["wire_length", "length"]),
    "dBdt":     dict(desc="rate of change of magnetic field", unit="T/s",
                     aliases=["dB_dt", "rate_of_change_B", "B_rate", "dBydt"]),
    "A":        dict(desc="loop area", unit="m^2", aliases=["area", "loop_area"]),
    "EMF":      dict(desc="induced electromotive force", unit="V",
                     aliases=["emf", "induced_emf", "induced_voltage"]),
}

# Reverse lookup: alias (lowercased) -> canonical
_ALIAS_TO_CANONICAL = {}
for canonical, meta in GLOSSARY.items():
    _ALIAS_TO_CANONICAL[canonical.lower()] = canonical
    for alias in meta["aliases"]:
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical


def normalize_name(name):
    """Map whatever the LLM emitted onto a canonical card variable name.
    Returns (canonical_name, was_recognized)."""
    if name in GLOSSARY:
        return name, True
    hit = _ALIAS_TO_CANONICAL.get(name.strip().lower())
    if hit:
        return hit, True
    return name, False


def normalize_parse(knowns, unknowns):
    """Normalize a raw LLM parse onto card vocabulary.

    Returns (knowns, unknowns, report) where report records every rename and every
    name we could not place -- unrecognized names are NOT silently dropped, because a
    dropped known becomes a mysterious closure gap three stages later."""
    norm_knowns, norm_unknowns = {}, []
    renamed, unrecognized = {}, []

    for name, value in knowns.items():
        canonical, ok = normalize_name(name)
        if not ok:
            unrecognized.append(name)
        elif canonical != name:
            renamed[name] = canonical
        norm_knowns[canonical] = value

    for name in unknowns:
        canonical, ok = normalize_name(name)
        if not ok:
            unrecognized.append(name)
        elif canonical != name:
            renamed[name] = canonical
        norm_unknowns.append(canonical)

    return norm_knowns, norm_unknowns, {"renamed": renamed, "unrecognized": unrecognized}


def inject_constants(knowns, unknowns=None, cards=None):
    """Add physical constants the student never states but a card needs.

    SCOPED, not blanket. Injecting every constant into every problem is tempting and
    wrong: it puts k_e into a pure-mechanics parse, which makes E&M cards look
    satisfiable to retrieval's ranking and can manufacture ambiguity that the physics
    does not actually contain. So only constants required by a card that can solve for
    something actually being asked get injected.

    Falls back to the blanket AUTO_INJECT set when no card list is supplied, so calling
    this without the KB still works -- just less precisely.

    Never overwrites a value already present: a problem stating 'on the Moon, g = 1.62'
    must beat the default."""
    injected = {}
    if cards is not None and unknowns:
        wanted_unknowns = set(unknowns)
        needed = set()
        for card in cards:
            if set(card.solves_for) & wanted_unknowns:
                needed |= set(card.required_knowns) & set(CONSTANTS)
    else:
        needed = set(AUTO_INJECT)

    for const in needed:
        if const in CONSTANTS and const not in knowns:
            knowns[const] = CONSTANTS[const]
            injected[const] = CONSTANTS[const]
    return knowns, injected


def audit_symbol_collisions(cards):
    """Derive the live symbol collisions FROM the cards, rather than maintaining a list
    by hand that drifts the moment someone adds a card.

    Returns dict with:
      output_collisions -- one symbol, several cards claiming to solve for it. These are
                           the dangerous ones: retrieval must choose, and choosing wrong
                           is a wrong answer. The V2 ambiguity route is the safety net.
      input_collisions  -- one symbol meaning different things as an input. Safe today
                           only because the solves_for filter separates them.
      undocumented      -- card variables missing from the GLOSSARY entirely, which the
                           parser therefore cannot be told to produce.

    Run this in CI. When output_collisions grows past what the ambiguity route can
    arbitrate, that is the signal to namespace symbols per physical quantity.
    """
    from collections import defaultdict
    as_input, as_output = defaultdict(list), defaultdict(list)
    for c in cards:
        for k in c.required_knowns:
            as_input[k].append(c.id)
        for u in c.solves_for:
            as_output[u].append(c.id)

    documented = set(GLOSSARY) | set(CONSTANTS)
    used = set(as_input) | set(as_output)
    return {
        "output_collisions": {s: ids for s, ids in as_output.items() if len(ids) > 1},
        "input_collisions": {s: ids for s, ids in as_input.items()
                             if len(ids) > 1 and s not in CONSTANTS},
        "undocumented": sorted(used - documented),
    }


def glossary_for_prompt(topic=None):
    """Render the glossary as prompt text so the parser is TOLD the vocabulary
    rather than left to invent it. Formula-card constants are excluded -- the LLM
    should not be asked to recall g or k_e; those get injected from scipy."""
    lines = []
    for canonical, meta in GLOSSARY.items():
        if canonical in CONSTANTS:
            continue
        lines.append(f"  {canonical} ({meta['unit']}) - {meta['desc']}")
    return "\n".join(lines)
