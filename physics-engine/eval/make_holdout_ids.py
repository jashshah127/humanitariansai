"""
Make the list of numeric problems that were NOT in the prompt-experiment set, so a change
(and the offline guards) can be tested on problems nobody tuned them on. IDs only.

Run from physics-engine/:
    python eval/make_holdout_ids.py benchmark_full_01_all.json
Writes eval/sample/ids_holdout.txt and prints how many problems it holds.
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--ab", default=os.path.join(HERE, "sample", "ids_ab.txt"))
    ap.add_argument("--out", default=os.path.join(HERE, "sample", "ids_holdout.txt"))
    args = ap.parse_args()

    with open(args.results, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    with open(args.ab, encoding="utf-8") as f:
        used = {line.strip() for line in f if line.strip()}
    numeric = [r["problem_id"] for r in rows if r.get("kind") in ("scorable", "partially_numeric")]
    hold = sorted(p for p in numeric if p not in used)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(hold) + "\n")
    print(f"numeric problems in the results file: {len(numeric)}")
    print(f"already in the experiment set (ids_ab): {len(numeric) - len(hold)}")
    print(f"holdout problems written to {args.out}: {len(hold)}")
    print(f"estimated time at 6.5 s per call: about {len(hold) * 6.5 / 60:.0f} minutes per run")


if __name__ == "__main__":
    main()
