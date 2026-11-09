"""
Show which problems got values filled in by the engine (the "injected" quantities) in one
run that the other run did not get, and what happened to those problems. Built to check
whether a value table (for example proton -> charge and mass, "perpendicular" -> 90 degrees)
fired, where, and whether it helped or produced a wrong answer.

Run from physics-engine/:
    python eval/compare_injected.py benchmark_ab_v0.json benchmark_ab_named1.json
    python eval/compare_injected.py benchmark_ab_v0b.json benchmark_ab_named1.json --show 40

Prints IDs, quantity names, values and outcomes only, no problem text.
"""
import argparse
import json


def load(path):
    with open(path, encoding="utf-8") as f:
        return {r["problem_id"]: r for r in json.load(f)["rows"]}


def short(pid):
    return pid.replace("ClassicalMechanics-", "M-").replace("ClassicalElectromagnetism-", "EM-")


def injected(row):
    return (row.get("parse") or {}).get("injected_constants") or {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", help="the run without the change")
    ap.add_argument("b", help="the run with the change")
    ap.add_argument("--show", type=int, default=30)
    args = ap.parse_args()

    A, B = load(args.a), load(args.b)
    shared = sorted(set(A) & set(B))
    fired = []
    for p in shared:
        extra = {k: v for k, v in injected(B[p]).items() if k not in injected(A[p])}
        if extra:
            fired.append((p, extra))

    print(f"A = {args.a}\nB = {args.b}\nshared problems: {len(shared)}")
    print(f"problems where B filled in a value that A did not: {len(fired)}\n")
    for p, extra in fired[: args.show]:
        vals = ", ".join(f"{k}={v}" for k, v in extra.items())
        print(f"{short(p):10} {vals[:60]:60} {A[p]['outcome']} -> {B[p]['outcome']}")
    changed = [p for p, _ in fired if A[p]["outcome"] != B[p]["outcome"]]
    answered = [p for p, _ in fired if B[p]["outcome"] in ("match", "mismatch", "answered_not_compared")]
    wrong = [p for p, _ in fired if B[p]["outcome"] == "mismatch"]
    print(f"\nof those: outcome changed {len(changed)}, answered in B {len(answered)}, answered WRONG in B {len(wrong)}")
    print("Note: outcomes also change from run to run with no change at all, so a changed outcome is not proof the filled value caused it.")


if __name__ == "__main__":
    main()
