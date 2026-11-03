"""
Rule-based triage of why problems were declined, from saved results files. No model
calls and no problem text in the output. This is a first sort to find the biggest
groups; each group still needs a few examples read by hand before it is called a cause.

Run from physics-engine/:
    python eval/taxonomy.py benchmark_full_01_all.json
    python eval/taxonomy.py benchmark_full_01_all.json --stratum numeric --examples 4

Groups for "declined, missing knowns" (the best-fitting card is the one with the fewest
missing quantities; injected constants such as G or g are not counted as parsed):
  one_short        exactly one required quantity is missing. Usually a naming mismatch
                   (the card wants R, the parser wrote Re) or an implied value (observer
                   at rest = 0).
  several_short    two or more are missing, but the parser did give at least one quantity
                   the card uses.
  nothing_relevant the parser gave nothing any considered card uses. The card was likely
                   considered only because the unknown shares a name with another card's.
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_benchmark as rb  # noqa: E402,F401  (adds ../engine to sys.path)
from formula_kb import ALL_CARDS  # noqa: E402

CARDS = {c.id: c for c in ALL_CARDS}


def stratum(r):
    return "numeric" if r.get("kind") in ("scorable", "partially_numeric") else "symbolic"


def classify_missing(r):
    p = r.get("parse") or {}
    parsed = set((p.get("knowns") or {}).keys())
    consts = set((p.get("injected_constants") or {}).keys())
    own = parsed - consts
    best = None
    for cid in r.get("cards_considered") or []:
        card = CARDS.get(cid)
        if card is None:
            continue
        req = list(card.required_knowns)
        missing = [k for k in req if k not in parsed]
        overlap = own & set(req)
        key = (len(missing), -len(overlap))
        if best is None or key < best[0]:
            best = (key, cid, missing, overlap)
    if best is None:
        return "no_card_found", None, []
    (n_missing, _), cid, missing, overlap = best
    if n_missing == 1:
        return "one_short", cid, missing
    if overlap:
        return "several_short", cid, missing
    return "nothing_relevant", cid, missing


def show(title, counter, top=8):
    print(f"  {title}")
    for k, v in counter.most_common(top):
        print(f"    {v:4}  {k}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--stratum", choices=["numeric", "symbolic"], default=None)
    ap.add_argument("--examples", type=int, default=3)
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    if args.stratum:
        rows = [r for r in rows if stratum(r) == args.stratum]
    print(f"{len(rows)} problems" + (f" ({args.stratum})" if args.stratum else ""))

    c = Counter(r["outcome"] for r in rows)
    print("\nOutcomes")
    for k, v in c.most_common():
        print(f"  {v:4} {v / len(rows):6.1%}  {k}")

    # --- declined, missing knowns
    mk = [r for r in rows if r["outcome"] == "declined_missing_knowns"]
    print(f"\nDeclined, missing knowns: {len(mk)}")
    groups = defaultdict(list)
    for r in mk:
        g, cid, missing = classify_missing(r)
        groups[g].append((r["problem_id"], cid, missing))
    for g in ("one_short", "several_short", "nothing_relevant", "no_card_found"):
        items = groups.get(g, [])
        if not items:
            continue
        print(f"\n  {g}: {len(items)} ({len(items) / len(mk):.0%} of these)")
        if g == "one_short":
            show("quantity that was missing", Counter(m[0] for _, _, m in items), args.top)
            show("card that was one short", Counter(cid for _, cid, _ in items), args.top)
        elif g == "several_short":
            show("card that was closest", Counter(cid for _, cid, _ in items), args.top)
        elif g == "nothing_relevant":
            show("card considered", Counter(cid for _, cid, _ in items), args.top)
        print("    examples:", ", ".join(pid for pid, _, _ in items[: args.examples]))

    # --- declined, no card
    nc = [r for r in rows if r["outcome"] == "declined_no_card"]
    print(f"\nDeclined, no card: {len(nc)}")
    if nc:
        unk = Counter()
        for r in nc:
            for u in (r.get("parse") or {}).get("unknowns") or []:
                unk[u] += 1
        show("unknown the parser asked for", unk, args.top)
        print("    examples:", ", ".join(r["problem_id"] for r in nc[: args.examples]))

    # --- parsed, no unknown
    nu = [r for r in rows if r["outcome"] == "parse_found_no_unknown"]
    print(f"\nParsed, no unknown found: {len(nu)}")
    if nu:
        empty = sum(1 for r in nu if not (r.get("parse") or {}).get("knowns"))
        print(f"    parser also gave no quantities: {empty}; gave some quantities: {len(nu) - empty}")
        show("topic hint", Counter((r.get("parse") or {}).get("topic_hint") for r in nu), args.top)
        print("    examples:", ", ".join(r["problem_id"] for r in nu[: args.examples]))

    # --- wrong answers and parse problems
    wrong = [r["problem_id"] for r in rows if r["outcome"] == "mismatch"]
    bad = [r["problem_id"] for r in rows if r["outcome"] in ("parse_failed_bad_output", "parse_failed_api")]
    rep = sum(1 for r in rows if (r.get("parse") or {}).get("json_repaired"))
    unrec = sum(1 for r in rows if (r.get("parse") or {}).get("unrecognized_names"))
    print(f"\nAnswered and wrong: {len(wrong)} {wrong}")
    print(f"Parse failures: {len(bad)} {bad}")
    print(f"Parses that needed a JSON/LaTeX repair: {rep}")
    print(f"Parses with names outside the glossary: {unrec}")


if __name__ == "__main__":
    main()
