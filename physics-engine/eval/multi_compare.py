"""
Compare runs when a single run is too noisy to trust. The same code and prompt give
different parses on different runs, so a problem answered wrongly in one run may decline
or even come out right in the next.

stability  shows, for every problem answered in at least one run, what happened in each run.
variant    judges a changed run against several control runs of the unchanged setup.

Run from physics-engine/:
    python eval/multi_compare.py stability benchmark_full_01_all.json benchmark_ab_v0.json benchmark_ab_v0b.json
    python eval/multi_compare.py variant benchmark_ab_v1.json --controls benchmark_ab_v0.json benchmark_ab_v0b.json

Rule used by "variant" (stricter than zero new wrong answers would be, but fair to noise):
  a NEW WRONG answer is one that was wrong in the variant and in none of the controls;
  a LOST RIGHT answer is one that was right in every control and not right in the variant.
  PASS only if there are none of either.
Output has IDs and counts only, no problem text.
"""
import argparse
import json
from collections import Counter

ANSWERED = ("match", "mismatch", "answered_not_compared")
CODE = {"match": "R", "mismatch": "W", "answered_not_compared": "?"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return {r["problem_id"]: r["outcome"] for r in json.load(f)["rows"]}


def short(pid):
    return pid.replace("ClassicalMechanics-", "M-").replace("ClassicalElectromagnetism-", "EM-")


def code(outcome):
    return CODE.get(outcome, "-")


def stability(paths):
    runs = [load(p) for p in paths]
    shared = sorted(set.intersection(*[set(r) for r in runs]))
    print(f"{len(runs)} runs, {len(shared)} problems in all of them")
    print("legend: R = answered right, W = answered wrong, ? = answered, not comparable, - = not answered\n")
    print(f"{'problem':10} " + " ".join(f"run{i + 1}" for i in range(len(runs))))
    rows = [(p, [code(r[p]) for r in runs]) for p in shared if any(r[p] in ANSWERED for r in runs)]
    for p, cs in rows:
        print(f"{short(p):10} " + " ".join(f"{c:>4}" for c in cs))
    stable = [p for p, cs in rows if len(set(cs)) == 1]
    print(f"\nanswered in at least one run: {len(rows)}")
    print(f"  same result in every run: {len(stable)}  {', '.join(short(p) for p in stable)}")
    print(f"  changed between runs: {len(rows) - len(stable)}")
    same_all = sum(1 for p in shared if len({r[p] for r in runs}) == 1)
    print(f"all {len(shared)} problems with an identical outcome in every run: {same_all} ({same_all / len(shared):.0%})")
    per_run = [Counter(code(r[p]) for p in shared) for r in runs]
    print("per run: " + "; ".join(f"run{i + 1} R={c['R']} W={c['W']}" for i, c in enumerate(per_run)))


def variant(path, controls):
    v = load(path)
    cs = [load(c) for c in controls]
    shared = sorted(set(v).intersection(*[set(c) for c in cs]))
    wrong_any = {p for p in shared if any(c[p] == "mismatch" for c in cs)}
    right_all = {p for p in shared if all(c[p] == "match" for c in cs)}
    answered_any = {p for p in shared if any(c[p] in ANSWERED for c in cs)}

    new_wrong = [p for p in shared if v[p] == "mismatch" and p not in wrong_any]
    lost_right = [p for p in shared if p in right_all and v[p] != "match"]
    new_right = [p for p in shared if v[p] == "match" and not any(c[p] == "match" for c in cs)]
    newly_answered = [p for p in shared if v[p] in ANSWERED and p not in answered_any]
    wrong_now = [p for p in shared if v[p] == "mismatch"]
    fmt = lambda ids: ", ".join(short(p) for p in ids) or "none"

    print(f"variant: {path}\ncontrols: {', '.join(controls)}\nshared problems: {len(shared)}\n")
    print(f"answered wrong in the variant: {len(wrong_now)}  {fmt(wrong_now)}")
    print(f"  of which wrong in some control too: {len(wrong_now) - len(new_wrong)}")
    print(f"problems answered by the variant and by no control: {len(newly_answered)}  {fmt(newly_answered)}")
    print(f"new right answers (right in the variant, in no control): {len(new_right)}  {fmt(new_right)}\n")
    print(f"NEW WRONG answers (wrong here, never wrong in a control): {len(new_wrong)}  {fmt(new_wrong)}")
    print(f"LOST RIGHT answers (right in every control, not here): {len(lost_right)}  {fmt(lost_right)}")
    print("\nRULE: " + ("PASS" if not new_wrong and not lost_right else "FAIL"))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stability")
    s.add_argument("runs", nargs="+")
    v = sub.add_parser("variant")
    v.add_argument("variant")
    v.add_argument("--controls", nargs="+", required=True)
    a = ap.parse_args()
    if a.cmd == "stability":
        stability(a.runs)
    else:
        variant(a.variant, a.controls)


if __name__ == "__main__":
    main()
