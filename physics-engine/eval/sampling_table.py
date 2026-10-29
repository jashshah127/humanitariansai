"""
Counts the UGPhysics problems by topic and by what the engine can do with them.
No model calls, no cost. Used to design the stratified sampling plan.

Run from physics-engine/:
    python eval/sampling_table.py

It reads the two local CSVs that pull_ugphysics_subset.py downloaded, and uses the
same rules as run_benchmark.py to decide how each problem would be handled:
  scorable           numeric answer the engine can be scored on today
  symbolic           expression, equation, interval (needs the antlr4 path, Wk 5)
  partially_numeric  some answers numeric, some not
  no_number_readable skipped by the benchmark runner (nothing to compare)
Problems whose only answer types are true/false or multiple choice are counted
separately: the runner skips them before any model call.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pandas as pd  # noqa: E402

import run_benchmark as rb  # noqa: E402

SECONDS_PER_CALL = 6.5  # the free-tier pacing used by the Gemini parser
OUT_OF_SCOPE = getattr(rb, "OUT_OF_SCOPE_TYPES", {"TF", "MC"})


def main():
    rows = []
    for subject in ["ClassicalMechanics", "ClassicalElectromagnetism"]:
        df = rb.load(subject)
        for _, r in df.iterrows():
            kind, _ = rb.classify_scorability(r)
            types = {t.strip().split()[0] for t in str(r["answer_type"]).split(",") if t.strip()}
            out_of_scope = kind != "no_number_readable" and bool(types) and types <= OUT_OF_SCOPE
            rows.append((subject, r["topic"], "skipped_tf_mc" if out_of_scope else kind))

    d = pd.DataFrame(rows, columns=["subject", "topic", "class"])
    print(f"Total problems: {len(d)}\n")
    print(pd.crosstab(d["topic"], d["class"], margins=True).to_string())

    attemptable = d[~d["class"].isin(["no_number_readable", "skipped_tf_mc"])]
    print(f"\nProblems the runner would send to the parser: {len(attemptable)}")
    print(f"  of which numeric-scorable today: {(attemptable['class'] == 'scorable').sum()}")
    minutes = len(attemptable) * SECONDS_PER_CALL / 60
    print(f"Time at {SECONDS_PER_CALL} s per call (parse only): about {minutes:.0f} minutes "
          f"({minutes / 60:.1f} hours)")
    print("\nAttemptable problems by topic:")
    print(attemptable.groupby("topic").size().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
