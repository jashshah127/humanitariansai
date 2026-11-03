"""
Print examples from one group of a results file: the problem text (read from the local
CSV), what the parser returned, and for "no unknown" parses the start of the model's reply.
Problem text is dataset content: read it on screen, do not put it in documents or the repo.

Run from physics-engine/:
    python eval/show_group.py benchmark_full_01_all.json --outcome declined_missing_knowns --card WAVE-FROM-EQUATION --n 5
    python eval/show_group.py benchmark_full_01_all.json --outcome parse_found_no_unknown --empty-parse --n 5

Filters (all optional, combined with AND):
    --outcome       exact outcome name
    --stratum       numeric or symbolic
    --card          text that must appear in one of the cards the engine considered
    --empty-parse   only problems where the parser returned no quantities at all
"""
import argparse
import json
import os
import sys

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


def short(x, n):
    s = str(x).replace("\n", " ")
    return s if len(s) <= n else s[:n] + " ..."


def stratum(r):
    return "numeric" if r.get("kind") in ("scorable", "partially_numeric") else "symbolic"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--outcome")
    ap.add_argument("--stratum", choices=["numeric", "symbolic"])
    ap.add_argument("--card")
    ap.add_argument("--empty-parse", action="store_true")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--chars", type=int, default=450, help="characters of problem text to show")
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        rows = json.load(f)["rows"]

    def keep(r):
        p = r.get("parse") or {}
        if args.outcome and r["outcome"] != args.outcome:
            return False
        if args.stratum and stratum(r) != args.stratum:
            return False
        if args.card and not any(args.card in c for c in (r.get("cards_considered") or [])):
            return False
        if args.empty_parse and (p.get("knowns") or p.get("unknowns")):
            return False
        return True

    chosen = [r for r in rows if keep(r)]
    print(f"{len(chosen)} problem(s) match; showing {min(args.n, len(chosen))}\n")
    for r in chosen[: args.n]:
        p = r.get("parse") or {}
        print("=" * 72)
        print(r["problem_id"], f"[{stratum(r)}] {r['outcome']}")
        print("PROBLEM:", short(problem_text(r["problem_id"]), args.chars))
        print("PARSED knowns:", short(p.get("knowns"), 250))
        print("PARSED unknowns:", p.get("unknowns"), "| topic hint:", p.get("topic_hint"))
        if r.get("cards_considered"):
            print("CARDS CONSIDERED:", r["cards_considered"])
        if r.get("raw_reply"):
            print("MODEL REPLY:", short(r["raw_reply"], 400))


if __name__ == "__main__":
    main()
