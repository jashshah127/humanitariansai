"""
How many of the benchmark's symbolic ground-truth answers can the LaTeX parser read at all?
No model calls. Uses the same steps the scorer uses (strip \boxed, split on top-level commas,
keep the right-hand side of one equals sign, parse). Prints a rate, which LaTeX constructs
appear in the answers that fail, and a few failing answers (answers are dataset content: read
them on screen, do not put them in documents or the repo).

Run from physics-engine/:
    python eval/truth_parse_rate.py
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import answer_match as am  # noqa: E402
import run_benchmark as rb  # noqa: E402

SUBJECTS = ["ClassicalMechanics", "ClassicalElectromagnetism"]
FORMULA_TYPES = {"EX", "EQ"}
NOT_FORMULA = {"TF", "MC", "IN"}
FEATURES = {
    r"\mathrm": r"\\mathrm", r"\text": r"\\text", r"\ln / \log": r"\\(ln|log)\b", r"\vec / \hat / \boldsymbol": r"\\(vec|hat|boldsymbol|mathbf)",
    r"\int": r"\\int", r"\sum": r"\\sum", r"\partial": r"\\partial", r"\left ... \right": r"\\left", r"\dfrac": r"\\dfrac",
    r"\pm": r"\\pm", r"\prime / '": r"\\prime|'", r"\begin (matrix, cases)": r"\\begin", r"\cdot": r"\\cdot", r"\times": r"\\times",
    r"\operatorname": r"\\operatorname", r"\sin / \cos / \tan": r"\\(sin|cos|tan)\b", r"\exp / e^": r"\\exp|e\^", r"\sqrt": r"\\sqrt",
    r"\hbar / \epsilon / \mu": r"\\(hbar|epsilon|varepsilon|mu)\b", "unit text (m, s, kg)": r"\\,|\\;|\\ ",
}


def main():
    total = full = part = none = 0
    feat_all, feat_fail = Counter(), Counter()
    failing = []
    for subject in SUBJECTS:
        df = rb.load(subject)
        for _, row in df.iterrows():
            types = {t.strip().split()[0] for t in str(row["answer_type"]).split(",") if t.strip()}
            if not (types & FORMULA_TYPES) or (types & NOT_FORMULA):
                continue
            toks = am.split_answers(am.strip_boxed(row["answers"]))
            if not toks:
                continue
            oks = []
            for t in toks:
                try:
                    oks.append(am._try_parse_latex(am.strip_equation(t)) is not None)
                except Exception:
                    oks.append(False)
            total += 1
            kind = "full" if all(oks) else ("part" if any(oks) else "none")
            full += kind == "full"
            part += kind == "part"
            none += kind == "none"
            body = " ".join(toks)
            for name, pat in FEATURES.items():
                if re.search(pat, body):
                    feat_all[name] += 1
                    if kind != "full":
                        feat_fail[name] += 1
            if kind != "full":
                failing.append((f"{subject}-{row['index']}", body))
    if not total:
        print("No symbolic (EX/EQ) answers found. Check the CSV files.")
        return
    print(f"Symbolic ground-truth answers (types EX or EQ): {total} problems")
    print(f"  every answer parses: {full} ({full / total:.0%})")
    print(f"  some parse:          {part} ({part / total:.0%})")
    print(f"  none parse:          {none} ({none / total:.0%})")
    print("\nConstructs in the answers (problems that did not fully parse / problems containing it):")
    for name, n in feat_all.most_common():
        print(f"  {name:28} {feat_fail[name]:4} / {n}")
    print("\nExamples that did not fully parse (on screen only):")
    for pid, body in failing[:8]:
        print(f"  {pid}: {body[:100]}")


if __name__ == "__main__":
    main()
