"""
Check that symbolic answers can be compared: does the LaTeX parser work, and does an engine
formula come out equal to the same formula written as LaTeX in the benchmark?

It runs a small set of known pairs through answer_match.symbolic_equal and prints, for each,
what was expected and what came out. A pair that should be equal but is reported different
usually means the two sides name a quantity differently (the engine writes m2, LaTeX writes
m_2). Where the two sides use different symbol names and are not equal, the answer must be
"cannot decide" and not "different", because the difference may be only naming.

Run from physics-engine/:
    pip install antlr4-python3-runtime==4.11
    python eval/antlr_check.py
If that install fails, an alternative parser may work:
    pip install lark
    python eval/antlr_check.py --backend lark

Prints formulas only, no problem text.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import answer_match as am  # noqa: E402

# (engine expression, ground-truth LaTeX, expected: True equal / False different / None cannot decide)
CASES = [
    ("m*v**2/2", r"\frac{1}{2}mv^2", True),
    ("m*v**2/2", r"\frac{m v^2}{2}", True),
    ("m*g*h", r"mgh", True),
    ("m*g*h", r"2mgh", False),
    ("m*g*h", r"mg", None),
    ("2*pi*sqrt(m/k)", r"2\pi\sqrt{\frac{m}{k}}", True),
    ("sqrt(2*g*h)", r"\sqrt{2gh}", True),
    ("sqrt(2*g*h)", r"\sqrt{gh}", False),
    ("G*M*m/r**2", r"\frac{GMm}{r^2}", True),
    ("g*(m2-m1)/(m1+m2)", r"\frac{g(m_2-m_1)}{m_1+m_2}", True),
    ("g*(m2-m1)/(m1+m2)", r"-\frac{g(m_1-m_2)}{m_1+m_2}", True),
    ("v0*t + a*t**2/2", r"v_0 t + \frac{1}{2} a t^2", True),
    ("mu0*I/(2*pi*r)", r"\frac{\mu_0 I}{2\pi r}", True),
    ("omega/k_wave", r"\frac{\omega}{k}", None),
    ("T", r"T", True),
    ("x", r"\text{see figure}", None),
]


def use_lark():
    from sympy.parsing.latex import parse_latex

    def parse(s):
        try:
            return parse_latex(s, backend="lark")
        except Exception:
            return None
    am._try_parse_latex = parse


def label(v):
    return {True: "equal", False: "different", None: "cannot decide"}[v]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["antlr", "lark"], default="antlr")
    args = ap.parse_args()
    if args.backend == "lark":
        use_lark()

    probe = am._try_parse_latex(r"\frac{1}{2}")
    if probe is None:
        print("The LaTeX parser is not available, so symbolic answers cannot be compared yet.")
        print("Install it with:  pip install antlr4-python3-runtime==4.11")
        print("or try:           pip install lark   and run again with --backend lark")
        sys.exit(2)
    print(f"LaTeX parser works (backend: {args.backend}).\n")

    bad = []
    print(f"{'result':6} {'expected':14} {'got':14} engine | truth LaTeX")
    for eng, truth, want in CASES:
        got = am.symbolic_equal(eng, truth)
        ok = got is want
        print(f"{'PASS' if ok else 'FAIL':6} {label(want):14} {label(got):14} {eng}  |  {truth}")
        if not ok:
            parsed = am._try_parse_latex(am.strip_equation(truth))
            names = sorted(str(s) for s in parsed.free_symbols) if parsed is not None else "unparsed"
            bad.append((eng, truth, names))
    print(f"\n{len(CASES) - len(bad)} of {len(CASES)} cases behave as expected.")
    for eng, truth, names in bad:
        print(f"  FAIL: {eng}  vs  {truth}\n        the parser read the LaTeX symbols as: {names}")
    if bad:
        print("\nIf the symbols differ only in how subscripts are written (m_{2} against m2), the fix is to\n"
              "rename symbols before comparing, not to change the parser.")


if __name__ == "__main__":
    main()
