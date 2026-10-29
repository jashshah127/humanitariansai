"""
Look inside a results file written by run_sample.py / run_benchmark.py.

Run from physics-engine/:
    python eval/inspect_outcome.py benchmark_pilot_run1.json
    python eval/inspect_outcome.py benchmark_pilot_run1.json --outcome mismatch
    python eval/inspect_outcome.py benchmark_pilot_run1.json --outcome parse_found_no_unknown --n 5

Without --outcome it prints a table of outcome by problem stratum. With --outcome it
prints, for up to --n problems with that outcome, the problem text (read from the local
CSV), what the parser returned, and what the engine did. Problem text is dataset content:
read it on screen, do not paste it into documents or the repo.
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_benchmark as rb  # noqa: E402

_cache = {}


def problem_text(pid):
    subject, idx = pid.rsplit("-", 1)
    if subject not in _cache:
        _cache[subject] = rb.load(subject).set_index("index")
    try:
        return str(_cache[subject].loc[int(idx), "problem"])
    except Exception:
        return "(problem text not found)"


def short(x, n=500):
    s = str(x)
    return s if len(s) <= n else s[:n] + " ..."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--outcome", default=None)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--stratum", choices=["numeric", "symbolic"], default=None)
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        rows = json.load(f)["rows"]

    stratum = lambda r: "numeric" if r.get("kind") in ("scorable", "partially_numeric") else "symbolic"
    table = Counter((stratum(r), r["outcome"]) for r in rows)
    outcomes = sorted({o for _, o in table})
    print(f"{'outcome':28} {'numeric':>8} {'symbolic':>9} {'total':>6}")
    for o in outcomes:
        a, b = table[("numeric", o)], table[("symbolic", o)]
        print(f"{o:28} {a:8} {b:9} {a + b:6}")
    print(f"{'ALL':28} {sum(1 for r in rows if stratum(r) == 'numeric'):8} "
          f"{sum(1 for r in rows if stratum(r) == 'symbolic'):9} {len(rows):6}")

    if not args.outcome:
        return
    chosen = [r for r in rows if r["outcome"] == args.outcome
              and (args.stratum is None or stratum(r) == args.stratum)][: args.n]
    print(f"\n{len(chosen)} example(s) of {args.outcome}\n")
    for r in chosen:
        p = r.get("parse") or {}
        print("=" * 72)
        print(r["problem_id"], f"[{stratum(r)}]")
        print("PROBLEM:", short(problem_text(r["problem_id"])))
        print("PARSED knowns:", short(p.get("knowns"), 300))
        print("PARSED unknowns:", p.get("unknowns"), "| unrecognized names:", p.get("unrecognized_names"))
        if r.get("raw_reply"):
            print("MODEL REPLY:", short(r["raw_reply"], 500))
        for key in ("card", "cards_considered", "plan_reason", "engine", "engine_symbolic", "detail", "truth"):
            if r.get(key) not in (None, "", [], {}):
                print(f"{key.upper()}:", short(r[key], 300))


if __name__ == "__main__":
    main()
