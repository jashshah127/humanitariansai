"""
For every problem a run declined, show what the parser gave and what the cards it
considered still needed. One line per card, so a naming mismatch (the card wants `R`,
the parser wrote `Re`) or a left-out quantity is visible at a glance.

Run from physics-engine/:
    python eval/missing_knowns.py benchmark_pilot_run1.json
    python eval/missing_knowns.py benchmark_pilot_run1.json --stratum numeric
    python eval/missing_knowns.py benchmark_pilot_run1.json --outcome declined_no_card

Reads only names and IDs from the results file, so there is no dataset text in the output.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_benchmark as rb  # noqa: E402,F401  (adds ../engine to sys.path)
from formula_kb import ALL_CARDS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--outcome", default="declined_missing_knowns")
    ap.add_argument("--stratum", choices=["numeric", "symbolic"], default=None)
    args = ap.parse_args()

    cards = {c.id: c for c in ALL_CARDS}
    with open(args.results, encoding="utf-8") as f:
        rows = json.load(f)["rows"]

    stratum = lambda r: "numeric" if r.get("kind") in ("scorable", "partially_numeric") else "symbolic"
    shown = 0
    for r in rows:
        if r["outcome"] != args.outcome:
            continue
        if args.stratum and stratum(r) != args.stratum:
            continue
        p = r.get("parse") or {}
        given = sorted((p.get("knowns") or {}).keys())
        print(f"{r['problem_id']} [{stratum(r)}]  wants: {p.get('unknowns')}  parsed: {given}")
        for cid in r.get("cards_considered") or []:
            card = cards.get(cid)
            if card is None:
                print(f"    {cid}: card not found in this version of formula_kb")
                continue
            missing = [k for k in card.required_knowns if k not in (p.get("knowns") or {})]
            print(f"    {cid}: needs {list(card.required_knowns)}  missing {missing}")
        shown += 1
    print(f"\n{shown} problem(s) with outcome {args.outcome}")


if __name__ == "__main__":
    main()
