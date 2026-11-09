"""
Build the test set for a parser-prompt experiment. IDs only are written.

The set holds the problems a change is meant to affect (including the words that the
named-object value table on feature-atharva reacts to), the problems the engine
already answered (to catch regressions), and random controls from the groups a parser
change should NOT move. Numeric stratum only.

Run from physics-engine/:
    python eval/make_ab_set.py benchmark_full_01_all.json
    python eval/make_ab_set.py benchmark_full_01_all.json --controls 20 --seed 2026

Writes eval/sample/ids_ab.txt and prints how many problems came from each group.
"""
import argparse
import json
import os
import random
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_benchmark as rb  # noqa: E402
import taxonomy  # noqa: E402

_cache = {}


def text_of(pid):
    subject, idx = pid.rsplit("-", 1)
    if subject not in _cache:
        _cache[subject] = rb.load(subject).set_index("index")
    try:
        return str(_cache[subject].loc[int(idx), "problem"]).lower()
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--controls", type=int, default=20)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--out", default=os.path.join(HERE, "sample", "ids_ab.txt"))
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        rows = [r for r in json.load(f)["rows"] if taxonomy.stratum(r) == "numeric"]
    by_id = {r["problem_id"]: r for r in rows}
    declined = [r for r in rows if r["outcome"] in ("declined_missing_knowns", "declined_no_card", "parse_found_no_unknown")]

    groups = OrderedDict()
    groups["answered (regression check)"] = [r["problem_id"] for r in rows if r["outcome"] in ("match", "mismatch")]
    groups["wave equation (wave + sin in text)"] = [r["problem_id"] for r in declined if "wave" in text_of(r["problem_id"]) and "sin" in text_of(r["problem_id"])]
    groups["implied zero (at rest / stationary)"] = [r["problem_id"] for r in declined if "at rest" in text_of(r["problem_id"]) or "stationary" in text_of(r["problem_id"])]
    named = re.compile(r"\b(perpendicular|at right angles|from rest|initially at rest|earth|proton|electron)s?\b")
    groups["named objects (Atharva's new value table)"] = [r["problem_id"] for r in declined if named.search(text_of(r["problem_id"]))]
    groups["one quantity short"] = [r["problem_id"] for r in rows if r["outcome"] == "declined_missing_knowns" and taxonomy.classify_missing(r)[0] == "one_short"]

    chosen = []
    for ids in groups.values():
        for pid in ids:
            if pid not in chosen:
                chosen.append(pid)

    pool = sorted(r["problem_id"] for r in declined if r["problem_id"] not in chosen)
    controls = random.Random(args.seed).sample(pool, min(args.controls, len(pool)))
    groups["random controls (should not move)"] = controls
    chosen += controls

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(chosen) + "\n")

    print(f"{'group':40} {'problems':>8}")
    for name, ids in groups.items():
        print(f"{name:40} {len(ids):8}")
    print(f"{'total (unique)':40} {len(chosen):8}")
    print(f"\nWrote {args.out}. An overlap between groups is counted once in the total.")
    print(f"Estimated time at 6.5 s per call: about {len(chosen) * 6.5 / 60:.0f} minutes per run")


if __name__ == "__main__":
    main()
