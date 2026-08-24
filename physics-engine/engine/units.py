"""
UNIT CONSISTENCY -- partial delivery of the brief's Phase 1 line, "LLM + SymPy/pint
tool use."

HONEST SCOPE, stated up front: `pint` is NOT used here. It could not be installed in
the build environment (no outbound network), so rather than write code against a library
that was never executed even once, this uses `sympy.physics.units`, which is present and
was actually run. What that buys is real but narrower than pint would give:

  DOES   check that every unit string in the KB parses to a genuine physical dimension,
         catching typos and nonsense units.
  DOES   cross-check card-declared output units against the glossary's unit for the same
         variable, catching a card that says `v` is in metres.
  DOES NOT propagate units through the algebra itself. The cards bake numeric values into
         their equations before sympy ever sees them, so there is no unit-carrying quantity
         left to propagate. Getting that would mean rewriting cards to build equations
         symbolically first and substitute numbers last -- a real change, worth doing,
         deliberately not smuggled in under a "units" ticket.

So: unit DECLARATIONS are now verified. Unit PROPAGATION through the solve is still the
open item, and the README says so rather than letting "units: done" imply more.
"""
import re

from sympy.physics import units as u
from sympy.physics.units.systems.si import SI

# unit-string token -> sympy unit. The KB writes units as plain strings ("m/s^2",
# "kg*m^2", "N/C"), so they need a parser rather than eval.
_TOKENS = {
    "m": u.meter, "s": u.second, "kg": u.kilogram, "N": u.newton, "J": u.joule,
    "W": u.watt, "C": u.coulomb, "V": u.volt, "A": u.ampere, "ohm": u.ohm,
    "F": u.farad, "T": u.tesla, "Wb": u.weber, "H": u.henry, "Hz": u.hertz,
    "rad": u.radian, "deg": u.degree, "K": u.kelvin,
    # thermodynamics
    "Pa": u.pascal, "mol": u.mole, "L": u.liter, "atm": u.atmosphere,
}

# Units the KB uses that carry no dimension, or that are deliberately ambiguous.
_DIMENSIONLESS = {"dimensionless", ""}


class UnitParseError(Exception):
    pass


def parse_unit(unit_str):
    """Turn a KB unit string into a sympy unit expression.

    Handles the 'm or ohm' form used by genuinely overloaded symbols (see the R entry
    in variable_glossary) by returning a list of alternatives rather than pretending
    there is one answer."""
    unit_str = unit_str.strip()
    if unit_str.lower() in _DIMENSIONLESS:
        return [1]
    if " or " in unit_str:
        out = []
        for alt in unit_str.split(" or "):
            out.extend(parse_unit(alt))
        return out

    expr = unit_str
    # rad/s^2 -> rad/s**2
    expr = expr.replace("^", "**")
    tokens = re.findall(r"[A-Za-z_]+", expr)
    unknown = [t for t in tokens if t not in _TOKENS]
    if unknown:
        raise UnitParseError(f"unrecognized unit token(s) {unknown} in {unit_str!r}")

    namespace = dict(_TOKENS)
    try:
        return [eval(expr, {"__builtins__": {}}, namespace)]  # noqa: S307 - fixed namespace
    except Exception as e:
        raise UnitParseError(f"could not parse unit {unit_str!r}: {e}")


def dimension_of(unit_str):
    """Physical dimension(s) of a unit string, e.g. 'm/s' -> length/time."""
    return [SI.get_dimensional_expr(x) if x != 1 else 1 for x in parse_unit(unit_str)]


def audit_units(cards, glossary):
    """CI check. Returns a dict of findings; an empty findings dict is a pass.

    unparseable       -- unit strings that are not valid units at all
    card_vs_glossary  -- a card declares an output unit whose dimension disagrees with
                         the glossary's unit for that same variable. Either the card is
                         wrong or the glossary is; both are worth knowing before the
                         parser starts trusting the glossary to describe reality.
    """
    unparseable, mismatches = [], []

    for name, meta in glossary.items():
        try:
            dimension_of(meta["unit"])
        except UnitParseError as e:
            unparseable.append({"where": f"glossary[{name}]", "error": str(e)})

    for card in cards:
        for var, unit_str in card.output_units.items():
            try:
                card_dims = dimension_of(unit_str)
            except UnitParseError as e:
                unparseable.append({"where": f"{card.id}.output_units[{var}]", "error": str(e)})
                continue
            if var not in glossary:
                continue
            try:
                gloss_dims = dimension_of(glossary[var]["unit"])
            except UnitParseError:
                continue  # already reported above
            if not set(map(str, card_dims)) & set(map(str, gloss_dims)):
                mismatches.append({
                    "variable": var,
                    "card": card.id,
                    "card_unit": unit_str,
                    "card_dimension": str(card_dims[0]),
                    "glossary_unit": glossary[var]["unit"],
                    "glossary_dimension": str(gloss_dims[0]),
                })

    return {"unparseable": unparseable, "card_vs_glossary": mismatches}
