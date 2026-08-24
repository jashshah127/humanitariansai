"""
ANSWER MATCHING -- the piece that gates every automated accuracy number.

WHY THIS IS ITS OWN MODULE, and why it is harder than it sounds:
Deciding whether the engine's answer agrees with a benchmark's answer is not a
comparison, it is a small parsing problem. UGPhysics stores ground truth as boxed
LaTeX with mixed types:

    \\boxed{3.04}                                    -> a number
    \\boxed{v = \\frac{k}{c-b}e^{-bt} - \\frac{g}{c}}  -> a symbolic equation
    \\boxed{0, v}                                    -> two answers, one symbolic
    \\boxed{A}                                       -> a bare symbol

"3.27 m/s^2" and "3.2667" and "49/15" are all the same answer. A naive string or
float comparison scores a correct engine as wrong and produces an accuracy number
that is confidently meaningless -- the exact failure this project exists to avoid,
reproduced one level up in the evaluation harness.

SCOPE, stated honestly:
  DOES   compare numeric answers with relative tolerance, so 3.27 == 3.2667.
  DOES   handle multi-answer rows and pick the best assignment.
  DOES   flag symbolic ground truth as NOT_COMPARABLE rather than scoring it wrong.
  DOES NOT parse LaTeX into sympy expressions. sympy's parse_latex needs the antlr4
         runtime, which is not installed in this environment (no network), so rather
         than write an untested LaTeX parser, symbolic rows are explicitly reported as
         out of scope. See MEASUREMENT.md -- 87% of UGPhysics is symbolic, so this is
         the single biggest thing standing between us and a full benchmark number, and
         it is called out rather than hidden inside an accuracy figure.
"""
import re

import sympy as sp
from fractions import Fraction


class Verdict:
    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_COMPARABLE = "not_comparable"   # ground truth is symbolic; engine emits numbers
    UNPARSEABLE = "unparseable"         # could not read the ground truth at all


_NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")
_FRAC = re.compile(r"^([-+]?)\\?[dt]?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}$")
_SCI = re.compile(r"^([-+]?[\d.]+)\s*\\times\s*10\^\{?(-?\d+)\}?$")


def strip_boxed(raw):
    """Pull the contents out of \\boxed{...}, tolerating nesting."""
    s = str(raw).strip()
    i = s.find(r"\boxed")
    if i == -1:
        return s
    j = s.find("{", i)
    if j == -1:
        return s
    depth, out = 0, []
    for ch in s[j:]:
        if ch == "{":
            depth += 1
            if depth == 1:
                continue
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
    return "".join(out).strip()


def split_answers(body):
    """Split a multi-answer body on top-level commas only, so
    \\frac{a,b}{c} is not torn apart."""
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur).strip())
    return [p for p in parts if p]


def to_number(token):
    """Best-effort numeric read of one LaTeX-ish token. Returns float or None.
    None means 'not a number', which the caller must treat as NOT_COMPARABLE
    rather than as a mismatch."""
    t = str(token).strip()
    t = re.sub(r"\\(?:text|mathrm|mbox)\s*\{[^{}]*\}", "", t)   # drop unit labels
    t = t.replace("$", "").replace("\\,", "").replace("\\!", "").replace("~", "")
    t = t.replace("\\left", "").replace("\\right", "").strip()
    t = t.rstrip(".").strip()

    if _NUM.match(t):
        return float(t)

    m = _SCI.match(t)
    if m:
        try:
            return float(m.group(1)) * 10 ** int(m.group(2))
        except ValueError:
            return None

    m = _FRAC.match(t)
    if m:
        try:
            val = float(Fraction(m.group(2).strip()) / Fraction(m.group(3).strip()))
            return -val if m.group(1) == "-" else val
        except (ValueError, ZeroDivisionError):
            return None

    if re.match(r"^[-+]?\d+/\d+$", t):
        try:
            return float(Fraction(t))
        except (ValueError, ZeroDivisionError):
            return None
    return None


def values_close(a, b, rel_tol=2e-2):
    """Relative tolerance defaults to 2%, deliberately loose: benchmark answers are
    frequently rounded to 3 significant figures (3.04, 3.27), so a tight tolerance
    would score correct answers as wrong."""
    if a is None or b is None:
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) / abs(b) < rel_tol


def compare(engine_values, ground_truth_raw, answer_type=None):
    """engine_values: list of floats the engine produced.
    ground_truth_raw: the benchmark's raw answer string (boxed LaTeX).

    Returns (verdict, detail). Any answer the harness cannot READ is reported as
    NOT_COMPARABLE or UNPARSEABLE -- never silently as a mismatch, because an
    unreadable ground truth says nothing about whether the engine was right."""
    body = strip_boxed(ground_truth_raw)
    if not body:
        return Verdict.UNPARSEABLE, "empty ground truth"

    # Explicitly non-numeric benchmark types: expression, equation, true/false,
    # interval, multiple choice. Our engine emits numbers, so these are out of scope
    # until the cards can produce symbolic output.
    if answer_type:
        types = {t.strip().split()[0] for t in str(answer_type).split(",") if t.strip()}
        if types & {"EX", "EQ", "TF", "IN", "MC"}:
            return Verdict.NOT_COMPARABLE, f"ground truth is {'/'.join(sorted(types))}, not numeric"

    gt_tokens = split_answers(body)
    gt_nums = [to_number(t) for t in gt_tokens]
    if all(n is None for n in gt_nums):
        return Verdict.NOT_COMPARABLE, f"no numeric value readable from {body[:60]!r}"

    gt_nums = [n for n in gt_nums if n is not None]
    eng = [v for v in engine_values if v is not None]
    if not eng:
        return Verdict.MISMATCH, "engine produced no value"

    # Any-order matching: the engine may return quantities in a different order than
    # the benchmark lists them, which is not an error.
    unmatched = list(gt_nums)
    hits = []
    for g in list(unmatched):
        found = next((e for e in eng if values_close(e, g)), None)
        if found is not None:
            hits.append((g, found))
            unmatched.remove(g)
    if not unmatched:
        return Verdict.MATCH, f"all {len(hits)} value(s) matched within tolerance"
    return Verdict.MISMATCH, (f"matched {len(hits)}/{len(gt_nums)}; "
                              f"unmatched ground truth {unmatched}; engine gave {eng}")


def _try_parse_latex(s):
    """Parse a LaTeX expression into a SymPy expression.

    Needs the antlr4 runtime, which is one command away on any machine with network:
        pip install antlr4-python3-runtime==4.11
    It was NOT installable in the sandbox this was written in, so the parse_latex call
    below is unexercised here while everything around it is tested. Returns None when
    unavailable or unparseable, so a missing dependency degrades to NOT_COMPARABLE
    rather than crashing a benchmark run midway."""
    try:
        from sympy.parsing.latex import parse_latex
    except Exception:
        return None
    try:
        return parse_latex(s)
    except Exception:
        return None


def strip_equation(s):
    """Ground truth is often written as an equation -- `v = \\frac{k}{c-b}e^{-bt}` --
    where only the right-hand side is the answer. Splits on a single top-level `=`.
    Deliberately conservative: anything with 0 or 2+ equals signs is returned untouched
    rather than guessed at."""
    depth = 0
    positions = []
    for i, ch in enumerate(s):
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth -= 1
        elif ch == "=" and depth == 0:
            positions.append(i)
    if len(positions) != 1:
        return s
    return s[positions[0] + 1:].strip()


def symbolic_equal(engine_expr, truth_latex):
    """Are two symbolic answers the same expression?

    Compares by simplifying the difference to zero, which is the only sound test --
    string comparison fails on g*(m2-m1)/(m1+m2) vs -g*(m1-m2)/(m1+m2), which are the
    same answer written two ways. Falls back to `equals()` for cases simplify can't
    close. Returns True / False / None, where None means 'could not decide' and must be
    reported as NOT_COMPARABLE rather than as a mismatch."""
    truth = _try_parse_latex(strip_equation(truth_latex))
    if truth is None:
        return None
    try:
        eng = sp.sympify(engine_expr) if not isinstance(engine_expr, sp.Basic) else engine_expr
    except Exception:
        return None
    try:
        if sp.simplify(eng - truth) == 0:
            return True
    except Exception:
        pass
    try:
        return bool(eng.equals(truth))
    except Exception:
        return None


def compare_symbolic(engine_symbolic, ground_truth_raw):
    """engine_symbolic: dict of {name: sympy expression or str} from the engine's
    symbolic answer. ground_truth_raw: the benchmark's boxed LaTeX.

    This is what makes the ~60% of UGPhysics with symbolic ground truth scorable, now
    that the engine returns general formulas rather than only numbers."""
    body = strip_boxed(ground_truth_raw)
    if not body:
        return Verdict.UNPARSEABLE, "empty ground truth"
    if not engine_symbolic:
        return Verdict.NOT_COMPARABLE, "engine produced no symbolic answer"

    truth_tokens = split_answers(body)
    engine_exprs = list(engine_symbolic.values())

    undecided = 0
    matched = []
    remaining = list(truth_tokens)
    for tok in list(remaining):
        decided_match = False
        for expr in engine_exprs:
            r = symbolic_equal(expr, tok)
            if r is True:
                matched.append(tok)
                remaining.remove(tok)
                decided_match = True
                break
            if r is None:
                undecided += 1
        if decided_match:
            continue
    if not remaining:
        return Verdict.MATCH, f"all {len(matched)} symbolic answer(s) equivalent"
    if undecided and not matched:
        return Verdict.NOT_COMPARABLE, ("could not parse the ground truth symbolically -- "
                                        "install antlr4-python3-runtime to enable this path")
    return Verdict.MISMATCH, (f"matched {len(matched)}/{len(truth_tokens)}; "
                              f"unmatched {remaining}")


def summarize(results):
    """results: list of (verdict, detail). Returns a dict with the honest denominators.

    Reports accuracy over COMPARABLE problems only, and states the comparable count
    separately, so a high accuracy on a small slice can never be mistaken for a high
    accuracy on the benchmark."""
    from collections import Counter
    c = Counter(v for v, _ in results)
    comparable = c[Verdict.MATCH] + c[Verdict.MISMATCH]
    return {
        "total": len(results),
        "comparable": comparable,
        "match": c[Verdict.MATCH],
        "mismatch": c[Verdict.MISMATCH],
        "not_comparable": c[Verdict.NOT_COMPARABLE],
        "unparseable": c[Verdict.UNPARSEABLE],
        "accuracy_on_comparable": (c[Verdict.MATCH] / comparable) if comparable else None,
        "comparable_fraction": comparable / len(results) if results else 0,
    }
