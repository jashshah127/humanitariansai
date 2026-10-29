"""
Rescore a saved baseline run by VALUE instead of by variable NAME.

WHY THIS EXISTS
baseline_eval.py only counts an answer if the model's quantity name matches the
expected name exactly (v, s, a, T, F, t_flight, range_ ...). The prompt never tells
the model those names, so a correct reply such as

    FINAL ANSWER: final speed = 30 m/s
    FINAL ANSWER: distance = 180 m

scores as "no answer found" for v and s. The strict accuracy then measures name
matching, not physics.

RULE USED HERE (decided and documented, not tuned per problem)
  * Take every "FINAL ANSWER:" line from the model's saved reply.
  * Read ONE number from each (the first number after the last "=", with
    scientific notation handled). Units are ignored.
  * A problem is correct only if EVERY expected value is matched by a DIFFERENT
    extracted value within 1% relative tolerance (the same tolerance the original
    scorer uses). Order and names do not matter.
  * Nothing is auto-accepted beyond that. Unmatched expected values are listed
    together with every extracted value, so a human can check for unit-scaled
    answers (km vs m), extra rounding, or real errors.

Run from physics-engine/:
    python eval/rescore_baseline.py baseline_results_gemini.json

Report BOTH numbers (strict and value-matched) in the methodology document.
"""
import json
import re
import sys

TOL = 1e-2  # same relative tolerance as baseline_eval.values_match

_SCI = re.compile(
    r"([-+]?\d[\d,]*\.?\d*)\s*(?:×|x|X|\\times|\\cdot|\*)\s*10\s*\^\s*\{?\s*([-+]?\d+)\s*\}?"
)
_PLAIN = re.compile(r"[-+]?\d[\d,]*\.?\d*(?:[eE][-+]?\d+)?")
_LINE = re.compile(r"FINAL\s+ANSWER\W*(.*)", re.IGNORECASE)


def _num(text):
    """First number in text, or None. Scientific notation is read as one number."""
    t = text.replace("$", "").replace("\\,", "").replace("\\!", "")
    m = _SCI.search(t)
    if m:
        try:
            return float(m.group(1).replace(",", "")) * 10 ** int(m.group(2))
        except ValueError:
            return None
    m = _PLAIN.search(t)
    if m:
        try:
            return float(m.group(0).replace(",", ""))
        except ValueError:
            return None
    return None


def extract_values(raw):
    """One number per FINAL ANSWER line, in order of appearance."""
    values = []
    for line in raw.splitlines():
        m = _LINE.search(line)
        if not m:
            continue
        rhs = m.group(1)
        if "=" in rhs:
            rhs = rhs.rsplit("=", 1)[1]
        v = _num(rhs)
        if v is not None:
            values.append(v)
    return values


def close(got, expected):
    if expected == 0:
        return abs(got) < 1e-6
    return abs(got - expected) / abs(expected) < TOL


def match_all(extracted, expected_values):
    """One-to-one matching. Returns (all_matched, unmatched_expected)."""
    pool = list(extracted)
    unmatched = []
    for e in expected_values:
        hit = next((g for g in pool if close(g, e)), None)
        if hit is None:
            unmatched.append(e)
        else:
            pool.remove(hit)
    return (not unmatched), unmatched


def main(path):
    with open(path, encoding="utf-8") as f:
        results = json.load(f)

    strict = rescored = 0
    rows = []
    for r in results:
        expected = [d["expected"] for d in r["detail"].values()]
        extracted = extract_values(r["raw_response"])
        ok, unmatched = match_all(extracted, expected)
        strict += bool(r["all_correct"])
        rescored += ok
        rows.append({
            "problem_id": r["problem_id"],
            "strict_correct": bool(r["all_correct"]),
            "value_matched_correct": ok,
            "expected": expected,
            "extracted": extracted,
            "unmatched_expected": unmatched,
        })

    n = len(results)
    print(f"{'problem':10} {'strict':7} {'by value':9}  unmatched expected -> extracted")
    for row in rows:
        tail = ""
        if not row["value_matched_correct"]:
            tail = f"{row['unmatched_expected']} -> {row['extracted']}"
        print(f"{row['problem_id']:10} {str(row['strict_correct']):7} "
              f"{str(row['value_matched_correct']):9}  {tail}")

    print(f"\nStrict (name must match)    : {strict}/{n} = {strict / n:.1%}")
    print(f"Value-matched (name ignored): {rescored}/{n} = {rescored / n:.1%}")
    print("Check every row marked False by hand before quoting the second number.")

    out = path.replace(".json", "_rescored.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"strict": strict, "value_matched": rescored, "n": n, "rows": rows},
                  f, indent=2)
    print(f"Per-problem detail -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python eval/rescore_baseline.py baseline_results_gemini.json")
    main(sys.argv[1])
