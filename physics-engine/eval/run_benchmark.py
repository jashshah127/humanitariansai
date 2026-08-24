"""
AUTOMATED BENCHMARK RUNNER -- UGPhysics vs. the engine.

Two modes, because one of them needs no API key and answers a question worth
answering first:

  --dry-run   Reports how much of the benchmark is even SCORABLE against a
              numeric engine, with no model calls and no cost. Run this first.
              It answers "can this benchmark measure us at all?" before spending
              anything finding out how well we do.

  (default)   Full evaluation: parse -> solve -> compare. Needs ANTHROPIC_API_KEY.

Usage:
    python3 eval/run_benchmark.py --dry-run
    python3 eval/run_benchmark.py --limit 200
    python3 eval/run_benchmark.py --subject ClassicalElectromagnetism --limit 100

Data: run eval/pull_ugphysics_subset.py first (needs network). The CSVs are
gitignored -- UGPhysics is CC-BY-NC-SA-4.0 (NonCommercial), so the data stays
local and only the resulting NUMBERS travel.
"""
import argparse
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "engine"))
sys.path.insert(0, HERE)

import pandas as pd  # noqa: E402

from answer_match import (  # noqa: E402
    compare_symbolic,
    compare, strip_boxed, split_answers, to_number, summarize, Verdict,
)

SYMBOLIC_TYPES = {"EX", "EQ", "TF", "IN", "MC"}


def load(subject):
    path = os.path.join(HERE, f"ugphysics_{subject}.csv")
    if not os.path.exists(path):
        sys.exit(f"missing {path}\nRun eval/pull_ugphysics_subset.py first "
                 f"(needs network access).")
    return pd.read_csv(path)


def classify_scorability(row):
    """Can this row score a NUMERIC engine at all? No model calls needed."""
    types = {t.strip().split()[0] for t in str(row["answer_type"]).split(",") if t.strip()}
    if types & SYMBOLIC_TYPES:
        return "symbolic", sorted(types)
    nums = [to_number(t) for t in split_answers(strip_boxed(row["answers"]))]
    if not nums or all(n is None for n in nums):
        return "no_number_readable", None
    if any(n is None for n in nums):
        return "partially_numeric", None
    return "scorable", None


def dry_run(subjects):
    """What fraction of this benchmark can measure us, and what is the rest asking for?"""
    print("=" * 74)
    print("DRY RUN -- what fraction of the benchmark can score a numeric engine?")
    print("(no model calls, no cost)")
    print("=" * 74)
    grand = Counter()
    per_topic = {}
    for subject in subjects:
        df = load(subject)
        c = Counter()
        for _, row in df.iterrows():
            kind, _ = classify_scorability(row)
            c[kind] += 1
            grand[kind] += 1
            t = row["topic"]
            per_topic.setdefault(t, Counter())[kind] += 1
        total = sum(c.values())
        print(f"\n{subject} ({total} problems)")
        for k, v in c.most_common():
            print(f"   {v:5} ({v/total:5.1%})  {k}")

    tot = sum(grand.values())
    print("\n" + "-" * 74)
    print(f"ACROSS BOTH SUBJECTS ({tot} problems)")
    for k, v in grand.most_common():
        print(f"   {v:5} ({v/tot:5.1%})  {k}")
    scorable = grand["scorable"]
    print(f"\nScorable against the engine as it stands: {scorable}/{tot} ({scorable/tot:.1%})")
    print("\nBy topic (scorable / total):")
    for t, c in sorted(per_topic.items(), key=lambda kv: -sum(kv[1].values())):
        n = sum(c.values())
        print(f"   {c['scorable']:4} / {n:4}  ({c['scorable']/n:5.1%})  {t}")

    print("\n" + "=" * 74)
    print("WHAT THE UNSCORABLE MAJORITY IS ASKING FOR, AND WHERE WE STAND")
    print("=" * 74)
    print("Most of this benchmark wants a DERIVATION -- a symbolic expression like")
    print("  v = (k/(c-b))e^(-bt) - g/c")
    print("not a number. That is what undergraduate physics largely tests.")
    print()
    print("ENGINE SIDE: done. Cards now stay symbolic until a final substitution, so all")
    print("16 return a general formula alongside the number (T = 2*g*m1*m2/(m1+m2), and")
    print("so on). The engine produces exactly the shape of answer these problems want.")
    print()
    print("HARNESS SIDE: one install away. Comparing our formula against the benchmark's")
    print("boxed LaTeX needs sympy's parse_latex, which requires:")
    print("    pip install antlr4-python3-runtime==4.11")
    print("The comparison code is written (eval/answer_match.py: compare_symbolic) and")
    print("wired into the full run. It was not executable in the environment it was")
    print("written in, so treat the symbolic path as untested-but-ready rather than")
    print("verified -- run it and see.")
    print()
    print("So the 'scorable' figure above is the floor, not the ceiling: it counts only")
    print("the numeric path. With antlr4 installed the symbolic majority is attempted too.")


def full_run(subjects, limit, llm):
    from parse import parse_problem, ParseError
    from pipeline import solve_physics_problem

    results, rows = [], []
    for subject in subjects:
        df = load(subject)
        if limit:
            df = df.head(limit)
        for i, row in df.iterrows():
            kind, _ = classify_scorability(row)
            pid = f"{subject}-{row['index']}"
            if kind == "no_number_readable":
                results.append((Verdict.NOT_COMPARABLE, "ground truth has no readable answer"))
                continue
            try:
                parsed = parse_problem(str(row["problem"]), llm)
            except ParseError as e:
                results.append((Verdict.MISMATCH, f"parse failed: {e}"))
                rows.append(dict(problem_id=pid, verdict="parse_failed", detail=str(e)))
                continue
            sol = solve_physics_problem(pid, str(row["problem"]), parsed["knowns"],
                                        parsed["unknowns"], topic_hint=parsed.get("topic_hint"))
            if sol["route"] != "deterministic_script":
                results.append((Verdict.NOT_COMPARABLE, f"route={sol['route']}"))
                rows.append(dict(problem_id=pid, verdict="unverified_route",
                                 detail=sol["route"]))
                continue

            if kind == "symbolic":
                # The engine now returns general formulas, so symbolic ground truth is
                # comparable -- needs antlr4-python3-runtime installed for the LaTeX read.
                verdict, detail = compare_symbolic(
                    sol["solve"].get("symbolic_answer"), row["answers"])
            else:
                verdict, detail = compare(list(sol["final_answer"].values()),
                                          row["answers"], row["answer_type"])
            results.append((verdict, detail))
            rows.append(dict(problem_id=pid, verdict=verdict, detail=detail, kind=kind,
                             engine=sol["final_answer"],
                             engine_symbolic=sol["solve"].get("symbolic_answer"),
                             truth=str(row["answers"])))
            print(f"  [{verdict:14}] {pid}: {detail[:70]}", file=sys.stderr)

    s = summarize(results)
    print("\n" + "=" * 74)
    print("BENCHMARK RESULT")
    print("=" * 74)
    print(f"  problems seen          : {s['total']}")
    print(f"  comparable             : {s['comparable']} ({s['comparable_fraction']:.1%})")
    print(f"  matched ground truth   : {s['match']}")
    print(f"  mismatched             : {s['mismatch']}")
    print(f"  not comparable         : {s['not_comparable']}")
    if s["accuracy_on_comparable"] is not None:
        print(f"\n  accuracy ON COMPARABLE PROBLEMS ONLY: {s['accuracy_on_comparable']:.1%}")
        print(f"  (over {s['comparable']} problems, NOT over {s['total']} -- quoting this")
        print(f"   as benchmark accuracy without the denominator would be a false claim)")
    with open("benchmark_results.json", "w") as f:
        json.dump({"summary": s, "rows": rows}, f, indent=2, default=str)
    print("\n  per-problem detail -> benchmark_results.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report scorability only; no model calls, no cost")
    ap.add_argument("--subject", default=None,
                    choices=["ClassicalMechanics", "ClassicalElectromagnetism"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--provider", default="gemini",
                    choices=["gemini", "ollama", "claude"],
                    help="gemini = FREE tier, no credit card (default). "
                         "ollama = free and fully local. claude = paid.")
    args = ap.parse_args()

    subjects = [args.subject] if args.subject else \
        ["ClassicalMechanics", "ClassicalElectromagnetism"]

    if args.dry_run:
        dry_run(subjects)
    else:
        if args.provider == "gemini":
            if not os.environ.get("GEMINI_API_KEY"):
                sys.exit("GEMINI_API_KEY not set.\n"
                         "  Free key, no credit card: https://aistudio.google.com -> Get API key\n"
                         "  Then: export GEMINI_API_KEY=...\n"
                         "  Or use --provider ollama to run fully local, or --dry-run for "
                         "the no-cost scorability analysis.")
            from parse import GeminiLLM
            llm = GeminiLLM()
        elif args.provider == "ollama":
            from parse import OllamaLLM
            llm = OllamaLLM()
        else:
            if not os.environ.get("ANTHROPIC_API_KEY"):
                sys.exit("ANTHROPIC_API_KEY not set. Use --provider gemini for the free tier.")
            from parse import ClaudeLLM
            llm = ClaudeLLM()
        full_run(subjects, args.limit, llm)
