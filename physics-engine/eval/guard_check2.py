"""
Second offline guard test, on saved results (no model calls). Idea: if the parser read a
quantity from the problem that the chosen formula card does not use, the engine may be
solving a simpler problem than the one asked, so it should decline.

For every answered problem this lists the parsed quantities the chosen card does not use.
Quantities the engine filled in itself (G, g, named-object values such as Earth's mass) are
ignored. A distractor in the problem (for example a satellite's mass) or a quantity the parser
always reports (a wave amplitude) can trigger a false alarm, so read the list.

Run from physics-engine/:
    python eval/guard_check2.py benchmark_ab_v2a.json benchmark_ab_v2b.json
    python eval/guard_check2.py benchmark_ab_v2a.json benchmark_ab_v2b.json --ignore A_amp m

--ignore  quantity names that never count as a sign of trouble (repeatable list).
Prints IDs, card names and quantity names only, no problem text.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_benchmark as rb  # noqa: E402,F401  (adds ../engine to sys.path)
from formula_kb import ALL_CARDS  # noqa: E402

CARDS = {c.id: c for c in ALL_CARDS}
ANSWERED = ("match", "mismatch", "answered_not_compared")


def short(pid):
    return pid.replace("ClassicalMechanics-", "M-").replace("ClassicalElectromagnetism-", "EM-")


def unused_for(row, ignore):
    card = CARDS.get(row.get("card"))
    if card is None:
        return None
    parse = row.get("parse") or {}
    own = [k for k in (parse.get("knowns") or {}) if k not in (parse.get("injected_constants") or {})]
    return [k for k in own if k not in card.required_knowns and k not in ignore]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--ignore", nargs="*", default=[])
    args = ap.parse_args()

    flagged = {"match": 0, "mismatch": 0}
    total = {"match": 0, "mismatch": 0}
    print(f"{'problem':8} {'outcome':10} {'run':26} {'card':20} parsed but unused by the card")
    for path in args.results:
        with open(path, encoding="utf-8") as f:
            rows = [r for r in json.load(f)["rows"] if r["outcome"] in ANSWERED]
        for r in sorted(rows, key=lambda r: r["problem_id"]):
            un = unused_for(r, set(args.ignore))
            o = r["outcome"]
            if o in total and un is not None:
                total[o] += 1
                flagged[o] += 1 if un else 0
            shown = "(card not found)" if un is None else (", ".join(un) or "-")
            print(f"{short(r['problem_id']):8} {o:10} {os.path.basename(path)[:26]:26} {str(r.get('card'))[:20]:20} {shown}")
    print()
    for o, label in (("mismatch", "wrong answers"), ("match", "right answers")):
        if total[o]:
            print(f"{label}: {flagged[o]} of {total[o]} would be declined by this guard")
    print("A good guard flags the wrong answers and leaves the right ones alone.")


if __name__ == "__main__":
    main()
