"""
Compare two results files on the problems they share. Built for prompt experiments:
what did the change answer that it did not before, how many of those are right and how
many are WRONG, and did anything that used to be right get lost.

Run from physics-engine/:
    python eval/compare_runs.py benchmark_full_01_all.json benchmark_ab_v1.json
    python eval/compare_runs.py A.json B.json --show 20

Rule printed at the end: PASS only if B has no new wrong answers and loses no right answer.
Output has IDs and counts only, no problem text.
"""
import argparse
import json
from collections import Counter

ANSWERED = ("match", "mismatch", "answered_not_compared")


def load(path):
    with open(path, encoding="utf-8") as f:
        return {r["problem_id"]: r for r in json.load(f)["rows"]}


def short(pid):
    return pid.replace("ClassicalMechanics-", "M-").replace("ClassicalElectromagnetism-", "EM-")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--show", type=int, default=15)
    args = ap.parse_args()

    A, B = load(args.a), load(args.b)
    shared = sorted(set(A) & set(B))
    print(f"A = {args.a} ({len(A)} problems)\nB = {args.b} ({len(B)} problems)\nshared: {len(shared)}\n")

    outcomes = sorted({A[p]["outcome"] for p in shared} | {B[p]["outcome"] for p in shared})
    ca = Counter(A[p]["outcome"] for p in shared)
    cb = Counter(B[p]["outcome"] for p in shared)
    print(f"{'outcome':28} {'A':>5} {'B':>5}")
    for o in outcomes:
        print(f"{o:28} {ca[o]:5} {cb[o]:5}")

    moves = Counter((A[p]["outcome"], B[p]["outcome"]) for p in shared if A[p]["outcome"] != B[p]["outcome"])
    same = sum(1 for p in shared if A[p]["outcome"] == B[p]["outcome"])
    print(f"\nsame outcome: {same} of {len(shared)} ({same / len(shared):.0%})" if shared else "\nno shared problems")
    if moves:
        print("changes (A -> B):")
        for (x, y), n in moves.most_common():
            print(f"  {n:3}  {x} -> {y}")

    newly = [p for p in shared if A[p]["outcome"] not in ANSWERED and B[p]["outcome"] in ANSWERED]
    lost = [p for p in shared if A[p]["outcome"] in ANSWERED and B[p]["outcome"] not in ANSWERED]
    new_wrong = [p for p in shared if B[p]["outcome"] == "mismatch" and A[p]["outcome"] != "mismatch"]
    lost_right = [p for p in shared if A[p]["outcome"] == "match" and B[p]["outcome"] != "match"]
    fixed = [p for p in shared if A[p]["outcome"] == "mismatch" and B[p]["outcome"] != "mismatch"]
    new_right = [p for p in shared if B[p]["outcome"] == "match" and A[p]["outcome"] != "match"]

    def lst(ids):
        return ", ".join(short(p) for p in ids[: args.show]) + (" ..." if len(ids) > args.show else "")

    print(f"\nnewly answered: {len(newly)}  (right {sum(1 for p in newly if B[p]['outcome'] == 'match')}, "
          f"wrong {sum(1 for p in newly if B[p]['outcome'] == 'mismatch')})  {lst(newly)}")
    print(f"no longer answered: {len(lost)}  {lst(lost)}")
    print(f"new right answers: {len(new_right)}  {lst(new_right)}")
    print(f"NEW WRONG answers: {len(new_wrong)}  {lst(new_wrong)}")
    print(f"wrong answers fixed: {len(fixed)}  {lst(fixed)}")
    print(f"right answers lost: {len(lost_right)}  {lst(lost_right)}")

    ok = not new_wrong and not lost_right
    print("\nRULE (no new wrong answers, no right answer lost): " + ("PASS" if ok else "FAIL"))


if __name__ == "__main__":
    main()
