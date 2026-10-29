"""
Merge several results files (for example a run that stopped early plus the run for the
rest) into one, and print the outcome table by stratum with percentages.

Run from physics-engine/:
    python eval/combine_results.py benchmark_full_01_all.json benchmark_full_01.json benchmark_full_01_rest.json
    python eval/combine_results.py benchmark_full_01_all.json benchmark_full_01.json benchmark_full_01_rest.json --compare benchmark_pilot_run1.json

First name is the file to write, the rest are inputs. If a problem appears in more than
one input, the later file wins. With --compare, problems that appear in both the merged
file and the comparison file are checked for whether the outcome is the same, which
measures run-to-run variation. The output holds names, IDs and counts, no problem text.
"""
import argparse
import json
from collections import Counter

NUMERIC_KINDS = ("scorable", "partially_numeric")


def stratum(r):
    return "numeric" if r.get("kind") in NUMERIC_KINDS else "symbolic"


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["rows"]


def pct(n, d):
    return f"{n / d:5.1%}" if d else "  n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--compare", default=None)
    args = ap.parse_args()

    merged = {}
    for path in args.inputs:
        for r in load_rows(path):
            merged[r["problem_id"]] = r
    rows = list(merged.values())
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"summary": {"meta": {"merged_from": args.inputs}}, "rows": rows}, f, indent=2, default=str)

    outcomes = sorted({r["outcome"] for r in rows})
    n_num = sum(1 for r in rows if stratum(r) == "numeric")
    n_sym = len(rows) - n_num
    count = Counter((stratum(r), r["outcome"]) for r in rows)

    print(f"Merged {len(rows)} problems from {len(args.inputs)} file(s) -> {args.out}\n")
    print(f"{'outcome':28} {'numeric':>8} {'':>6} {'symbolic':>9} {'':>6} {'all':>5} {'':>6}")
    for o in outcomes:
        a, b = count[("numeric", o)], count[("symbolic", o)]
        print(f"{o:28} {a:8} {pct(a, n_num):>6} {b:9} {pct(b, n_sym):>6} {a + b:5} {pct(a + b, len(rows)):>6}")
    print(f"{'ALL':28} {n_num:8} {'':>6} {n_sym:9} {'':>6} {len(rows):5}")

    repaired = sum(1 for r in rows if (r.get("parse") or {}).get("json_repaired"))
    declined = [r for r in rows if r["outcome"] in ("declined_no_card", "declined_missing_knowns")]
    unrec = sum(1 for r in declined if (r.get("parse") or {}).get("unrecognized_names"))
    print(f"\nParses that needed a JSON/LaTeX repair: {repaired}")
    print(f"Declines where the parser used names outside the glossary: {unrec} of {len(declined)}")

    wrong = [r["problem_id"] for r in rows if r["outcome"] == "mismatch"]
    right = [r["problem_id"] for r in rows if r["outcome"] == "match"]
    print(f"\nAnswered and matched: {len(right)}  {right}")
    print(f"Answered and WRONG:   {len(wrong)}  {wrong}")

    if args.compare:
        other = {r["problem_id"]: r for r in load_rows(args.compare)}
        shared = [pid for pid in merged if pid in other]
        same = [pid for pid in shared if merged[pid]["outcome"] == other[pid]["outcome"]]
        print(f"\nRun-to-run check against {args.compare}: {len(shared)} shared problems, "
              f"{len(same)} with the same outcome ({pct(len(same), len(shared)).strip()})")
        for pid in shared:
            if pid not in same:
                print(f"  {pid}: {other[pid]['outcome']} -> {merged[pid]['outcome']}")


if __name__ == "__main__":
    main()
