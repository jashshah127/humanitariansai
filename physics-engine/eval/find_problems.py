"""
Find problems in a results file by words in the problem text, and show their outcomes.
Useful for sizing a target: how many problems mention a wave equation, a Doppler source,
"at rest", and what the engine did with them. Problem text is dataset content: only IDs,
outcomes and counts are printed.

Run from physics-engine/:
    python eval/find_problems.py benchmark_full_01_all.json --contains wave --contains sin
    python eval/find_problems.py benchmark_full_01_all.json --contains "at rest" --stratum numeric
    python eval/find_problems.py benchmark_full_01_all.json --contains doppler --contains "sound"

--contains may be repeated; a problem must contain every word (case-insensitive).
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
        return ""


def stratum(r):
    return "numeric" if r.get("kind") in ("scorable", "partially_numeric") else "symbolic"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--contains", action="append", required=True)
    ap.add_argument("--stratum", choices=["numeric", "symbolic"], default=None)
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    if args.stratum:
        rows = [r for r in rows if stratum(r) == args.stratum]
    words = [w.lower() for w in args.contains]
    hits = []
    for r in rows:
        text = problem_text(r["problem_id"]).lower()
        if all(w in text for w in words):
            hits.append(r)

    print(f"{len(hits)} of {len(rows)} problems contain {args.contains}")
    for outcome, n in Counter(r["outcome"] for r in hits).most_common():
        print(f"  {n:4}  {outcome}")
    print("IDs by outcome:")
    by = {}
    for r in hits:
        by.setdefault(r["outcome"], []).append(r["problem_id"].replace("Classical", "").replace("Mechanics-", "M-").replace("Electromagnetism-", "EM-"))
    for outcome, ids in by.items():
        print(f"  {outcome}: {', '.join(ids[:25])}{' ...' if len(ids) > 25 else ''}")


if __name__ == "__main__":
    main()
