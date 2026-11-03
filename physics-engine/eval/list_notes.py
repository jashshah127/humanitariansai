"""
List the model's own notes for problems where the parser found nothing to solve for.
When the parser cannot fit a problem into the glossary it often says so in its notes,
which gives a free list of the physics the engine does not cover.

Run from physics-engine/:
    python eval/list_notes.py benchmark_full_01_all.json
    python eval/list_notes.py benchmark_full_01_all.json --stratum numeric --outcome parse_found_no_unknown

Output is problem IDs and the model's note (a short sentence), not problem text.
"""
import argparse
import json
import re
from collections import Counter

NOTE = re.compile(r'"notes"\s*:\s*"((?:[^"\\]|\\.)*)"')


def stratum(r):
    return "numeric" if r.get("kind") in ("scorable", "partially_numeric") else "symbolic"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--outcome", default="parse_found_no_unknown")
    ap.add_argument("--stratum", choices=["numeric", "symbolic"], default=None)
    ap.add_argument("--width", type=int, default=150)
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    rows = [r for r in rows if r["outcome"] == args.outcome
            and (args.stratum is None or stratum(r) == args.stratum)]

    words = Counter()
    for r in rows:
        m = NOTE.search(r.get("raw_reply") or "")
        note = m.group(1) if m else "(no note)"
        empty = "empty" if not ((r.get("parse") or {}).get("knowns") or (r.get("parse") or {}).get("unknowns")) else "some"
        print(f"{r['problem_id']:32} [{empty}] {note[:args.width]}")
        for w in re.findall(r"[a-z]{5,}", note.lower()):
            words[w] += 1
    print(f"\n{len(rows)} problem(s). Most common words in the notes:")
    skip = {"problem", "variable", "standard", "which", "quantities", "present", "provided", "asks", "list", "does", "model", "variables", "involves", "needs"}
    print("  " + ", ".join(f"{w} ({n})" for w, n in words.most_common(30) if w not in skip))


if __name__ == "__main__":
    main()
