"""
Offline test of an "unused number" guard. Idea: if a problem states a number that the
parser never used for any quantity, the engine probably did not read the whole problem,
so it should decline instead of answering. This script checks that idea on SAVED results,
with no model calls: for every answered problem it lists the numbers in the problem text
that no parsed quantity accounts for.

Run from physics-engine/:
    python eval/guard_check.py benchmark_full_01_all.json benchmark_ab_v0.json benchmark_ab_v0b.json benchmark_ab_v1a.json
    python eval/guard_check.py benchmark_ab_v0.json --all-outcomes

A number in the text counts as USED when some parsed value equals it, or equals it times a
power of ten (so 266 km and 266000 m match). This is a rough rule: dates, counts like
"two bodies", and numbers hidden in LaTeX can be flagged by mistake, and a number the
parser used after a conversion other than a power of ten (degrees to radians) can be
missed. So read the list; do not treat a flag as proof.

Prints IDs, outcomes and numbers only, no problem text.
"""
import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_benchmark as rb  # noqa: E402

NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?:\s*(?:\\times|\\cdot|x|×)\s*10\^\{?(-?\d+)\}?)?")
ANSWERED = ("match", "mismatch", "answered_not_compared")
_cache = {}


def text_of(pid):
    subject, idx = pid.rsplit("-", 1)
    if subject not in _cache:
        _cache[subject] = rb.load(subject).set_index("index")
    try:
        return str(_cache[subject].loc[int(idx), "problem"])
    except Exception:
        return ""


def numbers_in(text):
    out = []
    for m in NUM.finditer(text):
        v = float(m.group(1))
        if m.group(2) is not None:
            v *= 10 ** int(m.group(2))
        out.append(v)
    return out


def is_pow10_multiple(a, b):
    if a == 0 or b == 0:
        return a == b
    r = abs(a / b)
    k = round(math.log10(r))
    return abs(k) <= 12 and abs(r - 10 ** k) / (10 ** k) < 1e-6


def used(n, values):
    return any(is_pow10_multiple(n, v) or is_pow10_multiple(n * math.pi, v)
               or is_pow10_multiple(n / math.pi, v) for v in values)


def parsed_values(row):
    vals = []
    for v in ((row.get("parse") or {}).get("knowns") or {}).values():
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            pass
    return vals


def short(pid):
    return pid.replace("ClassicalMechanics-", "M-").replace("ClassicalElectromagnetism-", "EM-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--all-outcomes", action="store_true", help="also test problems that were declined")
    args = ap.parse_args()

    seen = {}
    for path in args.results:
        with open(path, encoding="utf-8") as f:
            for r in json.load(f)["rows"]:
                if args.all_outcomes or r["outcome"] in ANSWERED:
                    seen.setdefault(r["problem_id"], []).append((os.path.basename(path), r))

    flagged = {"match": 0, "mismatch": 0}
    total = {"match": 0, "mismatch": 0}
    print(f"{'problem':8} {'outcome':20} {'run':28} unused numbers in the text")
    for pid in sorted(seen):
        nums = numbers_in(text_of(pid))
        for name, r in seen[pid]:
            un = sorted({n for n in nums if not used(n, parsed_values(r))})
            o = r["outcome"]
            if o in total:
                total[o] += 1
                flagged[o] += 1 if un else 0
            print(f"{short(pid):8} {o:20} {name[:28]:28} {', '.join(f'{u:g}' for u in un) or '-'}")
    print()
    for o, label in (("mismatch", "wrong answers"), ("match", "right answers")):
        if total[o]:
            print(f"{label}: {flagged[o]} of {total[o]} would be declined by the guard")
    print("A good guard flags the wrong answers and leaves the right ones alone.")


if __name__ == "__main__":
    main()